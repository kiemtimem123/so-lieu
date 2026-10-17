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
UA = "solieutaichinh-research-catalog/1.0 (public report index)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept": "text/html,application/pdf,*/*;q=0.8"})
SYMBOLS_FALLBACK = ["MBB","ACB","FPT","SHB","TCX","HCM","VND","SHS","NLG","BSR","TCB","VHM"]
CATEGORIES = [
    ("stock_analysis", ["báo cáo phân tích", "phân tích cổ phiếu", "báo cáo cổ phiếu", "company report", "equity research"]),
    ("forecast_earnings", ["dự phóng", "dự báo", "ước tính kqkd", "forecast", "earning estimate", "outlook"]),
    ("recommendation_valuation", ["khuyến nghị", "giá mục tiêu", "định giá", "mua", "bán", "nắm giữ", "target price", "valuation"]),
    ("industry_report", ["báo cáo ngành", "phân tích ngành", "industry report", "sector"]),
    ("market_strategy", ["chiến lược", "vĩ mô", "chiến lược thị trường", "market strategy", "macro"]),
]

def category_for(title):
    t = (title or "").casefold()
    for category, words in CATEGORIES:
        if any(word in t for word in words):
            return category
    return "brokerage_research"

def search(query):
    try:
        r = S.post("https://html.duckduckgo.com/html/", data={"q":query}, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for a in soup.select("a.result__a"):
            href = a.get("href","")
            parsed = urlparse(href)
            if "duckduckgo.com" in (parsed.hostname or ""):
                href = parse_qs(parsed.query).get("uddg", [""])[0]
            if not href.startswith("http"):
                continue
            host = (urlparse(href).hostname or "").lower()
            # Keep only Vietstock's public research index and its public document CDN.
            if host not in {"edocs.vietstock.vn","www.vietstock.vn","vietstock.vn","finance.vietstock.vn","static1.vietstock.vn"}:
                continue
            title = a.get_text(" ",strip=True)
            if not title:
                continue
            items.append({"title":title,"url":href,"host":host,"category":category_for(title),
                          "source":"Vietstock eDocs / Vietstock Finance",
                          "access":"public_link","disclaimer":"Báo cáo phân tích của bên thứ ba; không phải BCTC công bố chính thức."})
        return items
    except Exception as e:
        return [{"query":query,"error":str(e)[:300]}]

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
        queries = [
            f'site:edocs.vietstock.vn "{symbol}" báo cáo phân tích OR dự phóng OR khuyến nghị',
            f'site:finance.vietstock.vn/downloadedoc "{symbol}" báo cáo cổ phiếu OR phân tích OR dự báo',
        ]
        for q in queries:
            for item in search(q):
                if "error" in item:
                    errors.append(item)
                    continue
                url = item["url"]
                # Keep ticker relevance conservative; source page must mention the ticker in title or URL.
                if not re.search(rf"(?<![A-Z0-9]){re.escape(symbol)}(?![A-Z0-9])", item["title"].upper()) and symbol.lower() not in url.lower():
                    continue
                item["symbol"] = symbol
                item["discoveredAt"] = NOW
                found[url] = item
            time.sleep(0.8)
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
