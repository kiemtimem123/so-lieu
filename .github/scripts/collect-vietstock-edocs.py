#!/usr/bin/env python3
"""Crawl public Vietstock eDocuments pages and validate report PDFs.

This worker does not log in, bypass paywalls/CAPTCHAs, or archive PDFs by default.
PDF archival is intentionally disabled unless explicitly enabled after rights review.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "analysis" / "analysis-reports.json"
DATA_OUT = ROOT / "data" / "analysis-reports.json"
REPORT_DIR = ROOT / "reports" / "analysis" / "pdf"
BASES = [
    "https://edocs.vietstock.vn/",
    "https://finance.vietstock.vn/",
]
ALLOWED = {"edocs.vietstock.vn", "finance.vietstock.vn", "static1.vietstock.vn", "vietstock.vn", "www.vietstock.vn"}
SYMBOL = os.getenv("REPORT_TEST_SYMBOL", "MBB").upper()
MAX_PAGES = int(os.getenv("EDOCS_MAX_PAGES", "35"))
ALLOW_ARCHIVE = os.getenv("ALLOW_BROKER_PDF_ARCHIVE", "false").lower() == "true"
NOW = datetime.now(timezone.utc).isoformat()
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; solieutaichinh-edocs-catalog/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en;q=0.8",
})
DATE_RE = re.compile(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b")
TICKER_RE = re.compile(r"(?<![A-Z0-9])" + re.escape(SYMBOL) + r"(?![A-Z0-9])", re.I)


def allowed_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in ALLOWED)


def clean_url(url: str) -> str:
    return urldefrag(url.strip())[0]


def read_catalog():
    for path in (OUT, DATA_OUT):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {
        "schemaVersion": 1, "updatedAt": NOW,
        "description": "Danh mục riêng cho báo cáo phân tích của bên thứ ba; không trộn với báo cáo tài chính công bố chính thức.",
        "categories": [
            {"id":"stock_analysis","label":"Báo cáo phân tích cổ phiếu"},
            {"id":"forecast_earnings","label":"Dự phóng kết quả kinh doanh"},
            {"id":"recommendation_valuation","label":"Khuyến nghị và định giá"},
            {"id":"industry_report","label":"Báo cáo phân tích ngành"},
            {"id":"market_strategy","label":"Chiến lược thị trường và vĩ mô"},
            {"id":"brokerage_research","label":"Báo cáo nghiên cứu khác"},
        ],
        "reports": [], "errors": [],
        "policy": {"official_financial_statements":"reports/raw + config/report-queue.json",
                   "brokerage_research":"reports/analysis/analysis-reports.json",
                   "auto_publish_numbers":False,
                   "pdf_mirroring":"disabled_until_license_and_download_permissions_are_confirmed"}
    }


def get_page(url: str):
    try:
        response = SESSION.get(url, timeout=25, allow_redirects=True)
        response.raise_for_status()
        return response
    except Exception as exc:
        print(json.dumps({"event":"page_fetch_failed","url":url,"error":str(exc)}, ensure_ascii=False))
        return None


def is_pdf_response(response) -> bool:
    ctype = (response.headers.get("Content-Type") or "").lower()
    return "application/pdf" in ctype or response.content[:5] == b"%PDF-"


def validate_pdf(url: str):
    """Stream to a temporary file only; never persist to the repository by default."""
    try:
        with SESSION.get(url, timeout=45, stream=True, allow_redirects=True) as response:
            response.raise_for_status()
            ctype = (response.headers.get("Content-Type") or "").lower()
            first = next(response.iter_content(chunk_size=8192), b"")
            if not (first.startswith(b"%PDF-") or "application/pdf" in ctype):
                return {"ok":False,"url":response.url,"reason":"response_not_pdf","content_type":ctype}
            # pypdf requires seekable input; temporary file is ephemeral and deleted on close.
            with tempfile.TemporaryFile() as tmp:
                tmp.write(first)
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        tmp.write(chunk)
                tmp.seek(0)
                reader = PdfReader(tmp, strict=False)
                if reader.is_encrypted:
                    return {"ok":False,"url":response.url,"reason":"encrypted_pdf"}
                pages = len(reader.pages)
                if pages < 1:
                    return {"ok":False,"url":response.url,"reason":"empty_pdf"}
                return {"ok":True,"url":response.url,"pages":pages,"bytes":tmp.tell(),"content_type":ctype}
    except Exception as exc:
        return {"ok":False,"url":url,"reason":"download_or_parse_failed","error":str(exc)}


def guess_category(title: str) -> str:
    t = title.casefold()
    if any(x in t for x in ("ngành", "industry", "sector")):
        return "industry_report"
    if any(x in t for x in ("chiến lược", "vĩ mô", "market outlook", "macro")):
        return "market_strategy"
    if any(x in t for x in ("khuyến nghị", "giá mục tiêu", "định giá", "mua", "bán", "nắm giữ", "target price")):
        return "recommendation_valuation"
    if any(x in t for x in ("dự phóng", "dự báo", "forecast", "outlook", "kết quả kinh doanh")):
        return "forecast_earnings"
    if any(x in t for x in ("phân tích", "cập nhật", "equity", "company report", "báo cáo cổ phiếu")):
        return "stock_analysis"
    return "brokerage_research"


def main():
    catalog = read_catalog()
    existing = {r.get("url"): r for r in catalog.get("reports", []) if r.get("url")}
    queue = list(dict.fromkeys(BASES))
    visited = set()
    candidates = {}
    pages_read = 0

    while queue and pages_read < MAX_PAGES:
        page_url = queue.pop(0)
        page_url = clean_url(page_url)
        if page_url in visited or not allowed_url(page_url):
            continue
        visited.add(page_url)
        response = get_page(page_url)
        if not response:
            continue
        pages_read += 1
        final_url = response.url
        if is_pdf_response(response):
            if TICKER_RE.search(page_url):
                candidates[page_url] = {"title": page_url.rsplit("/", 1)[-1], "url": final_url, "page_url": page_url}
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        # Search visible links and buttons for ticker/report labels; also inspect same-site detail pages.
        for a in soup.select("a[href]"):
            href = clean_url(urljoin(final_url, a.get("href", "")))
            if not href.startswith("http") or not allowed_url(href):
                continue
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
            combined = (title + " " + href).upper()
            looks_like_report = bool(TICKER_RE.search(combined)) or any(
                word in combined.lower() for word in ("downloadedoc", "edocs/", ".pdf", "báo cáo", "bao-cao")
            )
            if looks_like_report and href not in visited and len(queue) < MAX_PAGES * 5:
                queue.append(href)
            if TICKER_RE.search(combined) and any(
                word in combined.lower() for word in ("báo cáo", "bao-cao", "downloadedoc", ".pdf", "cập nhật", "khuyến nghị")
            ):
                candidates[href] = {"title": title or href.rsplit("/",1)[-1], "url": href, "page_url": final_url}
        # Some sites render reports through script data; retain a diagnostic marker for troubleshooting.
        if pages_read == 1:
            scripts = "\n".join(s.get_text(" ", strip=True) for s in soup.select("script"))
            api_markers = sorted(set(re.findall(r"""(?:https?://[^"' ]+|/[^"' ]*(?:api|search|report|document)[^"' ]*)""", scripts, re.I)))
            print(json.dumps({"event":"edocs_page_inspected","url":final_url,"title":soup.title.get_text(" ",strip=True) if soup.title else "",
                              "links":len(soup.select("a[href]")),"script_route_hints":api_markers[:25]}, ensure_ascii=False))
        time.sleep(0.15)


    # eDocuments renders much of its report list through AJAX. Crawl the public
    # paging routes advertised by its own JavaScript instead of guessing category URLs.
    ajax_routes = [
        ("/Home/Report_ReportAll_Paging", {"xml": "", "pageIndex": 1, "pageSize": 50, "type": ""}),
        ("/Home/Report_GetTopDownload_Paging", {"xml": "", "pageIndex": 1, "pageSize": 50, "type": ""}),
    ]
    home = get_page("https://edocs.vietstock.vn/")
    if home:
        hsoup = BeautifulSoup(home.text, "html.parser")
        script_urls = [urljoin(home.url, s.get("src", "")) for s in hsoup.select("script[src]")]
        for script_url in script_urls[:30]:
            if not allowed_url(script_url):
                continue
            sr = get_page(script_url)
            if not sr:
                continue
            js = sr.text
            for route in re.findall(r"""['"](/Home/(?:Report_[A-Za-z0-9_]+|DownloadReportPost))['"]""", js):
                if any(x in route for x in ("Report_ReportAll_Paging", "Report_GetTopDownload_Paging")):
                    continue
                if "Report_GetAllByStockCode_Paging" in route:
                    ajax_routes.append((route, {"xml": "", "pageIndex": 1, "pageSize": 50}))
                elif "ReportType_GetAll" in route:
                    ajax_routes.append((route, {}))
            if len(ajax_routes) > 12:
                break

    for route, params in ajax_routes:
        endpoint = urljoin("https://edocs.vietstock.vn/", route.lstrip("/"))
        try:
            response = SESSION.get(endpoint, params=params, headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://edocs.vietstock.vn/",
                "Accept": "application/json, text/html, */*",
            }, timeout=25)
            response.raise_for_status()
            body = response.text
            # AJAX payloads may be JSON containing an HTML fragment; parse both forms.
            fragments = [body]
            try:
                payload = response.json()
                fragments.extend(str(v) for v in payload.values() if isinstance(v, (str, list, dict)))
                if isinstance(payload, list):
                    fragments.extend(str(v) for v in payload)
            except Exception:
                pass
            found = 0
            for fragment in fragments:
                fsoup = BeautifulSoup(fragment, "html.parser")
                for a in fsoup.select("a[href]"):
                    href = clean_url(urljoin(response.url, a.get("href", "")))
                    title = re.sub(r"\\s+", " ", a.get_text(" ", strip=True)).strip()
                    combined = (title + " " + href + " " + fsoup.get_text(" ", strip=True)[:1200]).upper()
                    if allowed_url(href) and TICKER_RE.search(combined):
                        if any(x in (title + " " + href).lower() for x in ("download", "bao-cao", "report", ".pdf", "edoc", "cập nhật", "khuyến nghị")):
                            candidates[href] = {"title": title or href.rsplit("/", 1)[-1], "url": href, "page_url": response.url}
                            found += 1
                # Preserve candidate URLs embedded in JSON/text response.
                for href in re.findall(r"""https?://[^"'\\s<>]+|/[^"'\\s<>]+""", fragment):
                    href = clean_url(urljoin(response.url, href))
                    if allowed_url(href) and TICKER_RE.search(href.upper()) and any(x in href.lower() for x in ("downloadedoc", ".pdf", "report", "download")):
                        candidates[href] = {"title": href.rsplit("/", 1)[-1], "url": href, "page_url": response.url}
                        found += 1
            print(json.dumps({"event":"edocs_ajax_inspected","route":route,"status":response.status_code,"bytes":len(body),"tickerCandidates":found}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({"event":"edocs_ajax_failed","route":route,"error":str(exc)}, ensure_ascii=False))

    discovered = []
    for url, item in list(candidates.items()):
        # Open detail pages and extract direct PDF links when available.
        response = get_page(url)
        if not response:
            continue
        final_url = response.url
        direct_pdf = is_pdf_response(response)
        title = item["title"]
        publisher = ""
        report_date = ""
        if not direct_pdf:
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            if not TICKER_RE.search((title + " " + text).upper()):
                continue
            title = soup.title.get_text(" ",strip=True) if soup.title else title
            for a in soup.select("a[href]"):
                href = clean_url(urljoin(final_url, a.get("href","")))
                if allowed_url(href) and (".pdf" in href.lower() or "download" in href.lower() or "downloadedoc" in href.lower()):
                    item["pdf_url"] = href
                    break
            source_match = re.search(r"(?:Nguồn|Source)\s*[:：]\s*([A-Za-z0-9 .&_-]{2,80})", text, re.I)
            if source_match:
                publisher = source_match.group(1).strip()
            date_match = DATE_RE.search(text + " " + title)
            if date_match:
                y, m, d = date_match.groups()
                try:
                    report_date = datetime(int(y), int(m), int(d)).date().isoformat()
                except ValueError:
                    pass
        else:
            item["pdf_url"] = final_url
        pdf_url = item.get("pdf_url")
        if not pdf_url:
            # A detail URL can itself be a PDF-download endpoint; validate that exact URL.
            pdf_url = final_url if direct_pdf else ""
        if not pdf_url:
            continue
        check = validate_pdf(pdf_url)
        if not check.get("ok"):
            print(json.dumps({"event":"pdf_validation_failed","symbol":SYMBOL,"title":title,"url":pdf_url,"result":check},ensure_ascii=False))
            continue
        record = {
            "id": "vietstock-edocs-" + re.sub(r"[^a-z0-9]+","-", (SYMBOL + "-" + title).lower()).strip("-")[:90],
            "symbol": SYMBOL, "title": title, "publisher": publisher or "Vietstock eDocuments (nguồn phát hành cần xác minh)",
            "reportDate": report_date or None, "category": guess_category(title),
            "source": "Vietstock eDocuments", "landingUrl": final_url, "url": final_url,
            "downloadUrl": check["url"], "fileType": "application/pdf", "access": "public_link",
            "pdfValidation": {"status":"valid_pdf","pages":check["pages"],"bytes":check["bytes"],"checkedAt":NOW},
            "archived": False,
            "disclaimer": "Báo cáo phân tích của bên thứ ba; không phải báo cáo tài chính công bố chính thức. Chỉ lưu trữ hoặc phân phối lại PDF nếu quyền sử dụng cho phép."
        }
        discovered.append(record)
        print(json.dumps({"event":"valid_edocs_pdf","title":title,"landingUrl":final_url,"downloadUrl":check["url"],"pages":check["pages"],"bytes":check["bytes"]},ensure_ascii=False))
        # Intentionally no persistent PDF copy by default.
        if ALLOW_ARCHIVE:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            print("ALLOW_BROKER_PDF_ARCHIVE=true was set, but this worker still requires an explicit rights review before archiving.")

    for record in discovered:
        existing[record["url"]] = record
    catalog["updatedAt"] = NOW
    catalog["reports"] = sorted(existing.values(), key=lambda r:(r.get("symbol",""),r.get("reportDate") or "",r.get("title","")), reverse=False)
    catalog["crawl"] = {
        "source":"Vietstock eDocuments public pages",
        "testSymbol":SYMBOL,
        "pagesVisited":pages_read,
        "candidatesFound":len(candidates),
        "validPdfs":len(discovered),
        "runAt":NOW,
        "pdfArchivingEnabled":False,
        "note":"Crawler inspects public AJAX paging routes and validates direct PDF links; zero results may indicate changed endpoints or access restrictions."
    }
    for path in (OUT, DATA_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"event":"edocs_crawl_summary","symbol":SYMBOL,"pagesVisited":pages_read,
                      "candidatesFound":len(candidates),"validPdfs":len(discovered),
                      "catalog":str(DATA_OUT.relative_to(ROOT))},ensure_ascii=False))


if __name__ == "__main__":
    main()
