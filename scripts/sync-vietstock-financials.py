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
import os
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
DEFAULT_SYMBOLS = ["MBB", "ACB", "FPT", "SHB", "TCX", "HCM", "VND", "SHS", "NLG", "BSR", "TCB", "VHM"]

def configured_symbols() -> list[str]:
    config_path = ROOT / "config" / "securities.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        configured = [
            str(item.get("symbol", "")).strip().upper()
            for item in payload.get("securities", [])
            if isinstance(item, dict) and item.get("enabled", True) and item.get("symbol")
        ]
        if configured:
            return list(dict.fromkeys(configured))
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return DEFAULT_SYMBOLS

SYMBOLS = configured_symbols()
BANKS = {"MBB", "ACB", "SHB", "TCB", "TPB", "VPB", "STB", "VCB", "CTG", "BID"}
BROKERS = {"TCX", "HCM", "VND", "SHS", "VCI", "VCK", "VIX", "SSI", "VDS"}

DOC_TYPE = 1
MAX_PAGES_PER_YEAR = 20
MAX_DOWNLOAD_BYTES = 80 * 1024 * 1024
MAX_PDF_PAGES = 40
MAX_OCR_PAGES = 20
OCR_DPI = 180
SLEEP_BETWEEN_CALLS = 0.18
MAX_EXTRACTION_ATTEMPTS = 3  # After three failed attempts, preserve the source and request manual review.
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

ASSET_LABELS = ["tổng cộng tài sản", "tổng tài sản", "total assets"]
LIABILITY_LABELS = [
    "tổng các khoản nợ phải trả", "tổng nợ phải trả", "tổng cộng nợ phải trả",
    "total liabilities", "nợ phải trả",
]
EQUITY_LABELS = ["tổng vốn chủ sở hữu", "vốn chủ sở hữu", "total equity"]
SOURCE_TOTAL_LABELS = [
    "tổng cộng nguồn vốn", "tổng nguồn vốn", "tổng nợ phải trả và vốn chủ sở hữu",
    "total liabilities and equity", "total sources",
]
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
    if consolidated > 0 or separate > 0:
        return consolidated >= separate
    # If Vietstock's labels do not say "hợp nhất", preserve the scope already
    # represented by the existing source URLs rather than forcing consolidated.
    return any("hopnhat" in norm(x.get("source_url", "")) for x in items)


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


def row_numbers(lines: list[str], labels: list[str], limit: int = 5, min_abs: int = 1000) -> list[float]:
    normalized = [norm(line) for line in lines]
    for label in labels:
        term = norm(label)
        for index, clean_line in enumerate(normalized):
            start = clean_line.find(term)
            if start < 0:
                continue
            suffix = clean_line[start + len(term):start + len(term) + 36]
            if term in {"tổng cộng tài sản", "tổng tài sản"} and any(word in suffix for word in ("ngan han", "dai han")):
                continue
            if term == "nợ phải trả" and any(word in suffix for word in ("ngan han", "dai han")):
                continue
            if "von chu so huu" in suffix and ("no phai tra" in term or "liabilities" in term):
                # "Total liabilities and equity" is a source-of-funds total, not liabilities.
                continue
            if term == "vốn chủ sở hữu" and "khac" in suffix:
                continue
            raw_line = lines[index]
            tail = raw_line[min(len(raw_line), start + len(term)):]
            values = []
            for match in NUMBER_RE.findall(tail):
                value = number_value(match)
                if value is not None and abs(value) >= min_abs:
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
                    if value is not None and abs(value) >= min_abs:
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


def ocr_pdf_text(pdf_bytes: bytes) -> str:
    """OCR scanned PDFs locally in the GitHub runner; never calls another data source."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu gói OCR (pdf2image/pytesseract); báo cáo được giữ dạng chờ trích xuất."
        ) from exc

    reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    page_count = min(len(reader.pages), MAX_OCR_PAGES)
    if page_count < 1:
        raise ValueError("PDF không có trang để OCR.")
    images = convert_from_bytes(
        pdf_bytes,
        dpi=OCR_DPI,
        first_page=1,
        last_page=page_count,
        fmt="png",
        thread_count=1,
    )
    chunks = []
    for page_number, image in enumerate(images, start=1):
        try:
            extracted = pytesseract.image_to_string(
                image, lang="vie+eng", config="--oem 1 --psm 6"
            )
        except Exception:
            # PSM 4 can work better for tables with separate text blocks.
            extracted = pytesseract.image_to_string(
                image, lang="vie+eng", config="--oem 1 --psm 4"
            )
        chunks.append(f"\n[OCR PAGE {page_number}]\n{extracted or ''}")
    return "\n".join(chunks)


def extract_statement(
    pdf_bytes: bytes,
    previous_item: dict | None,
    symbol: str = "",
    cumulative: bool = False,
    force_ocr: bool = False,
) -> dict:
    reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    texts = []
    if not force_ocr:
        for page in reader.pages[:MAX_PDF_PAGES]:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
    text = "\n".join(texts)
    if force_ocr or len(text.strip()) < 300:
        print("    Văn bản PDF thiếu; thử OCR các trang đầu bằng Tesseract.")
        text = ocr_pdf_text(pdf_bytes)
    if len(text.strip()) < 300:
        raise ValueError("PDF không có đủ văn bản sau thử OCR; giữ liên kết chờ xử lý.")
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
    # Some bank statement layouts show "total assets" and "total liabilities
    # and equity" as matching totals, without a separately extractable equity row.
    # Match the two totals first, then derive equity from the reported liabilities.
    if balances is None and asset_series and source_total_series and liability_series:
        candidates = []
        for ai, assets in enumerate(asset_series[:5]):
            if assets <= 0:
                continue
            for si, total_sources in enumerate(source_total_series[:5]):
                match_delta = abs(assets - total_sources)
                if match_delta > max(5.0, abs(assets) * 1e-8):
                    continue
                for li, liabilities in enumerate(liability_series[:5]):
                    equity = assets - liabilities
                    if liabilities < 0 or equity < 0:
                        continue
                    candidates.append(((ai + si + li, match_delta), assets, liabilities, equity))
        if candidates:
            _, assets, liabilities, equity = min(candidates, key=lambda x: x[0])
            balances = (assets, liabilities, equity)
            derived_fields.append("equity_from_matched_assets_and_total_sources_minus_liabilities")
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
    if symbol in BANKS and equity <= 0:
        raise ValueError("Vốn chủ sở hữu ngân hàng bằng hoặc nhỏ hơn 0; nhiều khả năng OCR bắt nhầm dòng tổng nguồn vốn.")

    pretax_series = row_numbers(lines, PRETAX_LABELS)
    net_profit_series = row_numbers(lines, NET_PROFIT_LABELS)
    if not pretax_series or not net_profit_series:
        raise ValueError("Không tìm đủ dòng lợi nhuận trước thuế và sau thuế.")
    if cumulative and (len(pretax_series) < 3 or len(net_profit_series) < 3):
        raise ValueError(
            "Báo cáo 6/9 tháng không có đủ cột để xác nhận số quý riêng; "
            "không lấy số lũy kế làm lợi nhuận quý."
        )
    pretax_profit = million(pretax_series[0])
    net_profit = million(net_profit_series[0])
    # Reject obvious OCR/column-selection errors before a number reaches charts.
    # Quarterly net profit normally reconciles below pretax profit; extreme
    # inversions are left as source-linked placeholders for later retries.
    if pretax_profit > 0 and net_profit > pretax_profit * 1.5:
        raise ValueError("LNST vượt quá 1,5 lần LNTT; nghi ngờ OCR lệch cột hoặc nhận nhầm dòng.")
    if pretax_profit > 0 and net_profit < -pretax_profit * 0.5:
        raise ValueError("LNST âm lớn trong khi LNTT dương; nghi ngờ OCR lệch cột hoặc nhận nhầm dòng.")
    if total_assets > 0 and abs(net_profit) > total_assets * 0.25:
        raise ValueError("LNST vượt quá 25% tổng tài sản; nghi ngờ OCR lệch đơn vị hoặc cột.")

    parent_profit_series = row_numbers(lines, PARENT_PROFIT_LABELS)
    revenue_series = row_numbers(lines, REVENUE_LABELS)
    net_profit_attributable = million(parent_profit_series[0]) if parent_profit_series else None
    if symbol in BANKS:
        revenue_labels = ["tổng thu nhập hoạt động", "total operating income", "doanh thu hoạt động", "thu nhập lãi thuần"]
    elif symbol in BROKERS:
        revenue_labels = ["doanh thu hoạt động", "doanh thu thuần", "operating revenue"]
    else:
        revenue_labels = REVENUE_LABELS
    revenue_series = row_numbers(lines, revenue_labels)
    revenue = million(revenue_series[0]) if revenue_series else None

    balance_detail_labels = {
        "current_assets": ["tài sản ngắn hạn", "current assets"],
        "cash_and_equivalents": ["tiền và các khoản tương đương tiền", "tiền và tương đương tiền", "cash and cash equivalents"],
        "short_term_investments": ["đầu tư tài chính ngắn hạn", "short-term financial investments"],
        "short_term_receivables": ["các khoản phải thu ngắn hạn", "short-term receivables"],
        "inventory": ["hàng tồn kho", "inventories"],
        "non_current_assets": ["tài sản dài hạn", "non-current assets"],
        "fixed_assets": ["tài sản cố định", "fixed assets"],
        "current_liabilities": ["nợ phải trả ngắn hạn", "nợ ngắn hạn", "current liabilities"],
        "long_term_liabilities": ["nợ phải trả dài hạn", "nợ dài hạn", "long-term liabilities"],
        "retained_earnings": ["lợi nhuận sau thuế chưa phân phối", "lợi nhuận chưa phân phối", "retained earnings"],
    }
    income_detail_labels = {
        "cost_of_goods_sold": ["giá vốn hàng bán", "cost of goods sold"],
        "gross_profit": ["lợi nhuận gộp về bán hàng và cung cấp dịch vụ", "lợi nhuận gộp", "gross profit"],
        "financial_income": ["doanh thu hoạt động tài chính", "doanh thu tài chính", "financial income"],
        "financial_expense": ["chi phí tài chính", "financial expenses"],
        "interest_expense": ["chi phí lãi vay", "chi phí đi vay", "chi phí lãi và các khoản chi phí tương tự", "interest expense"],
        "selling_expense": ["chi phí bán hàng", "selling expenses"],
        "admin_expense": ["chi phí quản lý doanh nghiệp", "chi phí quản lý", "administrative expenses"],
        "operating_profit": ["lợi nhuận thuần từ hoạt động kinh doanh", "lợi nhuận từ hoạt động kinh doanh", "operating profit"],
        "income_tax_current": ["chi phí thuế tndn hiện hành", "chi phí thuế thu nhập doanh nghiệp hiện hành", "current corporate income tax expense"],
        "income_tax_deferred": ["chi phí thuế tndn hoãn lại", "chi phí thuế thu nhập doanh nghiệp hoãn lại", "deferred corporate income tax expense"],
    }
    cashflow_detail_labels = {
        "operating_cash_flow_ytd": ["lưu chuyển tiền thuần từ hoạt động kinh doanh", "lưu chuyển tiền từ hoạt động kinh doanh", "net cash from operating activities"],
        "investing_cash_flow_ytd": ["lưu chuyển tiền thuần từ hoạt động đầu tư", "lưu chuyển tiền từ hoạt động đầu tư", "net cash from investing activities"],
        "financing_cash_flow_ytd": ["lưu chuyển tiền thuần từ hoạt động tài chính", "lưu chuyển tiền từ hoạt động tài chính", "net cash from financing activities"],
        "capital_expenditure_ytd": ["tiền chi để mua sắm, xây dựng tài sản cố định", "tiền chi mua sắm xây dựng tài sản cố định", "purchase of fixed assets"],
        "dividends_paid_ytd": ["cổ tức, lợi nhuận đã trả cho chủ sở hữu", "cổ tức lợi nhuận đã trả cho chủ sở hữu", "dividends paid"],
        "net_cash_change_ytd": ["lưu chuyển tiền thuần trong kỳ", "lưu chuyển tiền thuần trong năm", "net change in cash"],
        "cash_beginning": ["tiền và các khoản tương đương tiền đầu kỳ", "tiền và tương đương tiền đầu kỳ", "cash and cash equivalents at beginning"],
        "cash_ending": ["tiền và các khoản tương đương tiền cuối kỳ", "tiền và tương đương tiền cuối kỳ", "cash and cash equivalents at end"],
        "foreign_exchange_effect_ytd": ["ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ", "ảnh hưởng thay đổi tỷ giá hối đoái", "effect of exchange rate changes"],
    }
    details: dict[str, object] = {}
    for field, labels in balance_detail_labels.items():
        series = row_numbers(lines, labels)
        if series:
            details[field] = million(series[0])
    for field, labels in income_detail_labels.items():
        series = row_numbers(lines, labels)
        if series:
            details[field] = million(series[0])

    if symbol in BANKS:
        bank_balance_labels = {
            "bank_cash_on_hand": ["tiền mặt, vàng bạc, đá quý", "cash on hand, gold, silver and gems"],
            "bank_deposits_at_state_bank": ["tiền gửi tại nhnn", "tiền gửi tại ngân hàng nhà nước"],
            "bank_deposits_and_loans_to_credit_institutions": ["tiền gửi và cho vay các tctd khác", "tiền gửi và cho vay các tổ chức tín dụng khác"],
            "bank_customer_loans": ["cho vay khách hàng", "loans to customers"],
            "bank_trading_securities": ["chứng khoán kinh doanh", "trading securities"],
            "bank_derivatives_and_other_financial_assets": ["các công cụ tài chính phái sinh và các tài sản tài chính khác"],
            "bank_investment_securities": ["chứng khoán đầu tư", "investment securities"],
            "bank_contributions_and_long_term_investments": ["góp vốn, đầu tư dài hạn", "góp vốn đầu tư dài hạn"],
            "bank_other_assets": ["tài sản có khác", "other assets"],
            "bank_deposits_and_borrowings_from_credit_institutions": ["tiền gửi và vay các tctd khác", "tiền gửi và vay các tổ chức tín dụng khác"],
            "bank_customer_deposits": ["tiền gửi của khách hàng", "customer deposits"],
            "bank_valuable_papers": ["phát hành giấy tờ có giá", "valuable papers issued"],
            "bank_funding_and_trust_liabilities": ["vốn tài trợ, ủy thác đầu tư", "funding and trust liabilities"],
            "bank_other_liabilities": ["nợ khác", "other liabilities"],
        }
        bank_income_labels = {
            "bank_interest_income": ["thu nhập lãi và các khoản thu nhập tương tự"],
            "bank_interest_expense": ["chi phí lãi và các khoản chi phí tương tự"],
            "bank_net_interest_income": ["thu nhập lãi thuần"],
            "bank_service_income": ["thu nhập từ hoạt động dịch vụ"],
            "bank_service_expense": ["chi phí hoạt động dịch vụ"],
            "bank_net_service_income": ["lãi thuần từ hoạt động dịch vụ"],
            "bank_fx_net_income": ["lãi thuần từ hoạt động kinh doanh ngoại hối"],
            "bank_trading_securities_net": ["lãi thuần từ mua bán chứng khoán kinh doanh"],
            "bank_investment_securities_net": ["lãi thuần từ mua bán chứng khoán đầu tư", "lãi thuần từ mua bán chứng khoán đầu tư và góp vốn đầu tư dài hạn"],
            "bank_other_operating_net": ["lãi thuần từ hoạt động kinh doanh khác"],
            "bank_dividend_and_capital_income": ["thu nhập từ góp vốn, mua cổ phần"],
            "bank_operating_expenses": ["tổng chi phí hoạt động"],
            "bank_pre_provision_operating_profit": ["lợi nhuận thuần từ hoạt động kinh doanh trước chi phí dự phòng rủi ro"],
            "bank_provision_expense": ["chi phí dự phòng rủi ro"],
            "bank_non_controlling_profit": ["lợi ích của cổ đông không kiểm soát"],
        }
        for field, labels in bank_balance_labels.items():
            series = row_numbers(lines, labels)
            if series:
                details[field] = million(series[0])
        for field, labels in bank_income_labels.items():
            series = row_numbers(lines, labels)
            if series:
                details[field] = million(series[0])

    if symbol in BROKERS:
        broker_balance_labels = {
            "broker_fvtpl_assets": ["tài sản tài chính ghi nhận thông qua lãi/lỗ", "tài sản tài chính ghi nhận thông qua lãi lỗ"],
            "broker_held_to_maturity_assets": ["các khoản đầu tư nắm giữ đến ngày đáo hạn"],
            "broker_lending_assets": ["các khoản cho vay"],
            "broker_afs_assets": ["tài sản tài chính sẵn sàng để bán"],
            "broker_receivables": ["các khoản phải thu"],
            "broker_short_term_borrowings": ["vay và nợ thuê tài chính ngắn hạn", "vay ngắn hạn"],
            "broker_short_term_bonds": ["trái phiếu phát hành ngắn hạn"],
            "broker_long_term_bonds": ["trái phiếu phát hành dài hạn"],
            "broker_customer_deposits": ["tiền gửi của khách hàng"],
        }
        broker_income_labels = {
            "broker_fvtpl_gain": ["lãi/(lỗ) từ các tài sản tài chính ghi nhận thông qua lãi/lỗ", "lãi từ các tài sản tài chính ghi nhận thông qua lãi/lỗ"],
            "broker_held_to_maturity_income": ["lãi từ các khoản đầu tư nắm giữ đến ngày đáo hạn"],
            "broker_lending_income": ["lãi từ các khoản cho vay và phải thu", "thu nhập từ các khoản cho vay"],
            "broker_afs_income": ["lãi từ tài sản tài chính sẵn sàng để bán"],
            "broker_brokerage_revenue": ["doanh thu nghiệp vụ môi giới chứng khoán"],
            "broker_underwriting_revenue": ["doanh thu nghiệp vụ bảo lãnh, đại lý phát hành chứng khoán"],
            "broker_advisory_revenue": ["doanh thu nghiệp vụ tư vấn đầu tư chứng khoán"],
            "broker_custody_revenue": ["doanh thu nghiệp vụ lưu ký chứng khoán"],
            "broker_financial_advisory_revenue": ["doanh thu hoạt động tư vấn tài chính"],
            "broker_other_operating_income": ["thu nhập từ hoạt động khác"],
            "broker_operating_expenses": ["chi phí hoạt động"],
            "broker_admin_expenses": ["chi phí quản lý công ty chứng khoán", "chi phí quản lý doanh nghiệp"],
            "broker_net_operating_profit": ["lợi nhuận thuần từ hoạt động kinh doanh"],
        }
        for field, labels in broker_balance_labels.items():
            series = row_numbers(lines, labels)
            if series:
                details[field] = million(series[0])
        for field, labels in broker_income_labels.items():
            series = row_numbers(lines, labels)
            if series:
                details[field] = million(series[0])

    if "income_tax_current" in details or "income_tax_deferred" in details:
        details["income_tax"] = int(round(details.get("income_tax_current", 0) + details.get("income_tax_deferred", 0)))

    # Bank statements present total operating income rather than industrial net sales.
    if symbol in BANKS:
        eps = None
        revenue_labels = ["tổng thu nhập hoạt động", "total operating income", "doanh thu hoạt động", "thu nhập lãi thuần"]
    elif symbol in BROKERS:
        revenue_labels = ["doanh thu hoạt động", "doanh thu thuần", "operating revenue"]
    else:
        revenue_labels = REVENUE_LABELS
    selected_revenue = row_numbers(lines, revenue_labels)
    if selected_revenue:
        revenue = million(selected_revenue[0])
        details["revenue"] = revenue

    # EPS is reported in VND per share, so it must not be converted to million VND.
    basic_eps = row_numbers(lines, ["lãi cơ bản trên cổ phiếu", "lãi cơ bản trên một cổ phiếu", "basic earnings per share"], min_abs=100)
    diluted_eps = row_numbers(lines, ["lãi suy giảm trên cổ phiếu", "lãi suy giảm trên một cổ phiếu", "diluted earnings per share"], min_abs=100)
    if basic_eps:
        details["eps"] = int(round(basic_eps[0]))
    if diluted_eps:
        details["diluted_eps"] = int(round(diluted_eps[0]))

    for field, labels in cashflow_detail_labels.items():
        series = row_numbers(lines, labels)
        if series:
            details[field] = million(series[0])
    normalized_text = norm(text)
    if (
        re.search(r"\b01\s*/\s*01\s*/?\s*20\d{2}\b", normalized_text)
        or "tu ngay 01 thang 01" in normalized_text
        or "giai doan tu 01/01" in normalized_text
    ):
        details["cashflow_period_basis"] = "year_to_date"
    elif cashflow_detail_labels:
        details["cashflow_period_basis"] = "quarterly_reported"

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
    result.update(details)
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
        "report_type": f"BCTC hợp nhất {symbol} {period} (phát hiện tự động qua VietstockFinance; chờ trích xuất)",
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
        "report_type": f"BCTC hợp nhất {symbol} {period} (tự trích xuất từ VietstockFinance; chờ rà soát trực quan)",
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
    detailed_keys = {
        "current_assets", "cash_and_equivalents", "short_term_investments", "short_term_receivables",
        "inventory", "non_current_assets", "fixed_assets", "current_liabilities", "long_term_liabilities",
        "retained_earnings", "cost_of_goods_sold", "gross_profit", "financial_income", "financial_expense",
        "interest_expense", "selling_expense", "admin_expense", "operating_profit", "income_tax",
        "income_tax_current", "income_tax_deferred", "eps", "diluted_eps", "operating_cash_flow_ytd",
        "investing_cash_flow_ytd", "financing_cash_flow_ytd", "capital_expenditure_ytd", "dividends_paid_ytd",
        "net_cash_change_ytd", "cash_beginning", "cash_ending", "foreign_exchange_effect_ytd",
        "bank_cash_on_hand", "bank_deposits_at_state_bank", "bank_deposits_and_loans_to_credit_institutions",
        "bank_customer_loans", "bank_trading_securities", "bank_derivatives_and_other_financial_assets",
        "bank_investment_securities", "bank_contributions_and_long_term_investments", "bank_other_assets",
        "bank_deposits_and_borrowings_from_credit_institutions", "bank_customer_deposits", "bank_valuable_papers",
        "bank_funding_and_trust_liabilities", "bank_other_liabilities", "bank_interest_income", "bank_interest_expense",
        "bank_net_interest_income", "bank_service_income", "bank_service_expense", "bank_net_service_income",
        "bank_fx_net_income", "bank_trading_securities_net", "bank_investment_securities_net",
        "bank_other_operating_net", "bank_dividend_and_capital_income", "bank_operating_expenses",
        "bank_pre_provision_operating_profit", "bank_provision_expense", "bank_non_controlling_profit",
        "broker_fvtpl_assets", "broker_held_to_maturity_assets", "broker_lending_assets", "broker_afs_assets",
        "broker_receivables", "broker_short_term_borrowings", "broker_short_term_bonds", "broker_long_term_bonds",
        "broker_customer_deposits", "broker_fvtpl_gain", "broker_held_to_maturity_income", "broker_lending_income",
        "broker_afs_income", "broker_brokerage_revenue", "broker_underwriting_revenue", "broker_advisory_revenue",
        "broker_custody_revenue", "broker_financial_advisory_revenue", "broker_other_operating_income",
        "broker_operating_expenses", "broker_admin_expenses", "broker_net_operating_profit"
    }
    extracted_fields = []
    for field in detailed_keys:
        if values.get(field) is not None:
            item[field] = values[field]
            extracted_fields.append(field)
    if values.get("cashflow_period_basis"):
        item["cashflow_period_basis"] = values["cashflow_period_basis"]
        extracted_fields.append("cashflow_period_basis")
    if values.get("revenue") is not None:
        extracted_fields.append("revenue")
    if values.get("net_profit_attributable") is not None:
        extracted_fields.append("net_profit_attributable")
    if extracted_fields:
        item["financial_line_items_status"] = "auto_extracted_pending_visual_review"
        item["financial_line_items_extracted_fields"] = sorted(set(extracted_fields))
        item["financial_line_items_source"] = source_url
        item["financial_line_items_updated_at"] = utc_now()
        item["financial_line_items_note"] = "Chỉ tiêu chi tiết trích xuất tự động từ PDF VietstockFinance; cần đối chiếu trực quan."
    published = parse_publication_date(record)
    if published:
        item["published_at"] = published
    if values.get("revenue") is None:
        item.pop("revenue", None)
    return item


def load_snapshot(symbol: str) -> tuple[dict, Path]:
    path = DATA_DIR / f"financials-{symbol}.json"
    if not path.exists():
        snapshot = {
            "symbol": symbol,
            "sourceName": f"VietstockFinance — báo cáo tài chính theo quý {symbol}",
            "fetchedAt": utc_now(),
            "items": [],
        }
        return snapshot, path
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("symbol") != symbol or not isinstance(snapshot.get("items"), list):
        raise ValueError(f"Snapshot sai schema: {path}")
    snapshot["items"].sort(key=lambda x: period_key(x.get("period", "")))
    return snapshot, path


def process_symbol(
    session: requests.Session, token: str, symbol: str, current_year: int,
    max_extract_periods: int | None = None,
) -> tuple[bool, int, int]:
    path = DATA_DIR / f"financials-{symbol}.json"
    snapshot_was_missing = not path.exists()
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
        if period in existing:
            existing_item = existing[period]
            core_pending = existing_item.get("verification_status") == "auto_pending_extraction"
            core_present = existing_item.get("total_assets") is not None and existing_item.get("net_profit") is not None
            details_pending = core_present and not existing_item.get("financial_line_items_status")
            if not core_pending and not details_pending:
                continue
        candidates.setdefault(period, []).append((candidate_score(record, explicit, cumulative), record, cumulative))

    # Keep existing pending reports eligible for another extraction attempt.
    # For new periods, accept only a contiguous sequence from the first missing quarter.
    contiguous = {}
    if not existing and candidates:
        # Newly listed tickers may have no pre-IPO reports in the catalog.
        # Start at their earliest available consolidated quarter rather than
        # discarding all later reports because Q1/2024 is absent.
        expected = min(candidates, key=period_key)
    else:
        expected = "2024-Q1"
        while expected in existing:
            expected = next_period(expected)
    for period in sorted(candidates, key=period_key):
        if period in existing:
            contiguous[period] = candidates[period]
            continue
        while expected in existing or expected in contiguous:
            expected = next_period(expected)
        if period == expected:
            contiguous[period] = candidates[period]
            expected = next_period(period)
        elif period_key(period) > period_key(expected):
            print(f"  Dừng ở {period}: còn thiếu kỳ trước {expected}; không tạo chuỗi có khoảng trống.")
            break
    candidates = contiguous

    changed = snapshot_was_missing
    added = 0
    filled = 0
    ordered_periods = sorted(candidates, key=period_key)
    processing_periods = ordered_periods
    if max_extract_periods is not None:
        cooldown_seconds = 30 * 60
        now_epoch = datetime.now(timezone.utc).timestamp()

        def extraction_attempt_age(period: str) -> float | None:
            existing_item = existing.get(period) or {}
            validation = existing_item.get("source_validation") or {}
            if existing_item.get("verification_status") == "auto_pending_extraction":
                attempted_at = validation.get("last_extraction_attempt_at")
            else:
                attempted_at = existing_item.get("financial_line_items_last_attempt_at")
            if not attempted_at:
                return None
            try:
                return now_epoch - datetime.fromisoformat(str(attempted_at).replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError, OSError):
                return None

        # Prefer never-tried or cooldown-expired placeholders, and rotate through
        # periods instead of retrying the same unparseable quarter on every run.
        eligible_periods = [
            period for period in ordered_periods
            if period not in existing
            or extraction_attempt_age(period) is None
            or extraction_attempt_age(period) >= cooldown_seconds
        ]

        def extraction_attempt_count(period: str) -> int:
            existing_item = existing.get(period) or {}
            validation = existing_item.get("source_validation") or {}
            try:
                if existing_item.get("verification_status") == "auto_pending_extraction":
                    return int(validation.get("extraction_attempt_count") or 0)
                return int(existing_item.get("financial_line_items_attempt_count") or 0)
            except (TypeError, ValueError):
                return 0

        def extraction_priority(period: str) -> tuple[int, int, tuple[int, int]]:
            # Visit every unattempted period first. After the first pass, retry
            # lower-attempt-count periods first so one unreadable PDF cannot
            # monopolize every scheduled run.
            if period not in existing or extraction_attempt_age(period) is None:
                return (0, 0, period_key(period))
            return (1, extraction_attempt_count(period), period_key(period))

        processing_periods = sorted(eligible_periods, key=extraction_priority)[:max(1, int(max_extract_periods))]
        processing_set = set(processing_periods)

        # Save all discovered source links now. Extraction of their figures is
        # deferred to later scheduled runs, so one difficult PDF won't block the ticker queue.
        for period in ordered_periods:
            if period in processing_set or period in existing:
                continue
            options = sorted(candidates[period], key=lambda x: x[0])
            _, record, cumulative = options[0]
            url = doc_url(record)
            placeholder = make_placeholder(symbol, period, record, url, cumulative)
            placeholder.setdefault("source_validation", {})["extraction_deferred_for_short_batch"] = True
            items.append(placeholder)
            existing[period] = placeholder
            added += 1
            changed = True
            print(f"  {symbol} {period}: đã lưu nguồn và kỳ báo cáo; trích xuất số liệu sẽ chạy ở lượt tiếp theo.")

    if not processing_periods:
        print(f"  {symbol}: tất cả kỳ chờ trích xuất đều đang trong thời gian nghỉ thử lại.")
    for period in processing_periods:
        options = sorted(candidates[period], key=lambda x: x[0])
        _, record, cumulative = options[0]
        url = doc_url(record)
        try:
            pdf_bytes, final_url = extract_pdf_bytes(url, session)
            previous = choose_previous_item(items, period)
            try:
                values = extract_statement(pdf_bytes, previous, symbol=symbol, cumulative=cumulative)
            except ValueError as text_error:
                print(f"    Trích xuất văn bản chưa đạt ({text_error}); chuyển sang OCR.")
                values = extract_statement(
                    pdf_bytes, previous, symbol=symbol, cumulative=cumulative, force_ocr=True
                )
            new_item = make_extracted_item(symbol, period, record, url, values, items, cumulative)
            new_item["source_extract_review"]["final_download_url"] = final_url
            if period in existing and existing[period].get("verification_status") != "auto_pending_extraction":
                # The core quarter was already reconciled. Merge only detail rows
                # into it; never replace manually verified assets/profit with OCR output.
                extracted_fields = list(new_item.get("financial_line_items_extracted_fields") or [])
                if not extracted_fields or not new_item.get("financial_line_items_status"):
                    raise ValueError("BCTC lõi đọc được nhưng không trích xuất thêm được chỉ tiêu chi tiết an toàn.")
                idx = next(i for i, item in enumerate(items) if item.get("period") == period)
                item = items[idx]
                prior_fields = set(item.get("financial_line_items_extracted_fields") or [])
                for field in extracted_fields:
                    value = new_item.get(field)
                    if value is not None and item.get(field) is None:
                        item[field] = value
                    prior_fields.add(field)
                item["financial_line_items_extracted_fields"] = sorted(prior_fields)
                item["financial_line_items_status"] = "auto_extracted_pending_visual_review"
                item["financial_line_items_source"] = url
                item["financial_line_items_source_index_url"] = f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1"
                item["financial_line_items_updated_at"] = utc_now()
                item["financial_line_items_last_attempt_at"] = utc_now()
                item["financial_line_items_attempt_count"] = 0
                item["financial_line_items_last_error"] = None
                item["financial_line_items_note"] = (
                    "Chỉ tiêu chi tiết trích xuất từ báo cáo VietstockFinance. "
                    "Các số lõi đã xác minh được giữ nguyên; chỉ tiêu chi tiết cần đối chiếu trực quan."
                )
                item["financial_line_items_extract_review"] = {
                    "final_download_url": final_url,
                    "balance_equation_matches": abs(values["total_assets"] - values["total_liabilities"] - values["equity"]) <= 3,
                    "unit_note": values.get("unit_note"),
                    "candidate_core_values_not_overwritten": True,
                }
                items[idx] = item
                existing[period] = item
                filled += 1
                print(f"  {symbol} {period}: đã bổ sung chỉ tiêu chi tiết; giữ nguyên số liệu lõi đã xác minh.")
            elif period in existing:
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
                # Keep the reconciled core unchanged; track either core or detail
                # extraction retries on the selected ticker/quarter.
                idx = next((i for i, item in enumerate(items) if item.get("period") == period), None)
                if idx is not None:
                    item = items[idx]
                    if item.get("verification_status") == "auto_pending_extraction":
                        validation = item.setdefault("source_validation", {})
                        validation["last_extraction_attempt_at"] = utc_now()
                        validation["extraction_attempt_count"] = int(validation.get("extraction_attempt_count") or 0) + 1
                        validation["last_extraction_error"] = str(exc)[:500]
                        if validation["extraction_attempt_count"] >= MAX_EXTRACTION_ATTEMPTS:
                            item["verification_status"] = "manual_review_required_pending_extraction"
                            item["source_pages"] = (
                                "Không trích xuất được số liệu lõi đáng tin cậy sau ba lượt tự động. "
                                "Giữ nguyên liên kết VietstockFinance; cần đối chiếu PDF thủ công."
                            )
                            validation["automatic_extraction_exhausted"] = True
                            validation["manual_review_reason"] = str(exc)[:500]
                            print(
                                f"  {symbol} {period}: đã thử {MAX_EXTRACTION_ATTEMPTS} lượt; "
                                "chuyển sang rà soát thủ công và tiếp tục quý khác của cùng mã."
                            )
                    elif not item.get("financial_line_items_status"):
                        item["financial_line_items_last_attempt_at"] = utc_now()
                        item["financial_line_items_attempt_count"] = int(item.get("financial_line_items_attempt_count") or 0) + 1
                        item["financial_line_items_last_error"] = str(exc)[:500]
                        if item["financial_line_items_attempt_count"] >= MAX_EXTRACTION_ATTEMPTS:
                            item["financial_line_items_status"] = "manual_review_required"
                            item["financial_line_items_note"] = (
                                "Đã thử trích xuất chỉ tiêu chi tiết ba lượt nhưng chưa tìm được số liệu đủ tin cậy. "
                                "Các trường còn thiếu được để trống; cần đối chiếu trực quan báo cáo gốc."
                            )
                            item["financial_line_items_manual_review_reason"] = str(exc)[:500]
                            print(
                                f"  {symbol} {period}: chỉ tiêu chi tiết không trích xuất được sau "
                                f"{MAX_EXTRACTION_ATTEMPTS} lượt; đánh dấu cần rà soát thủ công."
                            )
                    items[idx] = item
                    changed = True
                continue
            placeholder = make_placeholder(symbol, period, record, url, cumulative)
            validation = placeholder.setdefault("source_validation", {})
            validation["last_extraction_attempt_at"] = utc_now()
            validation["extraction_attempt_count"] = 1
            validation["last_extraction_error"] = str(exc)[:500]
            items.append(placeholder)
            existing[period] = placeholder
            added += 1
            changed = True
            print(f"  {symbol} {period}: đã thêm liên kết nguồn và trạng thái chờ trích xuất; chưa điền số liệu.")
        items.sort(key=lambda x: period_key(x.get("period", "")))

    if changed:
        snapshot["items"] = items
        if items:
            snapshot["sourceName"] = (
                f"VietstockFinance — báo cáo tài chính theo quý {symbol} "
                f"({items[0].get('period', '2024-Q1')} đến {items[-1].get('period', '')})"
            )
        else:
            snapshot["sourceName"] = f"VietstockFinance — {symbol} (đang chờ báo cáo tài chính theo quý từ 2024-Q1)"
            snapshot["source_index_url"] = f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1"
            snapshot["sync_status"] = "no_quarterly_consolidated_records_returned"
            snapshot["sync_note"] = "Chưa tìm thấy kỳ BCTC hợp nhất theo quý từ 2024 trong danh mục VietstockFinance; lịch đồng bộ sẽ thử lại."
        if items:
            snapshot["sync_status"] = "records_found"
            snapshot.pop("sync_note", None)
        snapshot["fetchedAt"] = utc_now()
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed, added, filled


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    print("Đồng bộ BCTC theo quý — chỉ danh mục VietstockFinance, doctype=1")
    current_year = datetime.now(timezone.utc).year
    selected = os.environ.get("FINANCIAL_SYNC_SYMBOL", "").strip().upper()
    bootstrap_only = os.environ.get("FINANCIAL_SYNC_BOOTSTRAP_ONLY", "").strip().lower() in {"1", "true", "yes"}
    # A script-push run is an intentional operator retry; scheduled runs keep the 30-minute cooldown.
    force_retry = os.environ.get("FINANCIAL_SYNC_FORCE_RETRY", "").strip().lower() in {"1", "true", "yes"}
    if force_retry:
        print("Bỏ qua cooldown của snapshot rỗng theo yêu cầu retry có chủ đích; vẫn chỉ xử lý một mã và không tự tạo số liệu.")
    if selected and selected not in SYMBOLS:
        print(f"Mã không có trong config/securities.json: {selected}", file=sys.stderr)
        return 2
    if selected:
        symbols_to_sync = [selected]
    elif bootstrap_only:
        # Strict single-ticker queue. Walk configured order and stop at the
        # first missing/incomplete snapshot; never skip it for another ticker.
        cooldown_seconds = 30 * 60
        now_epoch = datetime.now(timezone.utc).timestamp()
        selected_symbol = None

        def load_symbol_snapshot(symbol: str) -> dict | None:
            path = DATA_DIR / f"financials-{symbol}.json"
            if not path.exists():
                return None
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {}

        def last_attempt_epoch(snapshot: dict) -> float:
            stamp = snapshot.get("bootstrap_last_attempt_at") or snapshot.get("fetchedAt")
            if not stamp:
                return 0.0
            try:
                return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError, OSError):
                return 0.0

        for symbol in SYMBOLS:
            snapshot = load_symbol_snapshot(symbol)
            if snapshot is None:
                selected_symbol = symbol
                print(f"Single-ticker queue: bắt đầu mã còn thiếu đầu tiên {symbol}.")
                break
            if not snapshot:
                selected_symbol = symbol
                print(f"Single-ticker queue: snapshot của {symbol} không đọc được; ưu tiên sửa mã này trước.")
                break
            if snapshot.get("bootstrap_status") == "complete_needs_manual_review":
                print(f"Skip {symbol}: đã lưu dữ liệu, chỉ còn rà soát thủ công; không tải lại mã này.")
                continue
            if snapshot.get("bootstrap_status") == "complete":
                review_statuses = {
                    "manual_review_required",
                    "manual_review_required_pending_extraction",
                    "no_detail_fields_matched_pending_manual_review",
                    "auto_extracted_pending_visual_review",
                    "auto_extracted_pending_visual_review",
                }
                if any(
                    isinstance(item, dict) and (
                        item.get("verification_status") in {"manual_review_required", "manual_review_required_pending_extraction"}
                        or item.get("financial_line_items_status") in review_statuses
                    )
                    for item in snapshot.get("items", [])
                ):
                    snapshot["bootstrap_status"] = "complete_needs_manual_review"
                    snapshot["bootstrap_completion_note"] = "Đã lưu dữ liệu tự động; các chỉ tiêu được trích xuất cần đối chiếu trực quan. Mã này sẽ không tự tải lại."
                    snapshot_path = DATA_DIR / f"financials-{symbol}.json"
                    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"Reclassified {symbol}: saved data, manual visual review remains; skip future automatic fetches.")
                else:
                    print(f"Skip {symbol}: bootstrap đã hoàn tất; không tải lại mã này.")
                continue

            items = snapshot.get("items", [])
            has_pending_core = any(
                isinstance(item, dict)
                and item.get("verification_status") == "auto_pending_extraction"
                for item in items
            )
            has_pending_details = any(
                isinstance(item, dict)
                and period_key(str(item.get("period") or ""))[0] >= 2024
                and item.get("total_assets") is not None
                and item.get("net_profit") is not None
                and not item.get("financial_line_items_status")
                for item in items
            )
            has_stale_details = any(
                isinstance(item, dict)
                and period_key(str(item.get("period") or ""))[0] >= 2024
                and item.get("financial_line_items_status") not in {
                    None, "manual_review_required", "manual_review_required_pending_extraction",
                    "no_detail_fields_matched_pending_manual_review"
                }
                and item.get("financial_line_items_schema_version") != "2026-10-22-bank-statement-qc-v4"
                for item in items
            )
            if has_stale_details:
                print(
                    f"Single-ticker queue paused at {symbol}: detail schema needs enrichment. "
                    "OCR/enrichment workflow must finish this ticker before any later ticker is bootstrapped."
                )
                return 0
            if items and not has_pending_core and not has_pending_details:
                terminal_review_statuses = {
                    "manual_review_required",
                    "manual_review_required_pending_extraction",
                    "no_detail_fields_matched_pending_manual_review",
                    "auto_extracted_pending_visual_review",
                }
                needs_manual_review = any(
                    isinstance(item, dict) and (
                        item.get("verification_status") in {"manual_review_required", "manual_review_required_pending_extraction"}
                        or item.get("financial_line_items_status") in terminal_review_statuses
                    )
                    for item in items
                )
                completed_status = "complete_needs_manual_review" if needs_manual_review else "complete"
                snapshot["bootstrap_status"] = completed_status
                snapshot["bootstrap_completed_at"] = snapshot.get("bootstrap_completed_at") or utc_now()
                snapshot["bootstrap_completion_note"] = (
                    "Các kỳ báo cáo có thể tự trích xuất đã được lưu; một số kỳ còn cần đối chiếu thủ công."
                    if needs_manual_review else
                    "Đã lưu các kỳ báo cáo hợp nhất theo quý; tự động không tải lại mã này."
                )
                snapshot_path = DATA_DIR / f"financials-{symbol}.json"
                snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"Saved completion checkpoint for {symbol}: {completed_status}.")
                continue
            attempts = int(snapshot.get("bootstrap_attempt_count") or 0)
            empty_snapshot = not items
            terminal_empty = (
                empty_snapshot
                and attempts >= 3
                and snapshot.get("sync_status") in {
                    "fetch_failed", "no_quarterly_consolidated_records_returned",
                    "needs_manual_review_no_quarterly_data",
                }
            )
            if terminal_empty and not (has_pending_core or has_pending_details):
                snapshot["bootstrap_status"] = "complete_needs_manual_review"
                snapshot["bootstrap_completed_at"] = snapshot.get("bootstrap_completed_at") or utc_now()
                snapshot["bootstrap_completion_note"] = (
                    "Đã thử tự động ba lượt nhưng chưa lấy được BCTC hợp nhất. "
                    "Giữ liên kết nguồn để rà soát thủ công; tự động không tải lại mã này."
                )
                snapshot_path = DATA_DIR / f"financials-{symbol}.json"
                snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"{symbol}: saved manual-review terminal state after {attempts} attempts; stop here so the checkpoint commits before any next ticker.")
                return 0
            needs_retry = has_pending_core or has_pending_details or (empty_snapshot and not terminal_empty)
            if needs_retry:
                # Per-quarter retry cooldown is enforced inside process_symbol:
                # an unreadable quarter is skipped until its own retry window expires,
                # while other unattempted quarters of this SAME ticker can continue.
                if empty_snapshot:
                    age = now_epoch - last_attempt_epoch(snapshot)
                    if age < cooldown_seconds and not force_retry:
                        print(
                            f"Single-ticker queue đang giữ {symbol}: snapshot chưa có kỳ báo cáo; "
                            f"đã thử gần đây {max(0, int(age))} giây trước. Không chuyển sang mã khác."
                        )
                        return 0
                selected_symbol = symbol
                print(f"Single-ticker queue: tiếp tục hoàn tất {symbol} trước khi sang mã khác.")
                break

        if selected_symbol:
            symbols_to_sync = [selected_symbol]
        else:
            print("Single-ticker queue complete: all enabled tickers have saved completion checkpoints; no completed ticker will be fetched again automatically.")
            return 0

    # Only contact Vietstock after a pending ticker has been selected.
    token = get_anti_forgery_token(session)
    total_changed = total_added = total_filled = failed_symbols = 0
    for symbol in symbols_to_sync:
        print(f"\n[{symbol}]")
        try:
            changed, added, filled = process_symbol(
                session, token, symbol, current_year,
                max_extract_periods=16 if bootstrap_only else None,
            )
            total_changed += int(changed)
            total_added += added
            total_filled += filled
        except Exception as exc:
            failed_symbols += 1
            print(f"  LỖI {symbol}: {exc}", file=sys.stderr)
            if bootstrap_only:
                # Keep the sequential bootstrap moving without inventing numbers.
                # The scheduled full sync retries this explicit empty/error snapshot.
                path = DATA_DIR / f"financials-{symbol}.json"
                if not path.exists():
                    placeholder = {
                        "symbol": symbol,
                        "sourceName": f"VietstockFinance — {symbol} (chờ lấy báo cáo tài chính theo quý)",
                        "fetchedAt": utc_now(),
                        "source_index_url": f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1",
                        "sync_status": "fetch_failed",
                        "sync_note": "Lần lấy dữ liệu ban đầu gặp lỗi; không tạo số liệu giả. Lịch đồng bộ tiếp theo sẽ thử lại.",
                        "items": [],
                    }
                    path.write_text(json.dumps(placeholder, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"  {symbol}: đã ghi snapshot rỗng có trạng thái lỗi để tiếp tục xử lý mã kế tiếp.")
        if bootstrap_only:
            state_path = DATA_DIR / f"financials-{symbol}.json"
            if state_path.exists():
                try:
                    state_snapshot = json.loads(state_path.read_text(encoding="utf-8"))
                    state_snapshot["bootstrap_last_attempt_at"] = utc_now()
                    state_snapshot["bootstrap_attempt_count"] = int(state_snapshot.get("bootstrap_attempt_count") or 0) + 1
                    state_items = state_snapshot.get("items") or []
                    terminal_review_statuses = {
                        "manual_review_required",
                        "manual_review_required_pending_extraction",
                        "no_detail_fields_matched_pending_manual_review",
                        "auto_extracted_pending_visual_review",
                    }
                    state_pending_core = any(
                        isinstance(item, dict) and item.get("verification_status") == "auto_pending_extraction"
                        for item in state_items
                    )
                    state_pending_details = any(
                        isinstance(item, dict)
                        and period_key(str(item.get("period") or ""))[0] >= 2024
                        and item.get("total_assets") is not None
                        and item.get("net_profit") is not None
                        and not item.get("financial_line_items_status")
                        for item in state_items
                    )
                    state_stale_details = any(
                        isinstance(item, dict)
                        and period_key(str(item.get("period") or ""))[0] >= 2024
                        and item.get("financial_line_items_status") is not None
                        and item.get("financial_line_items_status") not in terminal_review_statuses
                        and item.get("financial_line_items_schema_version") != "2026-10-22-bank-statement-qc-v4"
                        for item in state_items
                    )
                    if state_items and not state_pending_core and not state_pending_details and not state_stale_details:
                        needs_manual_review = any(
                            isinstance(item, dict) and (
                                item.get("verification_status") in {"manual_review_required", "manual_review_required_pending_extraction"}
                                or item.get("financial_line_items_status") in terminal_review_statuses
                            )
                            for item in state_items
                        )
                        state_snapshot["bootstrap_status"] = "complete_needs_manual_review" if needs_manual_review else "complete"
                        state_snapshot["bootstrap_completed_at"] = state_snapshot.get("bootstrap_completed_at") or utc_now()
                        state_snapshot["bootstrap_completion_note"] = (
                            "Các kỳ báo cáo có thể tự trích xuất đã được lưu; một số kỳ còn cần đối chiếu thủ công."
                            if needs_manual_review else
                            "Đã lưu các kỳ báo cáo hợp nhất theo quý; tự động không tải lại mã này."
                        )
                    elif not state_items and int(state_snapshot.get("bootstrap_attempt_count") or 0) >= 3 and state_snapshot.get("sync_status") in {
                        "fetch_failed", "no_quarterly_consolidated_records_returned", "needs_manual_review_no_quarterly_data"
                    }:
                        state_snapshot["bootstrap_status"] = "complete_needs_manual_review"
                        state_snapshot["bootstrap_completed_at"] = state_snapshot.get("bootstrap_completed_at") or utc_now()
                        state_snapshot["bootstrap_completion_note"] = "Đã thử tự động ba lượt nhưng không lấy được BCTC; cần rà soát nguồn thủ công."
                    else:
                        state_snapshot["bootstrap_status"] = "in_progress"
                    state_path.write_text(json.dumps(state_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                except (OSError, json.JSONDecodeError, TypeError, ValueError) as state_error:
                    print(f"  Không ghi được trạng thái bootstrap cho {symbol}: {state_error}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN_CALLS)
    print("\nTóm tắt")
    print(f"- Mã: {len(symbols_to_sync)}; lỗi truy vấn/đọc snapshot: {failed_symbols}")
    print(f"- Snapshot thay đổi: {total_changed}")
    print(f"- Kỳ mới được thêm (có thể đang chờ trích xuất): {total_added}")
    print(f"- Kỳ chờ trước đó đã điền được số liệu: {total_filled}")
    if failed_symbols == len(symbols_to_sync) and not bootstrap_only:
        print("Tất cả mã đều lỗi; workflow sẽ báo thất bại để không coi đây là lần đồng bộ thành công.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
