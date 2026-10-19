#!/usr/bin/env python3
"""OCR the first financial-statement pages when Vietstock PDFs are image-only.

This is a review aid: originals remain unchanged and OCR text is stored only in
the companion extraction JSON. Figures are not published automatically.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime, timezone

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports/raw"
QUEUE_PATH = ROOT / "config/report-queue.json"
MAX_PAGES = int(os.getenv("REPORT_OCR_MAX_PAGES", "6"))
DPI = int(os.getenv("REPORT_OCR_DPI", "180"))


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select_symbol() -> str | None:
    override = os.getenv("REPORT_OCR_SYMBOL", "").strip().upper()
    if override:
        return override
    queue = load_json(QUEUE_PATH) or {}
    jobs = [j for j in queue.get("jobs", []) if j.get("processedAt")]
    if not jobs:
        return None
    latest = max(jobs, key=lambda j: str(j.get("processedAt") or ""))
    return str(latest.get("symbol") or "").upper() or None


def page_has_text(pages) -> bool:
    return any(isinstance(p, dict) and len(str(p.get("text") or "").strip()) > 20 for p in pages or [])


def ocr_pdf(path: Path, max_pages: int = MAX_PAGES):
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        return [], "OCR tools are unavailable on this runner."
    try:
        page_count = len(PdfReader(str(path)).pages)
    except Exception as exc:
        return [], f"Cannot read PDF page count: {exc}"
    count = min(max(page_count, 0), max_pages)
    if count < 1:
        return [], "PDF contains no pages."
    results = []
    with tempfile.TemporaryDirectory(prefix="solie-ocr-") as temp_dir:
        tmp = Path(temp_dir)
        prefix = tmp / "page"
        try:
            render = subprocess.run(
                ["pdftoppm", "-f", "1", "-l", str(count), "-r", str(DPI),
                 "-gray", "-png", str(path), str(prefix)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                timeout=180, check=False,
            )
        except Exception as exc:
            return [], f"PDF rendering failed: {exc}"
        if render.returncode != 0:
            return [], f"pdftoppm failed: {render.stderr[-800:]}"
        images = sorted(tmp.glob("page-*.png"))
        for page_number, image_path in enumerate(images[:count], start=1):
            try:
                result = subprocess.run(
                    ["tesseract", str(image_path), "stdout", "-l", "vie+eng", "--psm", "6"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    timeout=45, check=False,
                )
                text = (result.stdout or "").strip()
                if text:
                    results.append({
                        "page": page_number,
                        "text": text[:25000],
                        "ocr": True,
                        "ocr_engine": "tesseract-vie+eng",
                    })
            except Exception:
                continue
    return results, None if results else "OCR produced no text on the first pages."


def process_pdf(pdf_path: Path):
    extraction_path = Path(str(pdf_path) + ".extracted.json")
    extracted = load_json(extraction_path) or {}
    if extracted.get("kind") != "pdf":
        return {"path": str(pdf_path.relative_to(ROOT)), "status": "skipped_not_pdf_extraction"}
    if page_has_text(extracted.get("pages")):
        return {"path": str(pdf_path.relative_to(ROOT)), "status": "already_has_text"}
    pages, note = ocr_pdf(pdf_path)
    if not pages:
        return {"path": str(pdf_path.relative_to(ROOT)), "status": "ocr_empty", "note": note}
    extracted["pages"] = pages
    extracted["extraction"] = "ocr"
    extracted["ocr_pages"] = len(pages)
    extracted["ocr_completed_at"] = datetime.now(timezone.utc).isoformat()
    extracted["note"] = "OCR on first pages to aid review; manually verify values before publication."
    save_json(extraction_path, extracted)
    return {"path": str(pdf_path.relative_to(ROOT)), "status": "ocr_done", "pages": len(pages)}


def process_zip(zip_path: Path):
    extraction_path = Path(str(zip_path) + ".extracted.json")
    extracted = load_json(extraction_path) or {}
    if extracted.get("kind") != "zip" or not isinstance(extracted.get("members"), list):
        return {"path": str(zip_path.relative_to(ROOT)), "status": "skipped_no_zip_extraction"}
    changes = 0
    outcomes = []
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            available = set(archive.namelist())
            for member in extracted["members"]:
                if member.get("kind") != "pdf" or page_has_text(member.get("pages")):
                    continue
                name = member.get("name")
                if not name or name not in available:
                    outcomes.append({"member": name, "status": "member_missing_from_archive"})
                    continue
                raw = archive.read(name)
                with tempfile.TemporaryDirectory(prefix="solie-zip-pdf-") as td:
                    inner_pdf = Path(td) / "member.pdf"
                    inner_pdf.write_bytes(raw)
                    pages, note = ocr_pdf(inner_pdf)
                if pages:
                    member["pages"] = pages
                    member["extraction"] = "ocr"
                    member["ocr_pages"] = len(pages)
                    member["ocr_engine"] = "tesseract-vie+eng"
                    member["note"] = "OCR on first pages to aid review; manually verify values before publication."
                    changes += 1
                    outcomes.append({"member": name, "status": "ocr_done", "pages": len(pages)})
                else:
                    outcomes.append({"member": name, "status": "ocr_empty", "note": note})
    except Exception as exc:
        return {"path": str(zip_path.relative_to(ROOT)), "status": "zip_read_failed", "error": str(exc)[:500]}
    if changes:
        extracted["extraction"] = "archive_members_with_ocr"
        extracted["ocr_completed_at"] = datetime.now(timezone.utc).isoformat()
        extracted["note"] = "Image-only PDFs in the ZIP were OCRed on their first pages; manually verify before publishing."
        save_json(extraction_path, extracted)
    return {"path": str(zip_path.relative_to(ROOT)), "status": "ocr_done" if changes else "no_ocr_changes", "members_changed": changes, "members": outcomes}


def main():
    symbol = select_symbol()
    if not symbol:
        print(json.dumps({"event": "ocr_skip", "reason": "No latest processed symbol in report queue."}, ensure_ascii=False))
        return
    folder = REPORTS / symbol
    if not folder.exists():
        print(json.dumps({"event": "ocr_skip", "symbol": symbol, "reason": "No archive folder exists yet."}, ensure_ascii=False))
        return
    files = sorted(folder.rglob("*"))
    summary = {"event": "ocr_stored_report_archive", "symbol": symbol, "max_pages": MAX_PAGES, "results": []}
    for path in files:
        if not path.is_file():
            continue
        lower = path.name.lower()
        if lower.endswith(".pdf") and not lower.endswith(".pdf.extracted.json"):
            ext = Path(str(path) + ".extracted.json")
            if ext.exists():
                result = process_pdf(path)
                if result.get("status") != "already_has_text":
                    summary["results"].append(result)
        elif lower.endswith(".zip") and not lower.endswith(".zip.extracted.json"):
            ext = Path(str(path) + ".extracted.json")
            if ext.exists():
                result = process_zip(path)
                if result.get("members_changed") or result.get("status") not in {"no_ocr_changes"}:
                    summary["results"].append(result)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
