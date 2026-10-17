#!/usr/bin/env python3
"""Discover brokerage research separately from official issuer financial statements.

Research reports are catalogued with source links and never enter the financial
statement queue or verified financial data. The worker does not bypass logins,
CAPTCHAs, or access controls.
"""
from __future__ import annotations
import json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "analysis"
CATALOG = OUT / "analysis-reports.json"
DATA_CATALOG = ROOT / "data" / "analysis-reports.json"
SEC_PATH = ROOT / "config" / "securities.json"
NOW = datetime.now(timezone.utc).isoformat()
UA = "Mozilla/5.0 (compatible; solieutaichinh-research-catalog/1.1; public report index)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8"})
SYMBOLS_FALLBACK = ["MBB","ACB","FPT","SHB","TCX","HCM","VND","SHS","NLG","BSR","TCB","VHM"]
CATEGORIES = [
    ("stock_analysis", ["báo cáo phân tích", "phân tích cổ phiếu", "báo cáo cổ phiếu", "company report", "equity research", "cập nhật doanh nghiệp", "equity report"]),
    ("forecast_earnings", ["dự phóng", "dự báo", "ước tính kqkd", "forecast", "earning estimate", "outlook", "kết quả kinh doanh"]),
    ("recommendation_valuation", ["khuyến nghị", "giá mục tiêu", "định giá", "mua", "bán", "nắm giữ", "target price", "valuation", "khả quan", "tích lũy"]),
    ("industry_report", ["báo cáo ngành", "phân tích ngành", "industry report", "sector"]),
    ("market_strategy", ["chiến lược", "vĩ mô", "chiến lược thị trường", "market strategy", "macro", "market outlook"]),
]
# Public research landing pages and document CDNs used by Vietnamese brokerages/media.
ALLOWED_HOSTS = {
    "vietstock.vn", "www.vietstock.vn", "finance.vietstock.vn", "edocs.vietstock.vn", "static1.vietstock.vn",
    "cafef.vn", "www.cafef.vn", "cafefnew.mediacdn.vn",
    "vietcap.com.vn", "www.vietcap.com.vn",
    "shs.com.vn", "www.shs.com.vn",
    "dsc.com.vn", "www.dsc.com.vn",
    "new.bsc.com.vn", "bsc.com.vn", "www.bsc.com.vn",
    "acbs.com.vn", "www.acbs.com.vn",
    "mbs.com.vn", "www.mbs.com.vn",
    "fpts.com.vn", "www.fpts.com.vn",
    "hsc.com.vn", "www.hsc.com.vn",
    "vndirect.com.vn", "www.vndirect.com.vn",
    "ssi.com.vn", "www.ssi.com.vn",
    "kbsec.com.vn", "www.kbsec.com.vn",
    "yuanta.com.vn", "www.yuanta.com.vn",
    "masvn.com", "www.masvn.com",
    "vcbs.com.vn", "www.vcbs.com.vn",
    "fiintrade.vn", "www.fiintrade.vn",
}
BROKER_DOMAINS = [
    "vietcap.com.vn", "shs.com.vn", "dsc.com.vn", "new.bsc.com.vn",
    "acbs.com.vn", "mbs.com.vn", "fpts.com.vn", "hsc.com.vn",
    "vndirect.com.vn", "ssi.com.vn", "kbsec.com.vn", "yuanta.com.vn",
    "masvn.com", "vcbs.com.vn", "vietstock.vn", "cafef.vn",
]

def category_for(title):
    t = (title or "").casefold()
    for category, words in CATEGORIES:
        if any(word in t for word in words):
            return category
    return "brokerage_research"

def normalize_result_url(href):
    href = (href or "").strip()
    parsed = urlparse(href)
    if "duckduckgo.com" in (parsed.hostname or ""):
        href = parse_qs(parsed.query).get("uddg", [""])[0]
    return href

def search(query):
    # Try both DDG HTML endpoints; some runner IPs get an empty page from one endpoint.
    for endpoint, method in [
        ("https://html.duckduckgo.com/html/", "post"),
        ("https://html.duckduckgo.com/html/", "get"),
    ]:
        try:
            if method == "post":
                r = S.post(endpoint, data={"q": query}, timeout=20)
            else:
                r = S.get(endpoint, params={"q": query}, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            anchors = soup.select("a.result__a") or soup.select("a[data-testid='result-title-a']")
            items = []
            for a in anchors:
                href = normalize_result_url(a.get("href", ""))
                if not href.startswith(("http://", "https://")):
                    continue
                host = (urlparse(href).hostname or "").lower().removeprefix("www.")
                allowed = {x.removeprefix("www.") for x in ALLOWED_HOSTS}
                if not any(host == h or host.endswith("." + h) for h in allowed):
                    continue
                title = a.get_text(" ", strip=True)
                if not title or len(title) < 5:
                    continue
                items.append({
                    "title": title, "url": href, "host": host,
                    "category": category_for(title),
                    "source": host,
                    "access": "public_link",
                    "disclaimer": "Báo cáo phân tích của bên thứ ba; không phải BCTC công bố chính thức."
                })
            if items:
                return items
        except Exception:
            continue
    return []

def ticker_relevant(symbol, item):
    # Match ticker in title, URL, or query-visible slug; avoid false positives such as TCB in words.
    text = (item.get("title", "") + " " + item.get("url", "")).upper()
    return bool(re.search(rf"(?<![A-Z0-9]){re.escape(symbol)}(?![A-Z0-9])", text))


def main():
    securities = json.loads(SEC_PATH.read_text(encoding="utf-8")) if SEC_PATH.exists() else {}
    symbols = [str(x.get("symbol","")).upper() for x in securities.get("securities",[]) if x.get("enabled",True)]
    symbols = sorted(set(x for x in symbols if re.fullmatch(r"[A-Z0-9]{3,10}",x))) or SYMBOLS_FALLBACK
    existing = {}
    if CATALOG.exists():
        try:
            existing = {x.get("url"):x for x in json.loads(CATALOG.read_text(encoding="utf-8")).get("reports",[]) if x.get("url")}
        except Exception:
            existing = {}
    found = dict(existing)
    errors = []
    for symbol in symbols:
        # Search each source independently instead of requiring Vietstock-only results.
        queries = [
            f'"{symbol}" báo cáo phân tích cổ phiếu',
            f'"{symbol}" dự phóng khuyến nghị định giá',
            f'"{symbol}" site:cafef.vn/du-lieu/report',
            f'"{symbol}" site:vietcap.com.vn/trung-tam-phan-tich',
            f'"{symbol}" site:shs.com.vn/bao-cao-phan-tich',
            f'"{symbol}" site:dsc.com.vn/bao-cao-phan-tich',
            f'"{symbol}" site:new.bsc.com.vn/bao-cao-phan-tich',
        ]
        for q in queries:
            for item in search(q):
                if not ticker_relevant(symbol, item):
                    continue
                item["symbol"] = symbol
                item["discoveredAt"] = NOW
                found[item["url"]] = item
            time.sleep(0.35)
    reports = sorted(found.values(), key=lambda x:(x.get("symbol",""),x.get("category",""),x.get("title","")))
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion":1, "updatedAt":NOW,
        "description":"Danh mục riêng cho báo cáo phân tích/dự phóng của công ty chứng khoán. Không dùng số liệu dự báo làm số liệu thực tế; không trộn với báo cáo tài chính công bố chính thức.",
        "categories":[{"id":k,"label":label} for k,label in [
            ("stock_analysis","Báo cáo phân tích cổ phiếu"),
            ("forecast_earnings","Dự phóng kết quả kinh doanh"),
            ("recommendation_valuation","Khuyến nghị và định giá"),
            ("industry_report","Báo cáo phân tích ngành"),
            ("market_strategy","Chiến lược thị trường và vĩ mô"),
            ("brokerage_research","Báo cáo nghiên cứu khác")]],
        "reports":reports, "errors":errors[-30:],
        "policy":{"official_financial_statements":"reports/raw + config/report-queue.json",
                  "brokerage_research":"reports/analysis/analysis-reports.json",
                  "auto_publish_numbers":False}
    }
    serialized = json.dumps(payload,ensure_ascii=False,indent=2)+"\n"
    CATALOG.write_text(serialized,encoding="utf-8")
    DATA_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    DATA_CATALOG.write_text(serialized,encoding="utf-8")
    print(json.dumps({"symbols":len(symbols),"research_reports_catalogued":len(reports),"errors":len(errors),"catalog":str(CATALOG.relative_to(ROOT)),"website_snapshot":str(DATA_CATALOG.relative_to(ROOT))},ensure_ascii=False))

if __name__ == "__main__":
    main()
