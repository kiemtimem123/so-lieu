#!/usr/bin/env python3
"""Collect and archive VietstockFinance statements first; OCR is handled by the separate post-archive workflow."""
from __future__ import annotations
import hashlib, json, os, re, sys, time, io, zipfile
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
MAX_BYTES = int(os.getenv("MAX_REPORT_BYTES", str(25 * 1024 * 1024)))
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
            for i, page in enumerate(reader.pages[:20]):
                text = page.extract_text() or ""
                if text.strip(): pages.append({"page": i + 1, "text": text[:25000]})
            return {"kind":"pdf", "pages":pages, "page_count":len(reader.pages), "extraction":"text", "note":None if pages else "PDF không có lớp văn bản; có thể là bản scan cần OCR thủ công."}
        except Exception as exc:
            return {"kind":"pdf", "pages":[], "extraction":"failed", "note":str(exc)}
    if suffix == ".zip" or "zip" in content_type.lower():
        try:
            from pypdf import PdfReader
            entries = []
            with zipfile.ZipFile(path, "r") as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    name = member.filename.replace("\\", "/")
                    # Ignore path traversal, nested archives and non-report payloads.
                    if name.startswith("/") or any(part == ".." for part in name.split("/")):
                        continue
                    if not name.lower().endswith((".pdf", ".xlsx", ".xls")) or member.file_size > MAX_BYTES:
                        continue
                    raw = archive.read(member)
                    if name.lower().endswith(".pdf"):
                        try:
                            reader = PdfReader(io.BytesIO(raw))
                            pages = []
                            for i, page in enumerate(reader.pages[:20]):
                                page_text = page.extract_text() or ""
                                if page_text.strip():
                                    pages.append({"page":i+1,"text":page_text[:25000]})
                            entries.append({"name":name,"kind":"pdf","bytes":len(raw),
                                            "pages":pages,"page_count":len(reader.pages),
                                            "extraction":"text",
                                            "note":None if pages else "PDF trong ZIP không có lớp văn bản; cần xem thủ công."})
                        except Exception as exc:
                            entries.append({"name":name,"kind":"pdf","bytes":len(raw),
                                            "pages":[],"extraction":"failed","note":str(exc)[:500]})
                    else:
                        entries.append({"name":name,"kind":"spreadsheet","bytes":len(raw),
                                        "extraction":"archive_member_not_parsed"})
            return {"kind":"zip","members":entries,"member_count":len(entries),
                    "extraction":"archive_members","note":None if entries else "ZIP không có PDF/Excel báo cáo hỗ trợ."}
        except Exception as exc:
            return {"kind":"zip","members":[],"extraction":"failed","note":str(exc)[:1000]}
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
    if suffix not in {".pdf",".xlsx",".xls",".zip"}:
        suffix = ".pdf" if "pdf" in content_type.lower() else ".xlsx" if "spreadsheetml" in content_type.lower() else ".zip" if "zip" in content_type.lower() else ".bin"
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

def _vietstock_epoch_date(value):
    """Convert Vietstock /Date(milliseconds)/ metadata into a stable ISO date."""
    match = re.search(r"/Date\((-?\d+)\)/", str(value or ""))
    if not match:
        return None
    try:
        stamp = int(match.group(1)) / 1000.0
        return datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None

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
    """Use only VietstockFinance's own AJAX-backed per-symbol document list."""
    symbol = str(job["symbol"]).upper()
    start_year = int(job.get("startYear", 2024))
    index_url = vietstock_document_index_url(symbol)
    base_url = "https://finance.vietstock.vn"
    requested_type = str(job.get("reportType", "both")).casefold()
    try:
        page_response = SESSION.get(index_url, timeout=35, allow_redirects=True)
        page_response.raise_for_status()
    except Exception as exc:
        print(json.dumps({"event":"vietstock_index_fetch_failed","symbol":symbol,
                          "url":index_url,"error":str(exc)[:800]},ensure_ascii=False))
        return []

    soup = BeautifulSoup(page_response.text, "html.parser")
    page_title = soup.title.get_text(" ",strip=True) if soup.title else ""
    # Match the site's own request token: hidden input first, then JS assignment.
    token = ""
    token_input = soup.find("input", attrs={"name":"__RequestVerificationToken"})
    if token_input:
        token = str(token_input.get("value") or "")
    if not token:
        match = re.search(r"""(?:_tokenString|__RequestVerificationToken)\s*[:=]\s*['"]([^'"]+)['"]""",
                          page_response.text, re.I)
        if match:
            token = match.group(1)
    try:
        doctype = int(parse_qs(urlparse(index_url).query).get("doctype", ["1"])[0] or 1)
    except (TypeError, ValueError):
        doctype = 1
    headers = {
        "Referer": page_response.url,
        "Origin": base_url,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    def call_json(path, method="GET", payload=None):
        url = requests.compat.urljoin(base_url, path)
        try:
            if method == "POST":
                data = dict(payload or {})
                if token:
                    data["__RequestVerificationToken"] = token
                resp = SESSION.post(url, data=data, headers=headers, timeout=20)
            else:
                resp = SESSION.get(url, headers=headers, timeout=20)
            ctype = resp.headers.get("Content-Type","")
            try:
                parsed = resp.json()
            except Exception:
                parsed = None
            print(json.dumps({
                "event":"vietstock_api_probe","symbol":symbol,"endpoint":path,
                "status":resp.status_code,"content_type":ctype,
                "bytes":len(resp.content),"json_type":type(parsed).__name__ if parsed is not None else None,
                "json_preview":str(parsed)[:700] if parsed is not None else resp.text[:500]
            },ensure_ascii=False))
            resp.raise_for_status()
            return parsed
        except Exception as exc:
            print(json.dumps({"event":"vietstock_api_failed","symbol":symbol,
                              "endpoint":path,"error":str(exc)[:600]},ensure_ascii=False))
            return None

    # Same endpoints as the public page, but request only years in the user's scope.
    call_json("/data/getdocumenttype", "GET")
    year_response = call_json("/data/getyearreport", "POST", {"code":symbol})

    def years_from_response(value):
        found = set()
        def walk(node):
            if isinstance(node, dict):
                for key, item in node.items():
                    if str(key).casefold() in {"year","reportyear","value","id"}:
                        if isinstance(item, (int,float)) or (isinstance(item,str) and re.fullmatch(r"20\d{2}",item.strip())):
                            y = int(item)
                            if start_year <= y <= datetime.now(timezone.utc).year + 1:
                                found.add(y)
                    walk(item)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, (int,float)) or (isinstance(node,str) and re.fullmatch(r"20\d{2}",node.strip())):
                y = int(node)
                if start_year <= y <= datetime.now(timezone.utc).year + 1:
                    found.add(y)
        walk(value)
        return found

    # The endpoint usually returns the years available on this symbol's Vietstock
    # index. Add each calendar year through the current year as a safe fallback.
    years_to_query = set(range(start_year, datetime.now(timezone.utc).year + 1))
    years_to_query.update(years_from_response(year_response))
    years_to_query = sorted(years_to_query)
    def rows_from_json(value):
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for key in ("data","Data","items","Items","result","Result","rows","Rows"):
                sub = value.get(key)
                if isinstance(sub, list):
                    return sub
        return []

    seen_rows = set()
    all_rows = []
    total_rows_by_year = {}
    def add_rows(items):
        for row in items:
            if not isinstance(row, dict):
                continue
            ident = str(row.get("Id") or row.get("FileInfoID") or row.get("Url") or row.get("FullName") or row.get("Title") or "")
            if ident and ident not in seen_rows:
                seen_rows.add(ident)
                all_rows.append(row)

    for report_year in years_to_query:
        first_page = call_json("/data/getdocument", "POST",
                               {"code":symbol,"page":1,"type":doctype,"year":report_year})
        rows = rows_from_json(first_page)
        add_rows(rows)
        total_rows = 0
        if rows:
            try:
                total_rows = int(rows[0].get("TotalRow") or rows[0].get("totalRow") or 0)
            except (TypeError, ValueError):
                total_rows = 0
        total_rows_by_year[str(report_year)] = total_rows or len(rows)
        if total_rows:
            pages = min(max((total_rows + 19) // 20, 1), 30)
        else:
            pages = 1 if len(rows) < 20 else 30
        for page in range(2, pages + 1):
            result = call_json("/data/getdocument", "POST",
                               {"code":symbol,"page":page,"type":doctype,"year":report_year})
            page_rows = rows_from_json(result)
            if not page_rows:
                break
            before = len(all_rows)
            add_rows(page_rows)
            if len(all_rows) == before or len(page_rows) < 20:
                break
    candidates = []
    for row in all_rows:
        title = str(row.get("FullName") or row.get("Title") or row.get("FileName") or "").strip()
        # Some rows use separate Title/FullName/Url labels; combine metadata for filtering.
        name = str(row.get("Title") or "")
        full_name = str(row.get("FullName") or "")
        file_url = str(row.get("Url") or row.get("FileUrl") or row.get("DownloadUrl") or "").strip()
        updated = str(row.get("LastUpdate") or row.get("PublishDate") or row.get("PublishedAt") or "")
        evidence = " ".join([title,name,full_name,file_url,updated])
        if not is_financial_statement_document(evidence):
            continue
        if any(word in evidence.casefold() for word in [
            "báo cáo phân tích","bao cao phan tich","khuyến nghị","định giá",
            "dự phóng","forecast","equity research","brokerage","triển vọng",
            "khóa học","khoa hoc","đào tạo","dao tao","training","webinar","seminar"
        ]):
            continue
        period = _period_from_report_text(evidence)
        year, published_at = _extract_report_year_and_date(evidence)
        period_year = re.match(r"(20\d{2})-", period or "")
        if period_year:
            year = int(period_year.group(1))
        if year is not None and year < start_year:
            continue
        if year is None:
            continue
        if requested_type == "consolidated" and re.search(r"riêng\s*lẻ|rieng\s*le|separate financial|công ty\s*mẹ|cong ty\s*me|parent company", evidence, re.I):
            continue
        if requested_type == "separate" and re.search(r"hợp\s*nhất|hop\s*nhat|consolidated", evidence, re.I):
            continue
        if not file_url:
            continue
        absolute = requests.compat.urljoin(base_url, file_url)
        host = (urlparse(absolute).hostname or "").lower()
        if not host.endswith("vietstock.vn") and host != "vietstock.vn":
            continue
        candidates.append({
            "url":absolute,"title":title or name or full_name or absolute,
            "host":host,"allowlisted":domain_allowed(absolute,allowed_domains),
            "symbol":symbol,"query":"VietstockFinance /data/getdocument",
            "page_url":index_url,"document_index":index_url,
            "document_id":row.get("FileInfoID") or row.get("Id"),
            "report_year":year,"published_at":published_at or _vietstock_epoch_date(updated),
            "period":period,"report_type":job.get("reportType","both"),
            "vietstock_title":name,"full_name":full_name,
            "file_ext":row.get("FileExt"),"last_update":updated,
            "total_rows":total_rows
        })
    print(json.dumps({
        "event":"vietstock_index_discovery","symbol":symbol,"index_url":index_url,
        "http_status":page_response.status_code,"page_title":page_title,
        "ajax_rows":len(all_rows),"total_rows":total_rows,
        "candidate_count":len(candidates),
        "sample_rows":[{k:r.get(k) for k in ("Title","FullName","Url","FileExt","LastUpdate","TotalRow")} for r in all_rows[:5]]
    },ensure_ascii=False))
    deduped=[]
    seen_urls=set()
    for candidate in candidates:
        if candidate["url"] not in seen_urls:
            seen_urls.add(candidate["url"])
            deduped.append(candidate)
    return deduped

def download_candidate(candidate, job_dir):
    url = candidate["url"]
    host = (urlparse(url).hostname or "").lower()
    approved_attachment = candidate.get("official_filing_page") is True and host in {"static1.vietstock.vn", "static2.vietstock.vn", "vietstock.vn"}
    if not candidate.get("allowlisted") or (not domain_allowed(url, ALLOWED_DOMAINS) and not approved_attachment):
        return {"url":url,"title":candidate.get("title"),"status":"blocked_untrusted_domain","host":host}
    try:
        with SESSION.get(url, timeout=18, stream=True, allow_redirects=True) as response:
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
            if not ("pdf" in ctype.lower() or "spreadsheet" in ctype.lower() or "zip" in ctype.lower() or urlparse(final_url).path.lower().endswith((".pdf",".xlsx",".xls",".zip"))):
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
            return {"url":url,"final_url":final_url,"title":candidate.get("title"),"host":urlparse(final_url).hostname,"status":"downloaded_needs_review","file":str(path.relative_to(ROOT)),"extracted_file":str(extracted_path.relative_to(ROOT)),"sha256":digest,"bytes":len(data),"content_type":ctype,"extraction":extracted.get("extraction"),"pages":extracted.get("page_count"),"downloaded_at":NOW,"source":"VietstockFinance document index","document_index":candidate.get("document_index"),"index_title":candidate.get("index_title") or candidate.get("title"),"period":candidate.get("period"),"report_year":candidate.get("report_year"),"published_at":candidate.get("published_at"),"last_update":candidate.get("last_update"),"file_ext":candidate.get("file_ext"),"document_id":candidate.get("document_id"),"report_type":candidate.get("report_type"),"official_filing_page":candidate.get("filing_page"),"filing_page_title":candidate.get("filing_page_title")}
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
    jobs.sort(key=lambda job: (0 if job.get("status") == "queued" else 1, int(job.get("priority", 50)), 0 if str(job.get("symbol", "")).upper() == "MBB" else 1, job.get("createdAt", "")))
    for job in jobs:
        if summary["jobs_processed"] >= MAX_JOBS_PER_RUN:
            break
        if job.get("status") not in {"queued","failed"}: continue
        if job.get("status") == "failed" and int(job.get("attempts", 0)) >= 3:
            continue
        job["status"]="searching"; job["updatedAt"]=NOW; job["attempts"]=int(job.get("attempts",0))+1
        candidates = discover_for_job(job, ALLOWED_DOMAINS)
        # Avoid re-downloading the same Vietstock URL when a follow-up job for
        # this ticker is used to collect the remaining statements.
        already_downloaded_urls = set()
        for previous_job in jobs:
            if previous_job is job or str(previous_job.get("symbol","")).upper() != str(job.get("symbol","")).upper():
                continue
            for previous_file in previous_job.get("downloadedFiles", []) or []:
                if previous_file.get("status") != "downloaded_needs_review":
                    continue
                for key in ("url", "final_url"):
                    previous_url = previous_file.get(key)
                    if previous_url:
                        already_downloaded_urls.add(str(previous_url))
        before_dedup = len(candidates)
        candidates = [c for c in candidates if str(c.get("url","")) not in already_downloaded_urls]
        print(json.dumps({"event":"deduplicate_previous_downloads","symbol":job.get("symbol"),
                          "candidate_count_before":before_dedup,"already_downloaded_urls":len(already_downloaded_urls),
                          "candidate_count_after":len(candidates)},ensure_ascii=False))
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
