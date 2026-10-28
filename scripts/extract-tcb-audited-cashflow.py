#!/usr/bin/env python3
"""Extract the audited FY2025 consolidated cash-flow statement pages for TCB.

This targeted, resumable helper only updates the OCR sidecar for the already
archived PDF linked from VietstockFinance. It never changes financial values.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "reports/raw/TCB/vietstock-tcb-2024-2026-20261019/553195cdc772f58a.pdf"
SIDECAR = Path(str(PDF) + ".extracted.json")
Q3_PDF = ROOT / "reports/raw/TCB/repair-tcb-2026q3-full-report/fd82d64db310dbdb.pdf"
Q3_SIDECAR = Path(str(Q3_PDF) + ".extracted.json")
Q3_TARGET_PAGE = 12
TARGET_PAGES = (15, 16)  # PDF pages; report's printed pages 10–11 (cash-flow statement)


def native_text(page) -> str:
    try:
        return (page.extract_text(extraction_mode="layout") or "").strip()
    except TypeError:
        return (page.extract_text() or "").strip()
    except Exception:
        return ""


def ocr_pages(pdf_path: Path, page_numbers: tuple[int, ...]) -> dict[int, str]:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise RuntimeError("Missing pdftoppm/tesseract; cannot safely OCR scanned statement pages.")
    results: dict[int, str] = {}
    with tempfile.TemporaryDirectory(prefix="tcb-audited-cashflow-") as tmp:
        prefix = Path(tmp) / "page"
        run = subprocess.run(
            ["pdftoppm", "-f", str(min(page_numbers)), "-l", str(max(page_numbers)),
             "-r", "300", "-gray", "-png", str(pdf_path), str(prefix)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=240,
        )
        if run.returncode:
            raise RuntimeError("PDF rendering failed: " + run.stderr[-1200:])
        for image in Path(tmp).glob("page-*.png"):
            try:
                number = int(image.stem.rsplit("-", 1)[1])
            except ValueError:
                continue
            if number not in page_numbers:
                continue
            run = subprocess.run(
                ["tesseract", str(image), "stdout", "-l", "vie+eng", "--psm", "6"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90,
            )
            if run.returncode not in (0, 1):
                raise RuntimeError(f"Tesseract failed on PDF page {number}: {run.stderr[-600:]}")
            results[number] = run.stdout.strip()
    return results



def rescan_q3_cashflow_page() -> None:
    """Re-OCR TCB Q3/2026 statement continuation page at 300dpi; do not edit snapshot values."""
    if not Q3_PDF.is_file() or not Q3_SIDECAR.is_file():
        raise SystemExit(f"Required Q3 source PDF/sidecar not found: {Q3_PDF}")
    reader = PdfReader(str(Q3_PDF), strict=False)
    if len(reader.pages) < Q3_TARGET_PAGE:
        raise SystemExit(f"Q3 source PDF has only {len(reader.pages)} pages; expected page {Q3_TARGET_PAGE}.")
    ocr = ocr_pages(Q3_PDF, (Q3_TARGET_PAGE,))
    new_text = ocr.get(Q3_TARGET_PAGE, "").strip()
    if len(new_text) < 250 or "lưu chuyển tiền" not in new_text.lower():
        raise SystemExit("High-resolution Q3/2026 page 12 OCR failed; leave prior sidecar unchanged.")
    extracted = json.loads(Q3_SIDECAR.read_text(encoding="utf-8"))
    pages = {
        int(page["page"]): page for page in extracted.get("pages", [])
        if isinstance(page, dict) and str(page.get("page", "")).isdigit()
    }
    old_page = pages.get(Q3_TARGET_PAGE, {})
    pages[Q3_TARGET_PAGE] = {
        **old_page,
        "page": Q3_TARGET_PAGE,
        "text": new_text[:25000],
        "ocr": True,
        "ocr_engine": "tesseract-vie+eng-psm6-300dpi-targeted-rescan",
        "forced_rescan_completed": True,
        "forced_rescan_count": int(old_page.get("forced_rescan_count") or 0) + 1,
        "targeted_review_date": "2026-10-28",
    }
    extracted["pages"] = [pages[n] for n in sorted(pages)]
    extracted["page_count"] = len(reader.pages)
    extracted["targeted_extraction_note"] = (
        str(extracted.get("targeted_extraction_note") or "").rstrip()
        + " Re-scanned source PDF page 12 at 300dpi on 2026-10-28 to inspect the 20-million-VND cash-bridge residual. "
        "OCR is evidence only; snapshot values were not changed automatically."
    ).strip()
    Q3_SIDECAR.write_text(json.dumps(extracted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n===== TCB Q3/2026 PDF PAGE 12 (300dpi targeted OCR) =====\n{new_text[:16000]}")
    print(f"Updated sidecar: {Q3_SIDECAR.relative_to(ROOT)}")

def main() -> None:
    if not PDF.is_file() or not SIDECAR.is_file():
        raise SystemExit(f"Required archived PDF/sidecar not found: {PDF}")
    reader = PdfReader(str(PDF), strict=False)
    print(f"Audited consolidated TCB FY2025 PDF pages: {len(reader.pages)}")
    if max(TARGET_PAGES) > len(reader.pages):
        raise SystemExit(
            f"Expected cash-flow pages {TARGET_PAGES}; source PDF has only {len(reader.pages)} pages. Stop without edits."
        )
    extracted = json.loads(SIDECAR.read_text(encoding="utf-8"))
    if extracted.get("kind") != "pdf":
        raise SystemExit("Sidecar is not a PDF extraction; stop without edits.")
    existing = {
        int(page["page"]): page
        for page in extracted.get("pages", [])
        if isinstance(page, dict) and str(page.get("page", "")).isdigit()
    }
    native = {number: native_text(reader.pages[number - 1]) for number in TARGET_PAGES}
    need_ocr = tuple(number for number, value in native.items()
                     if len(value) < 350 or "lưu chuyển tiền" not in value.lower())
    scanned = ocr_pages(PDF, need_ocr) if need_ocr else {}
    for number in TARGET_PAGES:
        text = native[number]
        is_ocr = False
        engine = "pypdf-native-layout"
        if number in scanned and len(scanned[number]) > len(text):
            text = scanned[number]
            is_ocr = True
            engine = "tesseract-vie+eng-psm6-300dpi"
        if len(text.strip()) < 200 or "lưu chuyển tiền" not in text.lower():
            raise SystemExit(
                f"Could not reliably extract cash-flow heading on source PDF page {number}; no sidecar update."
            )
        existing[number] = {
            "page": number,
            "text": text[:25000],
            "ocr": is_ocr,
            "ocr_engine": engine,
            "source_document": "TCB consolidated audited financial statements for year ended 2025",
            "source_document_announced_at": "2026-03-17",
        }
        print(f"\n===== PDF PAGE {number} ({'OCR' if is_ocr else 'native text'}) =====\n{text[:14000]}")
    extracted["pages"] = [existing[n] for n in sorted(existing)]
    extracted["page_count"] = len(reader.pages)
    extracted["targeted_extraction_note"] = (
        "Targeted extraction of PDF pages 15-16, the printed cash-flow statement pages 10-11, "
        "from the audited TCB consolidated FY2025 report announced on 2026-03-17. "
        "This extraction is evidence for manual data reconciliation; it does not itself modify snapshot values."
    )
    SIDECAR.write_text(json.dumps(extracted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated sidecar: {SIDECAR.relative_to(ROOT)}")
    rescan_q3_cashflow_page()


if __name__ == "__main__":
    main()
