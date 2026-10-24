#!/usr/bin/env python3
"""Persist per-ticker financial-report processing progress after a successful report update.

The checkpoint is a resume aid only. The committed data/*.json and
reports/raw/**/*.extracted.json files remain the source of truth.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
CHECKPOINT_PATH = REPORTS_DIR / "processing-checkpoint.json"
QUARTER_RE = re.compile(r"20\d{2}-Q[1-4]")
CORE_PENDING = {
    "auto_pending_extraction",
    "manual_review_required_pending_extraction",
}
DETAIL_REVIEW_STATUSES = {
    "manual_review_required",
    "manual_review_required_pending_extraction",
    "no_detail_fields_matched_pending_manual_review",
}
DETAIL_SCHEMA_VERSION = "2026-10-22-bank-statement-qc-v4"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def payload_needs_pages(payload: Any, max_pages: int, rescan_pages: set[int]) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("kind") == "pdf":
        documents = [payload]
    elif payload.get("kind") == "zip":
        documents = [
            item for item in payload.get("members", [])
            if isinstance(item, dict) and item.get("kind") == "pdf"
        ]
    else:
        return False

    for document in documents:
        try:
            page_count = int(document.get("page_count") or 0)
        except (TypeError, ValueError):
            page_count = 0
        target_count = min(max(page_count, 0), max_pages)
        pages = {
            int(page.get("page")): page
            for page in document.get("pages", [])
            if isinstance(page, dict) and str(page.get("page", "")).isdigit()
        }
        if any(number not in pages for number in range(1, target_count + 1)):
            return True
        for number in rescan_pages:
            if not 1 <= number <= target_count:
                continue
            page = pages.get(number)
            if page is None or not page.get("forced_rescan_completed"):
                return True
            try:
                score = float(page.get("ocr_quality_score") or 0)
                attempts = int(page.get("forced_rescan_count") or 1)
            except (TypeError, ValueError):
                score, attempts = 0.0, 1
            if score < 0.34 and attempts < 3:
                return True
    return False


def is_terminal_manual_extraction(item: Any) -> bool:
    if not isinstance(item, dict) or item.get("verification_status") != "manual_review_required_pending_extraction":
        return False
    validation = item.get("source_validation")
    if not isinstance(validation, dict):
        validation = {}
    try:
        evidence_attempts = int(item.get("core_financial_extraction_evidence_attempt_count") or 0)
    except (TypeError, ValueError):
        evidence_attempts = 0
    return (
        item.get("core_financial_extraction_manual_terminal") is True
        or validation.get("automatic_extraction_exhausted") is True
        or evidence_attempts >= 3
    )


def next_symbol_hint(symbols: list[str], symbol: str) -> str | None:
    try:
        index = symbols.index(symbol)
    except ValueError:
        return None
    return symbols[index + 1] if index + 1 < len(symbols) else None


def main() -> int:
    symbol = (
        (sys.argv[1] if len(sys.argv) > 1 else "")
        or os.environ.get("REPORT_OCR_SYMBOL", "")
    ).strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{1,12}", symbol):
        raise SystemExit("A valid REPORT_OCR_SYMBOL is required.")

    config = load_json(ROOT / "config" / "securities.json", {}) or {}
    symbols = [
        str(item.get("symbol") or "").strip().upper()
        for item in config.get("securities", [])
        if isinstance(item, dict)
        and item.get("enabled") is not False
        and item.get("symbol")
    ]
    symbols = list(dict.fromkeys(symbols))
    if symbol not in symbols:
        raise SystemExit(f"{symbol} is not enabled in config/securities.json")

    snapshot_path = DATA_DIR / f"financials-{symbol}.json"
    snapshot = load_json(snapshot_path)
    checkpoint = load_json(CHECKPOINT_PATH, {}) or {}
    if not isinstance(checkpoint, dict):
        checkpoint = {}

    max_pages_raw = os.environ.get("REPORT_OCR_MAX_PAGES", "14")
    try:
        max_pages = min(40, max(1, int(max_pages_raw)))
    except (TypeError, ValueError):
        max_pages = 14
    rescan_pages = {
        int(value.strip())
        for value in os.environ.get("REPORT_OCR_RESCAN_PAGES", "").split(",")
        if value.strip().isdigit()
    }

    quarter_items: list[dict[str, Any]] = []
    if isinstance(snapshot, dict):
        quarter_items = [
            item for item in (snapshot.get("items") or [])
            if isinstance(item, dict) and QUARTER_RE.fullmatch(str(item.get("period") or ""))
        ]
    periods = sorted({str(item.get("period")) for item in quarter_items})

    core_pending_periods = sorted({
        str(item.get("period") or "unknown")
        for item in (snapshot.get("items") or []) if isinstance(item, dict)
        and (
            (
                item.get("verification_status") in CORE_PENDING
                and not is_terminal_manual_extraction(item)
            )
            or (
                item.get("balance_sheet_extraction_status") == "pending_full_report_archive_and_extraction"
                and not (
                    isinstance(item.get("source_validation"), dict)
                    and item["source_validation"].get("full_report_present_in_archive") is True
                )
            )
        )
    }) if isinstance(snapshot, dict) else []

    terminal_manual_review_periods = sorted({
        str(item.get("period") or "unknown")
        for item in (snapshot.get("items") or []) if isinstance(item, dict)
        and is_terminal_manual_extraction(item)
    }) if isinstance(snapshot, dict) else []

    details_pending_periods = sorted({
        str(item.get("period") or "unknown")
        for item in quarter_items
        if item.get("total_assets") is not None
        and item.get("net_profit") is not None
        and not item.get("financial_line_items_status")
    })

    stale_detail_periods = sorted({
        str(item.get("period") or "unknown")
        for item in quarter_items
        if item.get("financial_line_items_status")
        and item.get("financial_line_items_status") not in DETAIL_REVIEW_STATUSES
        and item.get("financial_line_items_schema_version") != DETAIL_SCHEMA_VERSION
    })

    statement_pages_pending = False
    checked_archives: set[str] = set()
    for item in quarter_items:
        # A missing linked full report is a live collection dependency even if
        # OCR has exhausted its retries on a shorter correction notice.
        if (
            item.get("balance_sheet_extraction_status") == "pending_full_report_archive_and_extraction"
            and not (
                isinstance(item.get("source_validation"), dict)
                and item["source_validation"].get("full_report_present_in_archive") is True
            )
        ):
            statement_pages_pending = True
            break
        if is_terminal_manual_extraction(item):
            continue
        source = str(item.get("source_archive_file") or "").strip()
        if not source:
            # No archive path means collection/linking has not completed yet.
            # Do not close unresolved quarters as manual review merely because
            # their linked PDF is not stored locally yet.
            if item.get("verification_status") in CORE_PENDING:
                statement_pages_pending = True
                break
            continue
        if source in checked_archives:
            continue
        checked_archives.add(source)
        archive_path = (ROOT / source).resolve()
        try:
            archive_path.relative_to((ROOT / "reports" / "raw").resolve())
        except ValueError:
            continue
        if not archive_path.is_file():
            # Collector may still be archiving the catalog-linked PDF/ZIP.
            if item.get("verification_status") in CORE_PENDING:
                statement_pages_pending = True
                break
            continue
        sidecar_path = Path(str(archive_path) + ".extracted.json")
        extracted = load_json(sidecar_path)
        # Existing archive + missing/invalid sidecar means this report still
        # has extraction work to do. Do not silently call the ticker complete.
        if extracted is None or payload_needs_pages(extracted, max_pages, rescan_pages):
            statement_pages_pending = True
            break

    snapshot_changed = False
    if isinstance(snapshot, dict) and not statement_pages_pending:
        # Once no linked report has any tracked pages left to OCR, remaining
        # unresolved core fields cannot progress automatically on the same
        # evidence. Mark them terminal for automation but retain blanks and
        # require visual review; never manufacture balancing figures.
        for item in quarter_items:
            if item.get("verification_status") not in CORE_PENDING:
                continue
            if is_terminal_manual_extraction(item):
                continue
            item["verification_status"] = "manual_review_required_pending_extraction"
            item["core_financial_extraction_status"] = "manual_review_required_pending_extraction"
            item["core_financial_extraction_manual_terminal"] = True
            item["core_financial_extraction_note"] = (
                "Không còn trang PDF/ZIP đang chờ trích xuất tự động nhưng bộ chỉ tiêu lõi "
                "vẫn thiếu hoặc chưa cân đối. Giữ trống chỉ tiêu chưa xác minh và yêu cầu "
                "đối chiếu trực quan với báo cáo VietstockFinance."
            )
            item["core_financial_extraction_updated_at"] = utc_now()
            snapshot_changed = True
        if snapshot_changed:
            snapshot_path.write_text(
                json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            quarter_items = [
                item for item in (snapshot.get("items") or [])
                if isinstance(item, dict) and QUARTER_RE.fullmatch(str(item.get("period") or ""))
            ]
            core_pending_periods = sorted({
                str(item.get("period") or "unknown")
                for item in quarter_items if item.get("verification_status") in CORE_PENDING
                and not is_terminal_manual_extraction(item)
            })
            terminal_manual_review_periods = sorted({
                str(item.get("period") or "unknown")
                for item in quarter_items if is_terminal_manual_extraction(item)
            })

    if snapshot is None:
        status = "missing_snapshot"
        complete_for_automation = False
    elif (
        snapshot.get("bootstrap_status") in {"complete", "complete_needs_manual_review"}
        and not core_pending_periods
        and not details_pending_periods
        and not stale_detail_periods
        and not statement_pages_pending
    ):
        status = "automated_processing_complete"
        complete_for_automation = True
    elif not (snapshot.get("items") or []):
        try:
            attempts = int(snapshot.get("bootstrap_attempt_count") or 0)
        except (TypeError, ValueError):
            attempts = 0
        terminal = (
            attempts >= 3
            and snapshot.get("sync_status") in {
                "fetch_failed",
                "no_quarterly_consolidated_records_returned",
                "needs_manual_review_no_quarterly_data",
            }
        )
        status = "terminal_needs_manual_review" if terminal else "in_progress"
        complete_for_automation = terminal
    else:
        complete_for_automation = not (
            core_pending_periods
            or details_pending_periods
            or stale_detail_periods
            or statement_pages_pending
        )
        status = (
            "automated_processing_complete"
            if complete_for_automation
            else "in_progress"
        )

    manual_review_remaining = bool(
        isinstance(snapshot, dict)
        and (
            "manual_review" in str(snapshot.get("bootstrap_status") or "")
            or any(
                isinstance(item, dict)
                and (
                    "pending_visual_review" in str(item.get("verification_status") or "")
                    or str(item.get("verification_status") or "").startswith("manual_review")
                    or str(item.get("financial_line_items_status") or "") in DETAIL_REVIEW_STATUSES
                    or str(item.get("financial_line_items_status") or "").endswith("pending_visual_review")
                )
                for item in (snapshot.get("items") or [])
            )
        )
    )

    now = utc_now()
    states = checkpoint.get("symbolStates")
    if not isinstance(states, dict):
        states = {}
    progress_entry = {
        "status": status,
        "completeForAutomation": complete_for_automation,
        "manualReviewRemaining": manual_review_remaining,
        "periodCount": len(periods),
        "firstQuarter": periods[0] if periods else None,
        "lastQuarter": periods[-1] if periods else None,
        "pendingCorePeriods": core_pending_periods,
        "terminalManualReviewPeriods": terminal_manual_review_periods,
        "pendingDetailPeriods": details_pending_periods,
        "staleDetailSchemaPeriods": stale_detail_periods,
        "statementPagesPending": statement_pages_pending,
        "sourceArchivesChecked": len(checked_archives),
        "updatedAt": now,
        "snapshotFetchedAt": snapshot.get("fetchedAt") if isinstance(snapshot, dict) else None,
    }
    states[symbol] = progress_entry

    completed = checkpoint.get("completedSymbols")
    if not isinstance(completed, list):
        completed = []
    completed = [str(item).upper() for item in completed if isinstance(item, str)]
    if complete_for_automation:
        if symbol not in completed:
            completed.append(symbol)
    else:
        completed = [item for item in completed if item != symbol]

    changed_paths = [
        item.strip()
        for item in os.environ.get("REPORT_OCR_CHANGED_PATHS", "").splitlines()
        if item.strip()
    ]

    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "").strip()
    repository = os.environ.get("GITHUB_REPOSITORY", "kiemtimem123/so-lieu").strip()
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    run_url = f"{server_url}/{repository}/actions/runs/{run_id}" if run_id else None

    checkpoint.update({
        "schemaVersion": 1,
        "updatedAt": now,
        "processingMode": "one stock ticker at a time; one report per workflow run",
        "sourcePolicy": "VietstockFinance document catalog (doctype=1) and linked PDF/ZIP only",
        "periodStart": "2024-Q1",
        "quarterRetentionTarget": int(config.get("retentionQuarters") or 12),
        "completedSymbols": completed,
        "lastCompletedSymbol": symbol if complete_for_automation else checkpoint.get("lastCompletedSymbol"),
        "activeSymbol": None if complete_for_automation else symbol,
        "resumeSymbolHint": next_symbol_hint(symbols, symbol) if complete_for_automation else symbol,
        "resumeRule": "To resume safely, dispatch ocr-financial-reports.yml with symbol blank. It scans persisted snapshots and extraction sidecars in registry order. Do not delete data/financials-*.json or reports/raw/.",
        "lastProgress": {
            "symbol": symbol,
            "status": status,
            "completeForAutomation": complete_for_automation,
            "manualReviewRemaining": manual_review_remaining,
            "processedAt": now,
            "workflowRunId": run_id or None,
            "workflowRunNumber": int(run_number) if run_number.isdigit() else None,
            "workflowRunUrl": run_url,
            "changedPaths": changed_paths[:20],
            "periodCount": len(periods),
            "firstQuarter": periods[0] if periods else None,
            "lastQuarter": periods[-1] if periods else None,
            "pendingCorePeriods": core_pending_periods,
            "terminalManualReviewPeriods": terminal_manual_review_periods,
            "pendingDetailPeriods": details_pending_periods,
            "staleDetailSchemaPeriods": stale_detail_periods,
            "statementPagesPending": statement_pages_pending,
        },
        "symbolStates": states,
    })
    history = checkpoint.get("progressHistory")
    if not isinstance(history, list):
        history = []
    history.append({
        "symbol": symbol,
        "status": status,
        "completeForAutomation": complete_for_automation,
        "processedAt": now,
        "workflowRunId": run_id or None,
        "changedPaths": changed_paths[:10],
    })
    checkpoint["progressHistory"] = history[-50:]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = CHECKPOINT_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(CHECKPOINT_PATH)
    print(json.dumps({
        "symbol": symbol,
        "status": status,
        "complete_for_automation": complete_for_automation,
        "manual_review_remaining": manual_review_remaining,
        "period_count": len(periods),
        "pending_core_periods": core_pending_periods,
        "pending_detail_periods": details_pending_periods,
        "stale_detail_schema_periods": stale_detail_periods,
        "statement_pages_pending": statement_pages_pending,
        "resume_symbol_hint": checkpoint.get("resumeSymbolHint"),
        "checkpoint": str(CHECKPOINT_PATH.relative_to(ROOT)),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
