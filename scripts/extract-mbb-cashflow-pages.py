#!/usr/bin/env python3
"""Targeted 300-dpi OCR of MBB quarterly cash-flow statement pages 7-8.

This is a source-evidence step for one ticker only. It preserves prior extraction
text, writes new OCR evidence into a separate sidecar property, and never mutates
the public financial snapshot.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/financials-MBB.json"
TARGET_PAGES = (7, 8)
DPI = 300


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def quality(text: str) -> float:
    value = (text or "").strip()
    words = re.findall(r"[A-Za-zÀ-ỹĐđ]{3,}", value)
    numbers = re.findall(r"(?<![A-Za-z])\(?-?\d[\d.,]{1,}\)?(?![A-Za-z])", value)
    return round((4 * len(words) + 2 * len(numbers)) / max(len(value), 1), 4)


def targeted_ocr(pdf: Path) -> list[dict]:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise RuntimeError("Missing pdftoppm/tesseract OCR dependencies")
    reader = PdfReader(str(pdf), strict=False)
    if len(reader.pages) < max(TARGET_PAGES):
        raise RuntimeError(f"{pdf.name}: only {len(reader.pages)} pages; expected page 8")
    results = []
    with tempfile.TemporaryDirectory(prefix="mbb-cashflow-") as temp_dir:
        prefix = Path(temp_dir) / "page"
        render = subprocess.run(
            ["pdftoppm", "-f", "7", "-l", "8", "-r", str(DPI), "-gray", "-png",
             str(pdf), str(prefix)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            timeout=240, check=False,
        )
        if render.returncode != 0:
            raise RuntimeError(f"{pdf.name}: pdftoppm failed: {render.stderr[-800:]}")
        images = sorted(Path(temp_dir).glob("page-*.png"))
        for image in images:
            match = re.search(r"-(\d+)\.png$", image.name, re.I)
            if not match:
                continue
            page_number = int(match.group(1))
            if page_number not in TARGET_PAGES:
                continue
            result = subprocess.run(
                ["tesseract", str(image), "stdout", "-l", "vie+eng", "--psm", "6"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=90, check=False,
            )
            if result.returncode not in (0, 1):
                raise RuntimeError(f"{pdf.name} page {page_number}: Tesseract failed: {result.stderr[-600:]}")
            text = result.stdout.strip()
            if len(text) < 300:
                raise RuntimeError(f"{pdf.name} page {page_number}: OCR output unexpectedly short")
            if not re.search(r"lưu chuy|luu chuy|tiền và các khoản tương đương|tien va cac khoan tuong duong", text, re.I):
                raise RuntimeError(f"{pdf.name} page {page_number}: cash-flow rows not detected; leave old evidence intact")
            results.append({
                "page": page_number,
                "text": text[:25000],
                "ocr_engine": "tesseract-vie+eng-psm6-300dpi-targeted-rescan",
                "ocr_quality_score": quality(text),
                "ocr": True,
            })
    by_page = {item["page"]: item for item in results}
    if set(by_page) != set(TARGET_PAGES):
        raise RuntimeError(f"{pdf.name}: expected pages {TARGET_PAGES}, got {sorted(by_page)}")
    return [by_page[n] for n in TARGET_PAGES]


def main() -> None:
    snapshot = load_json(SNAPSHOT)
    if not isinstance(snapshot, dict) or snapshot.get("symbol") != "MBB":
        raise SystemExit("MBB snapshot not found/invalid; no changes made")
    archive_paths = sorted({
        str(row.get("source_archive_file") or "").strip()
        for row in snapshot.get("items", [])
        if isinstance(row, dict) and str(row.get("source_archive_file") or "").strip()
    })
    if len(archive_paths) != len(snapshot.get("items", [])):
        print("WARN: some MBB items have no source archive path; they will not be silently invented.")
    if not archive_paths:
        raise SystemExit("No MBB archive paths available")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed = []
    errors = []
    for relative in archive_paths:
        source = (ROOT / relative).resolve()
        try:
            source.relative_to((ROOT / "reports/raw/MBB").resolve())
        except ValueError:
            errors.append(f"refused out-of-scope archive path: {relative}")
            continue
        sidecar_path = Path(str(source) + ".extracted.json")
        sidecar = load_json(sidecar_path)
        if not source.is_file() or not isinstance(sidecar, dict) or sidecar.get("kind") != "pdf":
            errors.append(f"missing PDF/valid sidecar: {relative}")
            continue
        try:
            pages = targeted_ocr(source)
        except Exception as exc:
            errors.append(f"{relative}: {exc}")
            continue
        sidecar["targeted_cashflow_ocr_300dpi"] = {
            "source_archive_file": relative,
            "source_catalog_url": "https://finance.vietstock.vn/MBB/tai-tai-lieu.htm?doctype=1",
            "performed_at": stamp,
            "dpi": DPI,
            "pages": pages,
            "note": "Independent targeted OCR evidence for quarterly cash-flow statement PDF pages 7-8. Original pages[] retained; this evidence does not alter snapshot values automatically.",
        }
        save_json(sidecar_path, sidecar)
        changed.append(relative)
        print(f"OK {relative}: pages 7-8 OCRed at {DPI}dpi; quality " +
              ", ".join(f"p{p['page']}={p['ocr_quality_score']}" for p in pages))
        # Print just the cash-flow totals to support quick human review without flooding logs.
        for page in pages:
            print(f"--- {relative} PDF page {page['page']} ---")
            for line in page["text"].splitlines():
                if re.search(r"lưu chuyển tiền thuần từ hoạt động kinh doanh$|lưu chuyển tiền thuần sử dụng trong hoạt động đầu tư|lưu chuyển tiền thuần từ hoạt động tài chính|lưu chuyển tiền thuần trong kỳ|tiền và các khoản tương đương tiền.*(đầu|cuối)", line, re.I):
                    print(line.strip())
    print(f"SUMMARY processed={len(changed)}/{len(archive_paths)}; errors={len(errors)}")
    for error in errors:
        print("ERROR " + error)
    if errors:
        # Fail visibly to avoid marking the ticker finished with partial source review.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
