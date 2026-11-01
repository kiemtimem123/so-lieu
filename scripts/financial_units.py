"""Financial statement unit normalization helpers."""

import re
import unicodedata


def _norm(value: object) -> str:
    text = str(value or "").lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def scale_to_million(
    text: str,
    raw_assets: float,
    previous_assets_million: float | None,
) -> tuple[float, str]:
    """Normalize source statement values to million VND.

    Explicit statement-unit declarations outrank narrative unit mentions in
    disclosure letters (for example, a cover letter saying "1,002 tỷ đồng"
    while the actual B01/B02/B03b tables are denominated in VND).
    """
    header = _norm(str(text or "")[:25000])
    explicit_vnd = re.search(
        r"\b(?:dvt|bvt|don vi tinh|unit)\s*[:\-]?\s*vnd\b",
        header,
    )
    if explicit_vnd:
        return 1e-6, "VND → triệu VND (đơn vị báo cáo ghi rõ VND)"
    if any(term in header for term in (
        "ngan dong", "ngan vnd", "nghin dong", "nghin vnd",
        "thousand dong", "thousand vnd"
    )) or re.search(r"\bngh?[a-z~._-]{0,4}n\s+(?:dong|vnd)\b", header):
        return 1e-3, "ngàn/nghìn VND → triệu VND"
    if "trieu dong" in header or "trieu vnd" in header or "million vnd" in header:
        return 1.0, "triệu VND"
    if "ty dong" in header or "ty vnd" in header or "billion vnd" in header:
        return 1e3, "tỷ VND → triệu VND"
    if re.search(r"don vi(?: tinh)?\s*[:\-]?\s*(?:vnd|dong)\b", header):
        return 1e-6, "VND → triệu VND"

    # Unknown unit: infer the scale from the previous quarter's assets, then
    # refuse extraction if no plausible conversion can be supported.
    if previous_assets_million and previous_assets_million > 0 and raw_assets > 0:
        import math
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

def drop_leading_statement_row_code(values: list[float], code: int) -> list[float]:
    """Remove a statement row code mistakenly parsed as the first value."""
    if values and int(round(values[0])) == int(code):
        return values[1:]
    return values
