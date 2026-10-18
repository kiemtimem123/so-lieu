#!/usr/bin/env python3
"""Discover and archive candidate public financial reports; never auto-publish extracted figures."""
from __future__ import annotations
import hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "config/report-queue.json"
SEC_PATH = ROOT / "config/securities.json"
SOURCES_PATH = ROOT / "config/source-registry.json"
OUT = ROOT / "reports/raw"
MAX_BYTES = int(os.getenv("MAX_REPORT_BYTES", str(12 * 1024 * 1024)))
MAX_PER_JOB = int(os.getenv("MAX_DOWNLOADS_PER_JOB", "2"))
MAX_JOBS_PER_RUN = int(os.getenv("MAX_JOBS_PER_RUN", "3"))
USER_AGENT = "solieutaichinh-report-collector/1.0 (public financial report archive)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.8"})
NOW = datetime.now(timezone.utc).isoformat()

def load(path, fallback):
    if not path.exists(): return fallback
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def domain_allowed(url, allowed):
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    return any(host == d or host.endswith("." + d) for d in allowed)

def search_web(query):
    url = "https://html.duckduckgo.com/html/"
    try:
        response = SESSION.post(url, data={"q": query}, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        found = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)
            parsed = urlparse(href)
            if "duckduckgo.com" in (parsed.hostname or ""):
                target = parse_qs(parsed.query).get("uddg", [""])[0]
                if target.startswith("http"):
                    href = target
            if href.startswith("http"):
                found.append({"url": href, "title": title})
        return found
    except Exception as exc:
        print(json.dumps({"event":"search_failed","query":query,"error":str(exc)[:500]}, ensure_ascii=False))
        return [{"error": str(exc), "query": query}]

def extract_file(path, content_type):
    suffix = path.suffix.lower()
    if suffix == ".pdf" or "pdf" in content_type.lower():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages[:100]):
                text = page.extract_text() or ""
                if text.strip(): pages.append({"page": i + 1, "text": text[:25000]})
            return {"kind":"pdf", "pages":pages, "page_count":len(reader.pages), "extraction":"text", "note":None if pages else "PDF không có lớp văn bản; có thể là bản scan cần OCR thủ công."}
        except Exception as exc:
            return {"kind":"pdf", "pages":[], "extraction":"failed", "note":str(exc)}
    if suffix == ".xlsx" or "spreadsheetml" in content_type.lower():
        try:
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True, data_only=True)
            sheets = []
            for ws in wb.worksheets[:30]:
                rows = []
                for row in ws.iter_rows(min_row=1, max_row=250, values_only=True):
                    vals = [str(v)[:500] if v is not None else None for v in row[:40]]
                    if any(v is not None for v in vals): rows.append(vals)
                sheets.append({"name":ws.title,"rows":rows})
            return {"kind":"xlsx","sheets":sheets,"extraction":"table"}
        except Exception as exc:
            return {"kind":"xlsx","sheets":[],"extraction":"failed","note":str(exc)}
    return {"kind":"unknown","extraction":"not_supported","note":"Tệp được lưu nhưng định dạng chưa hỗ trợ trích xuất tự động."}

def safe_name(url, content_type):
    path = unquote(urlparse(url).path)
    suffix = Path(path).suffix.lower()
    if suffix not in {".pdf",".xlsx",".xls"}:
        suffix = ".pdf" if "pdf" in content_type.lower() else ".xlsx" if "spreadsheetml" in content_type.lower() else ".bin"
    return suffix

def is_official_statement_title(title, symbol, require_symbol=True):
    """Reject analyst/research material; accept only issuer filing notices for actual statements."""
    t = (title or "").lower()
    sym = re.escape(symbol.lower())
    if require_symbol and not re.search(rf"\b{sym}\b", t):
        return False
    reject = [
        "phân tích", "bao cao phan tich", "báo cáo phân tích", "cập nhật kqkd",
        "khuyến nghị", "định giá", "price target", "analyst", "earning report",
        "investment thesis", "forecast", "dự phóng", "triển vọng", "update kqkd",
        "mua", "bán", "nắm giữ", "brokerage"
    ]
    if any(word in t for word in reject):
        return False
    return any(word in t for word in [
        "báo cáo tài chính", "bao cao tai chinh", "financial statements",
        "financial statement", "consolidated financial statements"
    ])

def is_vietstock_statement_pdf(url, symbol):
    """Recognize direct Vietstock BCTC PDFs by their URL path, even if search metadata is poor."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = unquote(parsed.path).lower()
    if host not in {"static1.vietstock.vn", "static2.vietstock.vn"}:
        return False
    if not path.endswith(".pdf") or "/bctc/" not in path or "/vn/" not in path:
        return False
    # Typical filename: MBB_Baocaotaichinh_6T_2026_Soatxet_Hopnhat.pdf
    filename = Path(path).name
    if not re.match(rf"^{re.escape(symbol.lower())}[_-]", filename):
        return False
    return any(token in filename for token in ("baocaotaichinh", "bao-cao-tai-chinh", "bctc", "financialstatement", "financial-statement"))

def expand_vietstock_filing_page(candidate, symbol):
    """Vietstock is used only as an index of issuer disclosure notices, not as an analyst source."""
    url = candidate.get("url", "")
    host = (urlparse(url).hostname or "").lower()
    if host not in {"vietstock.vn", "www.vietstock.vn", "en.vietstock.vn"}:
        return []
    page_title = candidate.get("title", "")
    if not is_official_statement_title(page_title, symbol):
        return []
    try:
        response = SESSION.get(url, timeout=25, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        heading = soup.find(["h1", "title"])
        verified_title = heading.get_text(" ", strip=True) if heading else page_title
        if not is_official_statement_title(verified_title, symbol):
            return []
        attachments = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            label = a.get_text(" ", strip=True)
            absolute = requests.compat.urljoin(response.url, href)
            path = urlparse(absolute).path.lower()
            if not path.endswith((".pdf", ".xlsx", ".xls")):
                continue
            if not domain_allowed(absolute, ["static1.vietstock.vn", "static2.vietstock.vn", "vietstock.vn"]):
                continue
            evidence = (label + " " + path).lower()
            if any(x in evidence for x in ["explanation", "giai-trinh", "giai_trinh", "forecast", "phan-tich", "analyst"]):
                continue
            if not any(x in evidence for x in ["baocao", "bao-cao", "financial", "bctc", "statement", "tai-chinh"]):
                continue
            attachments.append({
                "url": absolute, "title": label or verified_title,
                "host": (urlparse(absolute).hostname or "").lower(),
                "allowlisted": True, "official_filing_page": True,
                "filing_page": response.url, "filing_page_title": verified_title
            })
        return attachments
    except Exception:
        return []

def discover_for_job(job, allowed_domains):
    symbol = job["symbol"]
    start = int(job.get("startYear", 2024))
    report_type = job.get("reportType", "consolidated")
    report_words = "báo cáo tài chính quý" if report_type != "both" else "báo cáo tài chính quý hợp nhất riêng lẻ"
    source_registry = load(SOURCES_PATH, {"allowedDomains": [], "issuerDomainsBySymbol": {}})
    issuer_domains = source_registry.get("issuerDomainsBySymbol", {}).get(symbol, [])
    current_year = datetime.now().year
    queries = [
        f'"{symbol}" "báo cáo tài chính quý" {start}..{current_year}',
        f'"{symbol}" "báo cáo tài chính" "quý" site:vietstock.vn',
        # Vietstock stores direct PDF attachments under static1/static2 and different exchange folders.
        # Search each year instead of hard-coding only the current-year HOSE folder.
        *[
            f'"{symbol}" site:static2.vietstock.vn/data/ {year} BCTC PDF',
            f'"{symbol}" site:static1.vietstock.vn/data/ {year} BCTC PDF',
        ]
        for year in range(start, current_year + 1)
    ]
    # Search issuer/IR domains directly; a domain match alone is not enough:
    # the title still must pass the strict official-statement filter below.
    for issuer_domain in issuer_domains:
        if re.fullmatch(r"[a-zA-Z0-9.-]+", str(issuer_domain)):
            queries.append(f'"{symbol}" "báo cáo tài chính" quý site:{issuer_domain}')
    candidates, seen = [], set()
    for q in queries:
        results = search_web(q)
        for item in results:
            if "url" not in item: continue
            url = item["url"]
            if url in seen: continue
            seen.add(url)
            host = (urlparse(url).hostname or "").lower()
            item.update({"query":q,"host":host,"allowlisted":domain_allowed(url,allowed_domains),"symbol":symbol})
            if host in {"vietstock.vn", "www.vietstock.vn", "en.vietstock.vn"}:
                if is_official_statement_title(item.get("title", ""), symbol):
                    candidates.extend(expand_vietstock_filing_page(item, symbol))
            elif item["allowlisted"] and (
                is_vietstock_statement_pdf(url, symbol)
                or is_official_statement_title(
                    item.get("title", ""), symbol,
                    require_symbol=host not in issuer_domains
                )
            ):
                # On the issuer's own allowlisted domain, official filing titles may omit
                # the ticker. Keep financial-statement wording and analyst-material exclusions.
                candidates.append(item)
        time.sleep(0.2)
    deduped, urls = [], set()
    for item in candidates:
        if item.get("url") not in urls:
            urls.add(item.get("url"))
            deduped.append(item)
    print(json.dumps({"event":"discovery_summary","symbol":symbol,"queries":len(queries),"candidates":len(deduped)}, ensure_ascii=False))
    return deduped

def download_candidate(candidate, job_dir):
    url = candidate["url"]
    host = (urlparse(url).hostname or "").lower()
    approved_attachment = candidate.get("official_filing_page") is True and host in {"static1.vietstock.vn", "static2.vietstock.vn", "vietstock.vn"}
    if not candidate.get("allowlisted") or (not domain_allowed(url, ALLOWED_DOMAINS) and not approved_attachment):
        return {"url":url,"title":candidate.get("title"),"status":"blocked_untrusted_domain","host":host}
    try:
        with SESSION.get(url, timeout=40, stream=True, allow_redirects=True) as response:
            response.raise_for_status()
            final_url = response.url
            final_host = (urlparse(final_url).hostname or "").lower()
            redirect_is_filing_attachment = (
                (candidate.get("official_filing_page") is True and final_host in {"static1.vietstock.vn", "static2.vietstock.vn", "vietstock.vn"})
                or is_vietstock_statement_pdf(final_url, candidate.get("symbol", ""))
            )
            if not domain_allowed(final_url, ALLOWED_DOMAINS) and not redirect_is_filing_attachment:
                return {"url":url,"status":"blocked_redirect_outside_allowlist","final_url":final_url}
            ctype = response.headers.get("Content-Type","")
            if not ("pdf" in ctype.lower() or "spreadsheet" in ctype.lower() or urlparse(final_url).path.lower().endswith((".pdf",".xlsx",".xls"))):
                return {"url":url,"status":"skipped_not_document","content_type":ctype}
            declared = int(response.headers.get("Content-Length","0") or 0)
            if declared > MAX_BYTES: return {"url":url,"status":"skipped_too_large","bytes":declared}
            data = bytearray()
            for chunk in response.iter_content(1024*64):
                if not chunk: continue
                data.extend(chunk)
                if len(data) > MAX_BYTES: return {"url":url,"status":"skipped_too_large","bytes":len(data)}
            if not data: return {"url":url,"status":"empty"}
            suffix = safe_name(final_url, ctype)
            digest = hashlib.sha256(data).hexdigest()
            name = digest[:16] + suffix
            job_dir.mkdir(parents=True, exist_ok=True)
            path = job_dir / name
            path.write_bytes(data)
            extracted = extract_file(path, ctype)
            extracted_path = path.with_suffix(path.suffix + ".extracted.json")
            save(extracted_path, extracted)
            return {"url":url,"final_url":final_url,"title":candidate.get("title"),"host":urlparse(final_url).hostname,"status":"downloaded_needs_review","file":str(path.relative_to(ROOT)),"extracted_file":str(extracted_path.relative_to(ROOT)),"sha256":digest,"bytes":len(data),"content_type":ctype,"extraction":extracted.get("extraction"),"pages":extracted.get("page_count"),"downloaded_at":NOW,"official_filing_page":candidate.get("filing_page"),"filing_page_title":candidate.get("filing_page_title")}
    except Exception as exc:
        return {"url":url,"title":candidate.get("title"),"status":"download_error","error":str(exc)[:1000]}

def main():
    global ALLOWED_DOMAINS
    sources = load(SOURCES_PATH, {"allowedDomains":[]})
    ALLOWED_DOMAINS = sorted(set(str(x).lower().strip(".") for x in sources.get("allowedDomains",[]) if x))
    if not ALLOWED_DOMAINS:
        print("No allowlisted domains configured. Add official domains to config/source-registry.json; worker will not download from unverified domains.", file=sys.stderr)
    queue = load(QUEUE_PATH, {"schemaVersion":1,"updatedAt":None,"jobs":[]})
    securities = load(SEC_PATH, {"securities":[]})
    jobs = queue.setdefault("jobs", [])
    known = {j.get("id") for j in jobs}
    # Refresh discovery weekly for every enabled security; avoid creating a new job every day.
    last_processed = {}
    for existing in jobs:
        symbol = existing.get("symbol")
        stamp = existing.get("processedAt") or existing.get("createdAt")
        if symbol and stamp and (symbol not in last_processed or stamp > last_processed[symbol]):
            last_processed[symbol] = stamp
    for sec in securities.get("securities",[]):
        symbol = str(sec.get("symbol","")).upper()
        last_stamp = last_processed.get(symbol)
        refresh_due = not last_stamp
        if last_stamp:
            try:
                age = datetime.now(timezone.utc) - datetime.fromisoformat(last_stamp.replace("Z","+00:00"))
                refresh_due = age.days >= 7
            except Exception:
                refresh_due = True
        if sec.get("enabled",True) and symbol and refresh_due:
            job_id = "auto-" + symbol.lower() + "-" + datetime.now(timezone.utc).strftime("%Y%m%d")
            if job_id not in known:
                jobs.append({"id":job_id,"symbol":symbol,"startYear":int(securities.get("defaultStartYear",2024)),"reportType":"both" if len(sec.get("reportTypes",[]))>1 else (sec.get("reportTypes") or ["consolidated"])[0],"status":"queued","createdAt":NOW,"attempts":0,"sourceCandidates":[],"downloadedFiles":[],"verifiedPeriods":[],"origin":"scheduled_registry"})
                known.add(job_id)
    summary = {"started_at":NOW,"jobs_processed":0,"downloaded":0,"needs_review":0,"errors":0,"allowlisted_domains":ALLOWED_DOMAINS}
    # Do not let a few repeatedly failing early jobs starve the rest of the ticker queue.
    # Process never-attempted queued jobs first; retry failed jobs only after queued coverage.
    jobs.sort(key=lambda job: (0 if job.get("status") == "queued" else 1, job.get("createdAt", "")))
    for job in jobs:
        if summary["jobs_processed"] >= MAX_JOBS_PER_RUN:
            break
        if job.get("status") not in {"queued","failed"}: continue
        if job.get("status") == "failed" and int(job.get("attempts", 0)) >= 3:
            continue
        job["status"]="searching"; job["updatedAt"]=NOW; job["attempts"]=int(job.get("attempts",0))+1
        candidates = discover_for_job(job, ALLOWED_DOMAINS)
        job["sourceCandidates"] = candidates[:80]
        job_dir = OUT / job["symbol"] / job["id"]
        results = []
        for candidate in candidates:
            if len([r for r in results if r.get("status")=="downloaded_needs_review"]) >= MAX_PER_JOB: break
            result = download_candidate(candidate, job_dir)
            results.append(result)
            if result.get("status")=="downloaded_needs_review": summary["downloaded"] += 1
            if result.get("status")=="download_error": summary["errors"] += 1
        job["downloadedFiles"] = results
        downloaded_any = any(r.get("status") == "downloaded_needs_review" for r in results)
        job["status"]="needs_review" if downloaded_any else "failed"
        job["lastError"] = None if downloaded_any else "Không tải được tài liệu từ miền đã cho phép; kiểm tra sourceCandidates và cấu hình allowlist."
        job["processedAt"]=NOW
        summary["jobs_processed"] += 1
        if job["status"]=="needs_review": summary["needs_review"] += 1
        print(json.dumps({"job":job["id"],"symbol":job["symbol"],"status":job["status"],"candidates":len(candidates),"downloaded":sum(1 for r in results if r.get("status")=="downloaded_needs_review")},ensure_ascii=False))
    queue["updatedAt"]=NOW
    save(QUEUE_PATH, queue)
    save(ROOT / "reports/worker-last-run.json", summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
