#!/usr/bin/env python3
"""Append newly published quarterly BCTC records from VietstockFinance.

Only uses the official VietstockFinance document catalog (doctype=1) and the
PDF/ZIP URLs returned by that catalog. Extracted numbers remain tagged as
automatic/text extraction until a person performs the final visual check.
"""
from __future__ import annotations

import html
import io
import json
import math
import re
import sys
import time
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_URL = "https://finance.vietstock.vn/"
API_URL = urljoin(BASE_URL, "data/getdocument")
SYMBOLS = ["MBB", "ACB", "FPT", "SHB", "TCX", "HCM", "VND", "SHS", "NLG", "BSR", "TCB", "VHM"]
DOC_TYPE = 1
MAX_PAGES_PER_YEAR = 20
MAX_DOWNLOAD_BYTES = 80 * 1024 * 1024
MAX_PDF_PAGES = 40
SLEEP_BETWEEN_CALLS = 0.18
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": BASE_URL,
    "Origin": "https://finance.vietstock.vn",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}
NUMBER_RE = re.compile(r"(?<![A-Za-z])\(?-?\d[\d.,]*\d?\)?")
PERIOD_RE = re.compile(
    r"\bquy\s*(iv|iii|ii|i|[1-4])\b.{0,16}?\b(20\d{2})\b",
    re.IGNORECASE,
)
SHORT_PERIOD_RE = re.compile(r"\bq\s*([1-4])\s*[/_.\- ]?\s*(20\d{2})\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(20\d{2})\b")
ROMAN_QUARTERS = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
ALLOWED_HOSTS = {"finance.vietstock.vn", "static2.vietstock.vn", "vietstock.vn", "www.vietstock.vn"}

ASSET_LABELS = ["tổng cộng tài sản", "total assets"]
LIABILITY_LABELS = ["tổng nợ phải trả", "tổng cộng nợ phải trả", "total liabilities", "nợ phải trả"]
EQUITY_LABELS = ["tổng vốn chủ sở hữu", "vốn chủ sở hữu", "total equity"]
SOURCE_TOTAL_LABELS = ["tổng cộng nguồn vốn", "tổng nợ phải trả và vốn chủ sở hữu", "total liabilities and equity"]
PRETAX_LABELS = [
    "lợi nhuận kế toán trước thuế",
    "tổng lợi nhuận kế toán trước thuế",
    "lợi nhuận trước thuế",
    "profit before tax",
]
NET_PROFIT_LABELS = [
    "lợi nhuận sau thuế thu nhập doanh nghiệp",
    "lợi nhuận sau thuế",
    "profit after tax",
]
PARENT_PROFIT_LABELS = [
    "lợi nhuận sau thuế của cổ đông công ty mẹ",
    "lợi nhuận sau thuế của cổ đông của công ty mẹ",
    "lợi nhuận thuộc về cổ đông công ty mẹ",
]
REVENUE_LABELS = [
    "doanh thu thuần về bán hàng và cung cấp dịch vụ",
    "doanh thu hoạt động",
    "thu nhập lãi thuần",
    "doanh thu thuần",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(value: object) -> str:
    value = html.unescape(str(value or "")).lower().replace("đ", "d")
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", value).strip()


def period_key(period: str) -> tuple[int, int]:
    match = re.fullmatch(r"(20\d{2})-Q([1-4])", period or "")
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def next_period(period: str) -> str:
    year, quarter = period_key(period)
    if not year:
        return "2024-Q1"
    if quarter == 4:
        return f"{year + 1}-Q1"
    return f"{year}-Q{quarter + 1}"


def safe_host(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host in ALLOWED_HOSTS or host.endswith(".vietstock.vn")
    except Exception:
        return False


def doc_title(record: dict) -> str:
    fields = [
        record.get("FullName"), record.get("Title"), record.get("Name"),
        record.get("FileName"), record.get("Url"), record.get("URL"),
    ]
    return " | ".join(str(x) for x in fields if x)


def doc_url(record: dict) -> str:
    value = (
        record.get("Url") or record.get("URL") or record.get("FileUrl")
        or record.get("DownloadUrl") or record.get("Link") or ""
    )
    value = html.unescape(str(value)).strip()
    value = urljoin(BASE_URL, value).replace(" ", "%20")
    if not safe_host(value):
        return ""
    return value


def document_period(record: dict) -> tuple[str | None, bool, bool]:
    """Return (YYYY-Qn, explicitly_quarterly, cumulative-period-fallback)."""
    title = norm(unquote(doc_title(record)))
    if "bao cao tai chinh" not in title and "bctc" not in title and "financial statement" not in title:
        return None, False, False

    # Explicit words/numbers in the title take precedence over API fields.
    match = PERIOD_RE.search(title)
    if match:
        q_token, year = match.groups()
        quarter = ROMAN_QUARTERS.get(q_token.lower(), int(q_token) if q_token.isdigit() else None)
        return (f"{year}-Q{quarter}", True, False) if quarter else (None, False, False)

    match = SHORT_PERIOD_RE.search(title)
    if match:
        quarter, year = int(match.group(1)), match.group(2)
        return f"{year}-Q{quarter}", True, False

    year_value = None
    for key in ("Year", "year", "ReportYear", "reportYear", "FiscalYear"):
        try:
            value = int(str(record.get(key, "")).strip())
            if 2000 <= value <= 2100:
                year_value = value
                break
        except (TypeError, ValueError):
            pass
    if year_value is None:
        matches = YEAR_RE.findall(title)
        if matches:
            year_value = int(matches[-1])
    if year_value is None:
        return None, False, False

    # Some companies use half-year/nine-month reviewed statements instead of
    # naming the report Q2/Q3. Those statements are still from the same BCTC
    # catalog; the parser must pass the balance equation before any values save.
    if re.search(r"\b(6 thang|sau thang|6t)\b", title):
        return f"{year_value}-Q2", False, True
    if re.search(r"\b(9 thang|chin thang|9t)\b", title):
        return f"{year_value}-Q3", False, True

    for key in ("Quarter", "quarter", "ReportQuarter", "reportQuarter", "FiscalQuarter"):
        try:
            quarter = int(str(record.get(key, "")).strip())
            if quarter in (1, 2, 3, 4):
                return f"{year_value}-Q{quarter}", True, False
        except (TypeError, ValueError):
            pass
    # Deliberately do not convert annual-only audited statements to Q4:
    # annual earnings cannot safely be treated as a standalone quarter.
    return None, False, False


def parse_publication_date(record: dict) -> str | None:
    for key in ("LastUpdate", "PublishedAt", "PublishDate", "PublicationDate", "Date", "UpdatedAt"):
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        epoch = re.fullmatch(r"/Date\((\d+)(?:[+-]\d{4})?\)/", text)
        if epoch:
            try:
                return datetime.fromtimestamp(int(epoch.group(1)) / 1000, tz=timezone.utc).date().isoformat()
            except (ValueError, OSError):
                pass
        match = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", text)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date().isoformat()
            except ValueError:
                pass
    return None


def get_anti_forgery_token(session: requests.Session) -> str:
    response = session.get(BASE_URL, timeout=(15, 30))
    response.raise_for_status()
    text = response.text
    # Attribute order varies on the minified ASP.NET page.
    value_pattern = r"""(?:"([^"]+)"|'([^']+)'|([^\s>]+))"""
    patterns = [
        rf'name=(?:"__RequestVerificationToken"|__RequestVerificationToken)[^>]*value={value_pattern}',
        rf'value={value_pattern}[^>]*name=(?:"__RequestVerificationToken"|__RequestVerificationToken)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            for group in match.groups():
                if group:
                    return group
    raise RuntimeError("Không lấy được token phiên từ trang chủ VietstockFinance; dừng để tránh lưu dữ liệu rỗng.")


def response_records(response: requests.Response) -> list[dict]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"VietstockFinance trả về nội dung không phải JSON (HTTP {response.status_code}).") from exc
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("Data", "data", "Items", "items", "aaData"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    raise RuntimeError("Không nhận diện được cấu trúc phản hồi danh mục BCTC VietstockFinance.")


def get_listing_page(
    session: requests.Session, token: str, symbol: str, year: int, page: int
) -> list[dict]:
    payload = {
        "code": symbol.upper(),
        "page": str(page),
        "year": str(year),
        "type": str(DOC_TYPE),
        "__RequestVerificationToken": token,
    }
    response = session.post(API_URL, data=payload, headers=HEADERS, timeout=(15, 40))
    response.raise_for_status()
    return response_records(response)


def fetch_symbol_documents(
    session: requests.Session, token: str, symbol: str, years: list[int]
) -> list[dict]:
    all_records: dict[str, dict] = {}
    for year in years:
        previous_page_signature = None
        for page in range(1, MAX_PAGES_PER_YEAR + 1):
            records = get_listing_page(session, token, symbol, year, page)
            if not records:
                break
            signature = tuple(
                str(r.get("FileInfoID") or r.get("ID") or r.get("Id") or r.get("Url") or r.get("FullName") or "")
                for r in records
            )
            if signature and signature == previous_page_signature:
                break
            previous_page_signature = signature
            for record in records:
                key = str(record.get("FileInfoID") or record.get("ID") or record.get("Id") or
                           record.get("Url") or record.get("FullName") or record.get("Title") or "")
                if key:
                    all_records[key] = record
            time.sleep(SLEEP_BETWEEN_CALLS)
        print(f"  {symbol} {year}: tìm thấy {len(all_records)} tài liệu tích lũy trong danh mục")
    return list(all_records.values())


def desired_consolidated(items: list[dict]) -> bool:
    labels = [norm(x.get("report_type", "")) for x in items if x.get("report_type")]
    if not labels:
        return True
    consolidated = sum("hop nhat" in label or "consolidated" in label for label in labels)
    separate = sum(
        any(word in label for word in ("rieng le", "cong ty me", "ctck"))
        and "hop nhat" not in label
        for label in labels
    )
    if consolidated == 0 and separate == 0:
        return True
    return consolidated >= separate


def candidate_score(record: dict, explicit: bool, cumulative: bool) -> tuple[int, int, int]:
    text = norm(unquote(doc_title(record) + " " + doc_url(record)))
    # Explicit Qn report first; use 6/9-month report only when necessary.
    quarter_penalty = 1 if cumulative else (0 if explicit else 2)
    # Soát xét/kiểm toán is preferred when available for the same quarter.
    review_penalty = 0 if ("soat xet" in text or "kiem toan" in text) else 1
    # A direct PDF is smaller/easier to parse than an archive, all else equal.
    file_url = urlparse(doc_url(record)).path.lower()
    archive_penalty = 1 if file_url.endswith(".zip") else 0
    return (quarter_penalty, review_penalty, archive_penalty)


def is_scope_match(record: dict, consolidated_wanted: bool) -> bool:
    text = norm(unquote(doc_title(record) + " " + doc_url(record)))
    has_consolidated = "hop nhat" in text or "consolidated" in text
    has_parent_only = "cong ty me" in text or "parent company" in text
    if consolidated_wanted:
        return has_consolidated
    # Do not let a separate-company record be silently replaced with a
    # consolidated report, or vice versa.
    return not has_consolidated and not has_parent_only


def number_value(token: str) -> float | None:
    token = token.strip().replace(" ", "")
    if not token:
        return None
    negative = token.startswith("(") or token.startswith("-")
    token = token.strip("()").lstrip("-")
    if not token or not re.search(r"\d", token):
        return None
    dots, commas = token.count("."), token.count(",")
    if dots and commas:
        last_dot, last_comma = token.rfind("."), token.rfind(",")
        decimal_mark = "." if last_dot > last_comma else ","
        grouping_mark = "," if decimal_mark == "." else "."
        token = token.replace(grouping_mark, "")
        token = token.replace(decimal_mark, ".")
    elif dots or commas:
        mark = "." if dots else ","
        groups = token.split(mark)
        if len(groups) > 1 and all(len(group) == 3 for group in groups[1:]):
            token = "".join(groups)
        else:
            token = mark.join(groups).replace(mark, ".")
    try:
        value = float(token)
        return -value if negative else value
    except ValueError:
        return None


def row_numbers(lines: list[str], labels: list[str], limit: int = 5) -> list[float]:
    normalized = [norm(line) for line in lines]
    for label in labels:
        term = norm(label)
        for index, clean_line in enumerate(normalized):
            start = clean_line.find(term)
            if start < 0:
                continue
            raw_line = lines[index]
            tail = raw_line[min(len(raw_line), start + len(term)):]
            values = []
            for match in NUMBER_RE.findall(tail):
                value = number_value(match)
                if value is not None and abs(value) >= 1000:
                    values.append(value)
            if values:
                return values[:limit]
            # Some PDFs put the label and numeric columns on adjacent lines.
            for lookahead in range(index + 1, min(index + 4, len(lines))):
                next_clean = normalized[lookahead]
                if re.search(r"[a-z]", next_clean):
                    break
                values = []
                for match in NUMBER_RE.findall(lines[lookahead]):
                    value = number_value(match)
                    if value is not None and abs(value) >= 1000:
                        values.append(value)
                if values:
                    return values[:limit]
    return []


def choose_balance_columns(
    assets_values: list[float], liability_values: list[float], equity_values: list[float]
) -> tuple[float, float, float] | None:
    best = None
    best_score = None
    for ai, assets in enumerate(assets_values[:5]):
        if assets <= 0:
            continue
        for li, liabilities in enumerate(liability_values[:5]):
            if liabilities < 0:
                continue
            for ei, equity in enumerate(equity_values[:5]):
                if equity < 0:
                    continue
                delta = abs(assets - liabilities - equity)
                tolerance = max(5.0, abs(assets) * 1e-8)
                if delta <= tolerance:
                    score = (ai + li + ei, delta, ai, li, ei)
                    if best_score is None or score < best_score:
                        best_score = score
                        best = (assets, liabilities, equity)
    return best


def scale_to_million(text: str, raw_assets: float, previous_assets_million: float | None) -> tuple[float, str]:
    header = norm(text[:25000])
    if "nghin dong" in header or "nghin vnd" in header or "thousand vnd" in header:
        return 1e-3, "nghìn VND → triệu VND"
    if "trieu dong" in header or "trieu vnd" in header or "million vnd" in header:
        return 1.0, "triệu VND"
    if "ty dong" in header or "ty vnd" in header or "billion vnd" in header:
        return 1e3, "tỷ VND → triệu VND"
    if re.search(r"don vi(?: tinh)?\s*[:\-]?\s*(?:vnd|dong)\b", header) or "đơn vị tính: đồng" in text[:25000].lower():
        return 1e-6, "VND → triệu VND"

    # Unknown unit: infer the scale from the previous quarter's assets, then
    # refuse extraction if no plausible conversion can be supported.
    if previous_assets_million and previous_assets_million > 0 and raw_assets > 0:
        choices = [1.0, 1e-3, 1e3, 1e-6]
        plausible = []
        for factor in choices:
            ratio = raw_assets * factor / previous_assets_million
            if 0.2 <= ratio <= 5.0:
                plausible.append((abs(math.log(ratio)), factor, ratio))
        if plausible:
            _, factor, ratio = min(plausible)
            return factor, f"đơn vị suy ra từ số dư quý trước; tỷ lệ tài sản={ratio:.4g}"
    raise ValueError("Không xác định chắc chắn đơn vị báo cáo.")


def extract_pdf_bytes(url: str, session: requests.Session) -> tuple[bytes, str]:
    if not safe_host(url):
        raise ValueError("Từ chối URL báo cáo ngoài miền Vietstock.")
    response = session.get(url, headers={"User-Agent": USER_AGENT, "Referer": BASE_URL}, timeout=(20, 90), stream=True)
    response.raise_for_status()
    final_url = response.url
    if not safe_host(final_url):
        raise ValueError("Tệp báo cáo chuyển hướng ra ngoài miền Vietstock.")
    body = bytearray()
    for chunk in response.iter_content(chunk_size=1024 * 128):
        if not chunk:
            continue
        body.extend(chunk)
        if len(body) > MAX_DOWNLOAD_BYTES:
            raise ValueError(f"Tệp vượt giới hạn xử lý {MAX_DOWNLOAD_BYTES // (1024 * 1024)} MB.")
    data = bytes(body)
    if data.startswith(b"%PDF"):
        return data, final_url
    if data.startswith(b"PK"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = sorted(
                (info for info in archive.infolist()
                 if info.filename.lower().endswith(".pdf") and not info.is_dir()),
                key=lambda info: info.file_size,
                reverse=True,
            )
            if not members:
                raise ValueError("ZIP Vietstock không chứa PDF.")
            info = members[0]
            if info.file_size > MAX_DOWNLOAD_BYTES:
                raise ValueError("PDF bên trong ZIP vượt giới hạn xử lý.")
            return archive.read(info), final_url
    raise ValueError(f"Liên kết không trả PDF/ZIP trực tiếp (Content-Type={response.headers.get('Content-Type', '')}).")


def extract_statement(pdf_bytes: bytes, previous_item: dict | None) -> dict:
    reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    texts = []
    for page in reader.pages[:MAX_PDF_PAGES]:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            texts.append("")
    text = "\n".join(texts)
    if len(text.strip()) < 300:
        raise ValueError("PDF không có đủ văn bản để trích xuất; cần OCR/kiểm tra trực quan.")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    asset_series = row_numbers(lines, ASSET_LABELS)
    liability_series = row_numbers(lines, LIABILITY_LABELS)
    equity_series = row_numbers(lines, EQUITY_LABELS)
    source_total_series = row_numbers(lines, SOURCE_TOTAL_LABELS)

    # Prefer three explicit subtotals whose first/current-period columns
    # satisfy the accounting equation. If one subtotal is unreadable, derive
    # it from the other two and record that derivation transparently.
    balances = choose_balance_columns(asset_series, liability_series, equity_series)
    derived_fields = []
    if balances is None and asset_series and liability_series and not equity_series:
        a, l = asset_series[0], liability_series[0]
        if a > l >= 0:
            balances = (a, l, a - l)
            derived_fields.append("equity_from_assets_minus_liabilities")
    if balances is None and asset_series and equity_series and not liability_series:
        a, e = asset_series[0], equity_series[0]
        if a > e >= 0:
            balances = (a, a - e, e)
            derived_fields.append("liabilities_from_assets_minus_equity")
    if balances is None and asset_series and source_total_series and liability_series:
        balances = choose_balance_columns(asset_series, liability_series, source_total_series)
        if balances:
            a, l, total_sources = balances
            balances = (a, l, total_sources - l)
            derived_fields.append("equity_from_total_sources_minus_liabilities")
    if balances is None:
        raise ValueError("Không tìm được ba dòng tài sản/nợ/vốn cùng một cột thỏa phương trình cân đối.")

    raw_assets, raw_liabilities, raw_equity = balances
    previous_assets = previous_item.get("total_assets") if previous_item else None
    factor, unit_note = scale_to_million(text, raw_assets, previous_assets)

    def million(value: float) -> int:
        return int(round(value * factor))

    total_assets = million(raw_assets)
    total_liabilities = million(raw_liabilities)
    equity = million(raw_equity)
    if total_assets <= 0 or total_liabilities < 0 or equity < 0:
        raise ValueError("Số dư tài sản/nợ/vốn không hợp lệ sau chuẩn hóa đơn vị.")
    if abs(total_assets - total_liabilities - equity) > 3:
        raise ValueError("Phương trình cân đối không khớp sau chuẩn hóa đơn vị.")

    pretax_series = row_numbers(lines, PRETAX_LABELS)
    net_profit_series = row_numbers(lines, NET_PROFIT_LABELS)
    if not pretax_series or not net_profit_series:
        raise ValueError("Không tìm đủ dòng lợi nhuận trước thuế và sau thuế.")
    pretax_profit = million(pretax_series[0])
    net_profit = million(net_profit_series[0])

    parent_profit_series = row_numbers(lines, PARENT_PROFIT_LABELS)
    revenue_series = row_numbers(lines, REVENUE_LABELS)
    net_profit_attributable = million(parent_profit_series[0]) if parent_profit_series else None
    revenue = million(revenue_series[0]) if revenue_series else None

    result = {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "equity": equity,
        "pretax_profit": pretax_profit,
        "net_profit": net_profit,
        "net_profit_attributable": net_profit_attributable,
        "revenue": revenue,
        "scale_factor_to_million": factor,
        "unit_note": unit_note,
        "derived_fields": derived_fields,
        "raw_values_report_units": {
            "total_assets": raw_assets,
            "total_liabilities": raw_liabilities,
            "equity": raw_equity,
            "pretax_profit": pretax_series[0],
            "net_profit": net_profit_series[0],
        },
    }
    return result


def choose_previous_item(items: list[dict], period: str) -> dict | None:
    previous_period = period
    key = period_key(previous_period)
    if not key[0]:
        return None
    if key[1] == 1:
        target = f"{key[0] - 1}-Q4"
    else:
        target = f"{key[0]}-Q{key[1] - 1}"
    return next((item for item in items if item.get("period") == target), None)


def make_placeholder(
    symbol: str, period: str, record: dict, source_url: str, cumulative: bool
) -> dict:
    title = doc_title(record)
    item = {
        "symbol": symbol,
        "period": period,
        "total_assets": None,
        "total_liabilities": None,
        "equity": None,
        "pretax_profit": None,
        "net_profit": None,
        "net_profit_attributable": None,
        "revenue": None,
        "roa": None,
        "roe": None,
        "unit": "triệu VND",
        "ratio_unit": "%/năm (tính từ lợi nhuận quý khi đủ dữ liệu bình quân đầu/cuối kỳ)",
        "source_url": source_url,
        "source_index_url": f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1",
        "report_type": f"BCTC {symbol} {period} (phát hiện tự động qua VietstockFinance; chờ trích xuất)",
        "source_pages": "Chưa trích xuất được đủ chỉ tiêu; xem PDF/ZIP trong đường dẫn VietstockFinance.",
        "quarter_profit_basis": (
            "Tài liệu 6/9 tháng: cần lấy cột phát sinh riêng trong quý, không dùng số lũy kế."
            if cumulative else
            "Chỉ lưu số liệu khi cột phát sinh riêng của quý được trích xuất và cân đối hợp lệ."
        ),
        "verification_status": "auto_pending_extraction",
        "source_validation": {
            "reviewed_at": utc_now(),
            "single_source_policy": "Chỉ danh mục VietstockFinance và tệp do danh mục đó liên kết.",
            "source_catalog_url": f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1",
            "source_document_url": source_url,
            "listing_title": title[:500],
            "document_id": str(record.get("FileInfoID") or record.get("ID") or record.get("Id") or "") or None,
            "manually_visual_reviewed": False,
        },
    }
    published = parse_publication_date(record)
    if published:
        item["published_at"] = published
    return item


def make_extracted_item(
    symbol: str, period: str, record: dict, source_url: str, values: dict,
    items: list[dict], cumulative: bool,
) -> dict:
    title = doc_title(record)
    previous = choose_previous_item(items, period)
    total_assets = values["total_assets"]
    total_liabilities = values["total_liabilities"]
    equity = values["equity"]
    net_profit = values["net_profit"]
    average_assets = None
    average_equity = None
    roa = None
    roe = None
    if previous and isinstance(previous.get("total_assets"), (int, float)) and isinstance(previous.get("equity"), (int, float)):
        average_assets = (previous["total_assets"] + total_assets) / 2
        average_equity = (previous["equity"] + equity) / 2
        if average_assets > 0:
            roa = round(net_profit / average_assets * 4 * 100, 2)
        if average_equity > 0:
            roe = round(net_profit / average_equity * 4 * 100, 2)

    item = {
        "symbol": symbol,
        "period": period,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "equity": equity,
        "pretax_profit": values["pretax_profit"],
        "net_profit": net_profit,
        "net_profit_attributable": values.get("net_profit_attributable"),
        "revenue": values.get("revenue"),
        "roa": roa,
        "roe": roe,
        "unit": "triệu VND",
        "ratio_unit": "%/năm (tính từ LNST quý / bình quân số dư đầu-cuối quý × 4)",
        "source_url": source_url,
        "source_index_url": f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1",
        "report_type": f"BCTC {symbol} {period} (tự trích xuất từ VietstockFinance; chờ rà soát trực quan)",
        "source_pages": "Tự trích xuất văn bản PDF/ZIP; số trang có thể khác giữa mẫu báo cáo.",
        "quarter_profit_basis": (
            "Tự trích xuất số phát sinh riêng quý từ báo cáo lũy kế; cần kiểm tra trực quan."
            if cumulative else
            "Tự trích xuất cột phát sinh riêng của quý; không dùng số lũy kế."
        ),
        "verification_status": "auto_extracted_pending_visual_review",
        "average_total_assets": average_assets,
        "average_equity": average_equity,
        "roa_formula": "LNST quý / bình quân tổng tài sản đầu và cuối quý × 4 × 100",
        "roe_formula": "LNST quý / bình quân vốn chủ sở hữu đầu và cuối quý × 4 × 100",
        "reconciliation": {
            "assets_minus_liabilities_equity": total_assets - total_liabilities - equity,
            "raw_values_vnd": {
                key: int(round(values["raw_values_report_units"][key] * values["scale_factor_to_million"] * 1_000_000))
                for key in ("total_assets", "total_liabilities", "equity", "pretax_profit", "net_profit")
            },
            "unit_note": values["unit_note"],
            "derived_fields": values["derived_fields"],
        },
        "source_extract_review": {
            "checked_at": utc_now(),
            "source_index_url": f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1",
            "source_report_url": source_url,
            "source_scope": "Chỉ PDF/ZIP do danh mục VietstockFinance của mã liên kết.",
            "method": "automatic PDF text extraction + accounting balance validation",
            "manually_visual_reviewed": False,
            "checks": {
                "balance_equation_difference_million_vnd": total_assets - total_liabilities - equity,
                "balance_equation_matches": abs(total_assets - total_liabilities - equity) <= 3,
                "unit_note": values["unit_note"],
                "cumulative_document": cumulative,
            },
            "note": "Các số tự trích xuất cần được kiểm tra trực quan trước khi đánh dấu đã xác minh thủ công.",
        },
    }
    published = parse_publication_date(record)
    if published:
        item["published_at"] = published
    if values.get("revenue") is None:
        item.pop("revenue", None)
    return item


def load_snapshot(symbol: str) -> tuple[dict, Path]:
    path = DATA_DIR / f"financials-{symbol}.json"
    if not path.exists():
        raise FileNotFoundError(f"Không có snapshot hiện tại: {path}")
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("symbol") != symbol or not isinstance(snapshot.get("items"), list):
        raise ValueError(f"Snapshot sai schema: {path}")
    snapshot["items"].sort(key=lambda x: period_key(x.get("period", "")))
    return snapshot, path


def process_symbol(
    session: requests.Session, token: str, symbol: str, current_year: int
) -> tuple[bool, int, int]:
    snapshot, path = load_snapshot(symbol)
    items = snapshot["items"]
    existing = {item.get("period"): item for item in items}
    latest = max((period_key(p) for p in existing if period_key(p)[0]), default=(2024, 1))
    years = list(range(max(2024, min(current_year, latest[0]) - 1), current_year + 1))
    records = fetch_symbol_documents(session, token, symbol, years)

    want_consolidated = desired_consolidated(items)
    candidates: dict[str, list[tuple[tuple[int, int, int], dict, bool]]] = {}
    for record in records:
        period, explicit, cumulative = document_period(record)
        if not period or period_key(period) < (2024, 1):
            continue
        url = doc_url(record)
        if not url:
            continue
        if not is_scope_match(record, want_consolidated):
            continue
        if period in existing and existing[period].get("verification_status") != "auto_pending_extraction":
            continue
        # Append only the immediate next quarter; skip gaps rather than make
        # a series look complete when Vietstock's listing has not returned a
        # previous quarter yet.
        next_expected = next_period(max(
            (item.get("period") for item in items if period_key(item.get("period", ""))[0]),
            key=period_key,
            default="2024-Q1",
        ))
        if period not in existing and period != next_expected:
            continue
        candidates.setdefault(period, []).append((candidate_score(record, explicit, cumulative), record, cumulative))

    changed = False
    added = 0
    filled = 0
    for period in sorted(candidates, key=period_key):
        options = sorted(candidates[period], key=lambda x: x[0])
        _, record, cumulative = options[0]
        url = doc_url(record)
        try:
            pdf_bytes, final_url = extract_pdf_bytes(url, session)
            previous = choose_previous_item(items, period)
            values = extract_statement(pdf_bytes, previous)
            new_item = make_extracted_item(symbol, period, record, url, values, items, cumulative)
            new_item["source_validation"]["final_download_url"] = final_url
            if period in existing:
                idx = next(i for i, item in enumerate(items) if item.get("period") == period)
                items[idx] = new_item
                existing[period] = new_item
                filled += 1
                print(f"  {symbol} {period}: đã trích xuất được kỳ đang chờ; giữ trạng thái cần rà soát trực quan.")
            else:
                items.append(new_item)
                existing[period] = new_item
                added += 1
                print(f"  {symbol} {period}: đã thêm số liệu tự trích xuất; cân đối khớp, cần rà soát trực quan.")
            changed = True
        except Exception as exc:
            print(f"  {symbol} {period}: chưa tự trích xuất đủ tin cậy: {exc}")
            if period in existing:
                # Keep the pending placeholder unchanged; try again next run
                # without generating a new commit every day.
                continue
            placeholder = make_placeholder(symbol, period, record, url, cumulative)
            items.append(placeholder)
            existing[period] = placeholder
            added += 1
            changed = True
            print(f"  {symbol} {period}: đã thêm liên kết nguồn và trạng thái chờ trích xuất; chưa điền số liệu.")
        items.sort(key=lambda x: period_key(x.get("period", "")))

    if changed:
        snapshot["items"] = items
        snapshot["sourceName"] = (
            f"VietstockFinance — báo cáo tài chính theo quý {symbol} "
            f"({items[0].get('period', '2024-Q1')} đến {items[-1].get('period', '')})"
        )
        snapshot["fetchedAt"] = utc_now()
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed, added, filled


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    print("Đồng bộ BCTC theo quý — chỉ danh mục VietstockFinance, doctype=1")
    token = get_anti_forgery_token(session)
    current_year = datetime.now(timezone.utc).year
    total_changed = total_added = total_filled = failed_symbols = 0
    for symbol in SYMBOLS:
        print(f"\n[{symbol}]")
        try:
            changed, added, filled = process_symbol(session, token, symbol, current_year)
            total_changed += int(changed)
            total_added += added
            total_filled += filled
        except Exception as exc:
            failed_symbols += 1
            print(f"  LỖI {symbol}: {exc}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN_CALLS)
    print("\nTóm tắt")
    print(f"- Mã: {len(SYMBOLS)}; lỗi truy vấn/đọc snapshot: {failed_symbols}")
    print(f"- Snapshot thay đổi: {total_changed}")
    print(f"- Kỳ mới được thêm (có thể đang chờ trích xuất): {total_added}")
    print(f"- Kỳ chờ trước đó đã điền được số liệu: {total_filled}")
    if failed_symbols == len(SYMBOLS):
        print("Tất cả mã đều lỗi; workflow sẽ báo thất bại để không coi đây là lần đồng bộ thành công.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
