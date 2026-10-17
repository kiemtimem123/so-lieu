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
        response = SESSION.post(url, data={"q": query}, timeout=25)
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

def discover_for_job(job, allowed_domains):
    symbol = job["symbol"]
    start = int(job.get("startYear", 2024))
    report_type = job.get("reportType", "consolidated")
    report_words = "báo cáo tài chính quý" if report_type != "both" else "báo cáo tài chính quý hợp nhất riêng lẻ"
    queries = [
        f'"{symbol}" {report_words} {start} filetype:pdf',
        f'"{symbol}" báo cáo tài chính {datetime.now().year} filetype:pdf',
        f'site:hsx.vn "{symbol}" báo cáo tài chính filetype:pdf',
        f'site:hnx.vn "{symbol}" báo cáo tài chính filetype:pdf',
    ]
    candidates, seen = [], set()
    for q in queries:
        results = search_web(q)
        for item in results:
            if "url" not in item: continue
            url = item["url"]
            if url in seen: continue
            seen.add(url)
            host = (urlparse(url).hostname or "").lower()
            item.update({"query":q,"host":host,"allowlisted":domain_allowed(url,allowed_domains)})
            candidates.append(item)
        time.sleep(1.0)
    return candidates

def download_candidate(candidate, job_dir):
    url = candidate["url"]
    if not candidate.get("allowlisted"):
        return {"url":url,"title":candidate.get("title"),"status":"blocked_untrusted_domain","host":candidate.get("host")}
    try:
        with SESSION.get(url, timeout=40, stream=True, allow_redirects=True) as response:
            response.raise_for_status()
            final_url = response.url
            if not domain_allowed(final_url, ALLOWED_DOMAINS):
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
            return {"url":url,"final_url":final_url,"title":candidate.get("title"),"host":urlparse(final_url).hostname,"status":"downloaded_needs_review","file":str(path.relative_to(ROOT)),"extracted_file":str(extracted_path.relative_to(ROOT)),"sha256":digest,"bytes":len(data),"content_type":ctype,"extraction":extracted.get("extraction"),"pages":extracted.get("page_count"),"downloaded_at":NOW}
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
    # Create discovery jobs for enabled securities that have no active job.
    active_symbols = {j.get("symbol") for j in jobs}
    for sec in securities.get("securities",[]):
        symbol = str(sec.get("symbol","")).upper()
        if sec.get("enabled",True) and symbol and symbol not in active_symbols:
            job_id = f"auto-{symbol.lower()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            if job_id not in known:
                jobs.append({"id":job_id,"symbol":symbol,"startYear":int(securities.get("defaultStartYear",2024)),"reportType":"both" if len(sec.get("reportTypes",[]))>1 else (sec.get("reportTypes") or ["consolidated"])[0],"status":"queued","createdAt":NOW,"attempts":0,"sourceCandidates":[],"downloadedFiles":[],"verifiedPeriods":[],"origin":"scheduled_registry"})
                known.add(job_id)
    summary = {"started_at":NOW,"jobs_processed":0,"downloaded":0,"needs_review":0,"errors":0,"allowlisted_domains":ALLOWED_DOMAINS}
    for job in jobs:
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
