#!/usr/bin/env python3
"""Collect and audit quarterly financial statements from VietstockFinance per-symbol document indexes."""
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

def vietstock_document_index_url(symbol):
    """The per-symbol Vietstock document index is the primary discovery source."""
    return f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1"

def is_financial_statement_document(text):
    """Keep BCTC documents and reject analyst research, estimates and recommendations."""
    t = (text or "").casefold()
    reject = [
        "báo cáo phân tích", "bao cao phan tich", "phân tích cổ phiếu",
        "khuyến nghị", "định giá", "giá mục tiêu", "dự phóng", "du phong",
        "forecast", "triển vọng", "cập nhật kqkd", "equity research",
        "analyst", "brokerage", "mua", "bán", "nắm giữ", "annual report",
        "khóa học", "khoa hoc", "đào tạo", "dao tao", "training", "đọc hiểu", "doc hieu", "webinar", "seminar"
    ]
    if any(term in t for term in reject):
        return False
    return any(term in t for term in [
        "báo cáo tài chính", "bao cao tai chinh", "bctc",
        "financial statement", "financial statements"
    ])

def _document_context(anchor):
    """Get the closest useful row/card around a document link."""
    for tag in ("tr", "li", "article"):
        node = anchor.find_parent(tag)
        if node and len(node.get_text(" ", strip=True)) > 20:
            return node
    node = anchor.parent
    for _ in range(3):
        if not node:
            break
        text = node.get_text(" ", strip=True)
        if len(text) > 20:
            return node
        node = node.parent
    return anchor

def _extract_report_year_and_date(text):
    text = text or ""
    year_matches = [int(x) for x in re.findall(r"\b(20\d{2})\b", text)]
    year = max(year_matches) if year_matches else None
    date = None
    m = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if m:
        try:
            date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date().isoformat()
        except ValueError:
            pass
    if not date:
        m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b", text)
        if m:
            try:
                date = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date().isoformat()
            except ValueError:
                pass
    return year, date

def _period_from_report_text(text):
    t = (text or "").casefold()
    m = re.search(r"\b(?:quý|q)\s*([1-4i]{1,2})\D{0,16}(20\d{2})", t)
    if m:
        q = m.group(1).upper()
        q = {"I":"1","II":"2","III":"3","IV":"4"}.get(q, q)
        if q.isdigit() and int(q) in range(1,5):
            return f"{m.group(2)}-Q{q}"
    m = re.search(r"\b(20\d{2})\D{0,12}(?:quý|q)\s*([1-4])\b", t)
    if m:
        return f"{m.group(1)}-Q{m.group(2)}"
    m = re.search(r"\b(?:6 tháng|bán niên|6m|6t)\D{0,12}(20\d{2})", t)
    if m:
        return f"{m.group(1)}-H1"
    m = re.search(r"\b(?:9 tháng|9m|9t)\D{0,12}(20\d{2})", t)
    if m:
        return f"{m.group(1)}-9M"
    m = re.search(r"\b(?:năm|year)\D{0,8}(20\d{2})", t)
    if m:
        return f"{m.group(1)}-FY"
    return None

def _urls_from_document_page(url, symbol, row_text, index_url):
    """Expand a Vietstock document detail page to its direct PDF/XLS attachments."""
    host = (urlparse(url).hostname or "").lower()
    path = urlparse(url).path.lower()
    if not (host == "finance.vietstock.vn" and path.startswith("/downloadedoc/")):
        return [{"url":url, "title":row_text[:300], "symbol":symbol, "allowlisted":True,
                 "query":"Vietstock document index", "host":host, "page_url":index_url,
                 "document_index":index_url}]
    try:
        response = SESSION.get(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        ctype = (response.headers.get("Content-Type") or "").lower()
        if "pdf" in ctype or response.content[:5] == b"%PDF-":
            return [{"url":response.url, "title":row_text[:300], "symbol":symbol,
                     "allowlisted":True, "query":"Vietstock document index", "host":urlparse(response.url).hostname,
                     "page_url":index_url, "document_index":index_url}]
        soup = BeautifulSoup(response.text, "html.parser")
        found = []
        for a in soup.find_all("a", href=True):
            href = requests.compat.urljoin(response.url, a["href"])
            ap = urlparse(href)
            label = a.get_text(" ", strip=True)
            evidence = (row_text + " " + label + " " + href).casefold()
            if ap.hostname and (ap.hostname.lower().endswith("vietstock.vn")) and (
                ap.path.lower().endswith((".pdf", ".xlsx", ".xls")) or
                (ap.hostname.lower() in {"static1.vietstock.vn","static2.vietstock.vn"} and ".pdf" in ap.path.lower())
            ):
                if is_financial_statement_document(evidence) or is_financial_statement_document(row_text):
                    found.append({"url":href,"title":label or row_text[:300],"symbol":symbol,
                                  "allowlisted":True,"query":"Vietstock document index",
                                  "host":ap.hostname.lower(),"page_url":response.url,
                                  "document_index":index_url,"document_detail_url":response.url})
        # Some detail pages embed attachment URLs inside script/json instead of <a> elements.
        for href in re.findall(r"""https?://[^"'\s<>]+?\.(?:pdf|xlsx?)(?:\?[^"'\s<>]*)?""", response.text, re.I):
            ap = urlparse(href)
            evidence = (row_text + " " + href).casefold()
            if ap.hostname and ap.hostname.lower().endswith("vietstock.vn") and (
                is_financial_statement_document(evidence) or is_financial_statement_document(row_text)
            ):
                found.append({"url":href,"title":row_text[:300],"symbol":symbol,
                              "allowlisted":True,"query":"Vietstock document index",
                              "host":ap.hostname.lower(),"page_url":response.url,
                              "document_index":index_url,"document_detail_url":response.url})
        # If Vietstock serves the BCTC directly at /downloadedoc/{id}, let the
        # normal downloader validate Content-Type and PDF signature rather than guessing.
        if not found and is_financial_statement_document(row_text):
            found.append({"url":response.url,"title":row_text[:300],"symbol":symbol,
                          "allowlisted":True,"query":"Vietstock document index",
                          "host":urlparse(response.url).hostname,"page_url":response.url,
                          "document_index":index_url})
        return found
    except Exception as exc:
        print(json.dumps({"event":"vietstock_document_detail_failed","symbol":symbol,
                          "url":url,"error":str(exc)[:500]},ensure_ascii=False))
        return []

def discover_for_job(job, allowed_domains):
    """Discover issuer financial statements from the single Vietstock document index.

    This intentionally does not search individual issuer websites or generic web results.
    The index link and any direct report attachment URL are kept in the candidate metadata.
    """
    symbol = str(job["symbol"]).upper()
    start = int(job.get("startYear", 2024))
    index_url = vietstock_document_index_url(symbol)
    try:
        response = SESSION.get(index_url, timeout=35, allow_redirects=True)
        response.raise_for_status()
    except Exception as exc:
        print(json.dumps({"event":"vietstock_index_fetch_failed","symbol":symbol,
                          "url":index_url,"error":str(exc)[:800]},ensure_ascii=False))
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    page_title = soup.title.get_text(" ",strip=True) if soup.title else ""
    # The visible document grid can be populated by page JavaScript. Log the
    # scripts and likely document-list routes so the index API can be wired in
    # without reverting to issuer-site searching.
    script_srcs = [requests.compat.urljoin(response.url, s.get("src", "")) for s in soup.select("script[src]")]
    inline_js = "\\n".join(s.get_text(" ",strip=True) for s in soup.select("script"))
    route_hints = sorted(set(re.findall(
        r"""['"]([^'"]*(?:/data/|/home/|document|document|tai-lieu|report|attachment|download)[^'"]*)['"]""",
        inline_js, re.I
    )))
    # Fetch the relevant first-party scripts once and inspect only route strings
    # surrounding the document tab names. The public page loads its document grid
    # asynchronously, so anchor scraping alone misses the actual rows.
    script_diagnostics = []
    for script_url in script_srcs:
        if not any(part in script_url.casefold() for part in (
            "/bundles/company/document/jsx", "/bundles/company/jsx",
            "/bundles/company/jsnew"
        )):
            continue
        try:
            js_response = SESSION.get(script_url, timeout=25)
            js_response.raise_for_status()
            js = js_response.text
            routes = sorted(set(re.findall(
                r"""['"]([^'"]{1,220}(?:/Home/|/data/|Document|document|tai-lieu|download|Report|report)[^'"]{0,120})['"]""",
                js, re.I
            )))
            snippets = []
            for term in ("Documents_All", "Documents_Period", "Documents_Year", "Tab_Documents"):
                at = js.casefold().find(term.casefold())
                if at >= 0:
                    snippets.append({"term":term,"text":js[max(0,at-700):min(len(js),at+1600)]})
            script_diagnostics.append({
                "url":script_url,"status":js_response.status_code,"bytes":len(js),
                "route_hints":routes[:150],"snippets":snippets[:12]
            })
        except Exception as exc:
            script_diagnostics.append({"url":script_url,"error":str(exc)[:400]})
    print(json.dumps({"event":"vietstock_index_js_diagnostic","symbol":symbol,
                      "script_count":len(script_srcs),"script_srcs":script_srcs[:50],
                      "inline_route_hints":route_hints[:100],
                      "first_party_script_diagnostics":script_diagnostics},ensure_ascii=False))
    candidates = []
    seen = set()

    def add_candidate(url, title, context_text):
        url = requests.compat.urljoin(response.url, url)
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http","https") or not (
            host == "finance.vietstock.vn" or host.endswith(".vietstock.vn") or host == "vietstock.vn"
        ):
            return
        evidence = " ".join([str(title or ""), str(context_text or ""), url])
        year, published_at = _extract_report_year_and_date(evidence)
        period = _period_from_report_text(evidence)
        period_year = re.match(r"(20\d{2})-", period or "")
        if period_year:
            year = int(period_year.group(1))
        # The page itself is pre-filtered by doctype=1 (financial documents).
        # Still explicitly reject research/recommendation items and limit the scope.
        if not is_financial_statement_document(evidence):
            return
        if any(word in evidence.casefold() for word in [
            "báo cáo phân tích","bao cao phan tich","khuyến nghị","định giá",
            "dự phóng","forecast","equity research","brokerage","triển vọng"
        ]):
            return
        requested_type = str(job.get("reportType","consolidated")).casefold()
        if requested_type == "consolidated" and re.search(r"riêng\s*lẻ|rieng\s*le|separate financial", evidence, re.I):
            return
        if requested_type == "separate" and re.search(r"hợp\s*nhất|hop\s*nhat|consolidated", evidence, re.I):
            return
        if year is not None and year < start:
            return
        if year is None:
            # Do not assume old dates are in scope. Keep only rows with a discoverable
            # year, except a direct BCTC PDF with a year in its filename.
            return
        if url in seen:
            return
        seen.add(url)
        candidates.append({
            "url":url,"title":str(title or context_text or url)[:500],
            "host":host,"allowlisted":domain_allowed(url,allowed_domains),
            "symbol":symbol,"query":"Vietstock per-symbol document index",
            "page_url":response.url,"document_index":index_url,
            "report_year":year,"published_at":published_at,
            "period":period,
            "report_type":job.get("reportType","consolidated")
        })

    # First pass: table rows/cards so titles, period and publication date remain attached.
    for a in soup.find_all("a", href=True):
        href = a.get("href","").strip()
        label = re.sub(r"\s+"," ",a.get_text(" ",strip=True)).strip()
        context = _document_context(a)
        context_text = re.sub(r"\s+"," ",context.get_text(" ",strip=True)).strip()
        evidence = " ".join([label,context_text,href])
        # Do not treat navigation links as documents; require a BCTC label in the item.
        if not is_financial_statement_document(evidence):
            continue
        if not re.search(r"(?:/downloadedoc/|\.pdf(?:\?|$)|\.xlsx?(?:\?|$)|download|attachment|/files?/)",href,re.I):
            continue
        display_title = label if is_financial_statement_document(label) else context_text
        add_candidate(href, display_title or label, context_text)

    # Second pass: pick up direct attachment URLs embedded in HTML/JSON/scripts.
    embedded = re.findall(
        r"""(?:https?:)?//[^"'\s<>]+?\.(?:pdf|xlsx?)(?:\?[^"'\s<>]*)?|(?:https?:)?//static[12]\.vietstock\.vn/[^"'\s<>]+""",
        response.text, re.I
    )
    for href in embedded:
        href = href.rstrip("),;")
        absolute = requests.compat.urljoin(response.url, href)
        filename = unquote(urlparse(absolute).path).rsplit("/",1)[-1]
        evidence = " ".join([page_title,filename,absolute])
        if not re.search(r"\b"+re.escape(symbol)+r"\b",evidence,re.I):
            # Document list pages can omit ticker in a direct filename, but must have
            # a financial-statement filename and be linked from this symbol's index.
            if not re.search(r"(?:bao.?cao.?tai.?chinh|bctc|financial.?statement)",filename,re.I):
                continue
        add_candidate(absolute, filename or page_title, evidence)

    print(json.dumps({"event":"vietstock_index_discovery","symbol":symbol,
                      "index_url":index_url,"http_status":response.status_code,
                      "page_title":page_title,"html_bytes":len(response.text),
                      "anchors":len(soup.find_all("a",href=True)),
                      "candidates":len(candidates)},ensure_ascii=False))

    expanded = []
    for item in candidates:
        attachments = _urls_from_document_page(item["url"],symbol,item["title"],index_url)
        for attachment in attachments:
            for key in ("report_year","published_at","period","report_type","query","document_index","page_url"):
                if attachment.get(key) is None and item.get(key) is not None:
                    attachment[key] = item[key]
            # Keep the row title/context from the per-symbol list for auditability.
            attachment["index_title"] = item.get("title")
        expanded.extend(attachments)
        time.sleep(0.15)
    deduped = []
    urls = set()
    for item in expanded:
        if item.get("url") and item["url"] not in urls:
            urls.add(item["url"])
            item["allowlisted"] = domain_allowed(item["url"], allowed_domains)
            deduped.append(item)
    print(json.dumps({"event":"vietstock_index_attachment_summary","symbol":symbol,
                      "index_url":index_url,"attachments":len(deduped)},ensure_ascii=False))
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
            return {"url":url,"final_url":final_url,"title":candidate.get("title"),"host":urlparse(final_url).hostname,"status":"downloaded_needs_review","file":str(path.relative_to(ROOT)),"extracted_file":str(extracted_path.relative_to(ROOT)),"sha256":digest,"bytes":len(data),"content_type":ctype,"extraction":extracted.get("extraction"),"pages":extracted.get("page_count"),"downloaded_at":NOW,"source":"VietstockFinance document index","document_index":candidate.get("document_index"),"index_title":candidate.get("index_title") or candidate.get("title"),"period":candidate.get("period"),"report_year":candidate.get("report_year"),"published_at":candidate.get("published_at"),"report_type":candidate.get("report_type"),"official_filing_page":candidate.get("filing_page"),"filing_page_title":candidate.get("filing_page_title")}
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
