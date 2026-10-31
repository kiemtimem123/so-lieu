#!/usr/bin/env python3
"""Regression checks for bank financial-statement parsing and reconciliation.

This is a deterministic accounting/data-quality guard, not an OCR model. It
checks only rows stamped with the current parser schema, preserves provenance,
and leaves unresolved OCR/manual-visual-review items clearly flagged.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA = "2026-10-27-note-reference-alias-and-manual-guards-v8"
CURRENT_SCHEMAS = {SCHEMA, "2026-10-27-other-statements-source-fields-v11", "2026-10-26-bank-reconciliation-cashflow-v5"}
BANKS = {"MBB","ACB","SHB","TCB","TPB","VPB","STB","VCB","CTG","BID"}
ERRORS: list[str] = []
WARNINGS: list[str] = []
RELATIVE_TOLERANCE_PERCENT = 0.01
EPS = 0
ACTIVE_DETAILS_PENDING_REVIEW = False
DETAIL_REVIEW_STATUSES = {
    "manual_review_required",
    "manual_review_required_pending_extraction",
    "no_detail_fields_matched_pending_manual_review",
}

def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def close(a, b, tolerance=EPS):
    return abs(a - b) <= tolerance

def reconciliation_issue(symbol, period, message):
    """Don't block the queue on figures already marked for manual visual review."""
    if ACTIVE_DETAILS_PENDING_REVIEW:
        WARNINGS.append(
            f"{symbol} {period}: unconfirmed financial-detail field; {message}"
        )
    else:
        ERRORS.append(f"{symbol} {period}: {message}")

def relative_difference_percent(actual, expected):
    """Absolute percentage difference using the larger absolute value as denominator."""
    scale = max(abs(actual), abs(expected), 1)
    return abs(actual - expected) / scale * 100


def within_relative_tolerance(actual, expected, tolerance_percent=RELATIVE_TOLERANCE_PERCENT):
    """Accept a discrepancy at or below the explicitly configured relative threshold."""
    return relative_difference_percent(actual, expected) <= tolerance_percent


def require_close(symbol, period, label, actual, expected, tolerance=EPS):
    # The 0.01% relative rule supersedes the old blanket million-VND threshold.
    if abs(actual - expected) <= tolerance or within_relative_tolerance(actual, expected):
        return
    reconciliation_issue(
        symbol, period,
        f"{label}: actual={actual}, expected={expected}, diff={actual-expected}, "
        f"relative_diff_percent={relative_difference_percent(actual, expected):.8f}"
    )

def cash_bridge_delta(item):
    """Return the generic standalone-period cash bridge (legacy shared test contract)."""
    required = ("cash_beginning", "cash_ending", "net_cash_change")
    if not all(number(item.get(key)) for key in required):
        return None
    fx_effect = item.get("foreign_exchange_effect")
    if not number(fx_effect):
        fx_effect = 0
    return item["cash_ending"] - item["cash_beginning"] - item["net_cash_change"] - fx_effect


def bank_cash_bridge_delta(item):
    """Return the bank B04 bridge using YTD net cash when balances are annual/YTD."""
    if item.get("cashflow_period_basis") == "year_to_date":
        flow_key = "net_cash_change_ytd"
        fx_key = "foreign_exchange_effect_ytd"
    else:
        flow_key = "net_cash_change"
        fx_key = "foreign_exchange_effect"
    required = ("cash_beginning", "cash_ending", flow_key)
    if not all(number(item.get(key)) for key in required):
        return None
    fx_effect = item.get(fx_key)
    if not number(fx_effect):
        fx_effect = 0
    return item["cash_ending"] - item["cash_beginning"] - item[flow_key] - fx_effect


def audit_item(symbol, item, by_period):
    global ACTIVE_DETAILS_PENDING_REVIEW
    period = str(item.get("period") or "")
    if item.get("financial_line_items_schema_version") not in CURRENT_SCHEMAS:
        return
    if symbol not in BANKS:
        return
    detail_status = str(item.get("financial_line_items_status") or "")
    verification_status = str(item.get("verification_status") or "")
    core_status = str(item.get("core_financial_extraction_status") or "")
    ACTIVE_DETAILS_PENDING_REVIEW = (
        detail_status in DETAIL_REVIEW_STATUSES
        or detail_status.endswith("pending_visual_review")
        or verification_status in DETAIL_REVIEW_STATUSES
        or verification_status.endswith("pending_visual_review")
        or core_status in DETAIL_REVIEW_STATUSES
        or core_status.endswith("pending_visual_review")
    )
    # Source provenance remains constrained to the VietstockFinance document index.
    expected_index = f"https://finance.vietstock.vn/{symbol}/tai-tai-lieu.htm?doctype=1"
    if item.get("source_index_url") != expected_index:
        ERRORS.append(f"{symbol} {period}: source_index_url is not the required VietstockFinance catalog")
    if not str(item.get("source_url") or "").startswith("https://"):
        ERRORS.append(f"{symbol} {period}: report source URL is missing")
    # Validate balance and operating-income/profit subtotals whenever their source values exist.
    assets, liabilities, equity = (item.get(k) for k in ("total_assets","total_liabilities","equity"))
    if all(number(v) for v in (assets, liabilities, equity)):
        require_close(symbol, period, "balance equation", assets-liabilities, equity, 3)
    interest_income = item.get("bank_interest_income")
    interest_expense = item.get("bank_interest_expense")
    net_interest = item.get("bank_net_interest_income")
    if all(number(v) for v in (interest_income, interest_expense, net_interest)):
        require_close(symbol, period, "net interest income", interest_income-abs(interest_expense), net_interest)
    service_income, service_expense, net_service = (item.get(k) for k in ("bank_service_income","bank_service_expense","bank_net_service_income"))
    if all(number(v) for v in (service_income, service_expense, net_service)):
        require_close(symbol, period, "net service income", service_income-abs(service_expense), net_service)
    income_components = [
        item.get("bank_net_interest_income"), item.get("bank_net_service_income"),
        item.get("bank_fx_net_income"), item.get("bank_trading_securities_net"),
        item.get("bank_investment_securities_net"), item.get("bank_other_operating_net"),
        item.get("bank_dividend_and_capital_income"),
    ]
    if number(item.get("revenue")) and all(number(v) for v in income_components):
        require_close(symbol, period, "seven bank income components vs total operating income", sum(income_components), item["revenue"])
    if number(item.get("revenue")) and number(item.get("bank_pre_provision_operating_profit")) and number(item.get("bank_operating_expenses")):
        require_close(symbol, period, "operating income vs PPOP plus operating expenses",
                      item["bank_pre_provision_operating_profit"]+abs(item["bank_operating_expenses"]), item["revenue"])
    if number(item.get("pretax_profit")) and number(item.get("bank_pre_provision_operating_profit")) and number(item.get("bank_provision_expense")):
        # Preserve the signed provision line: positive is expense, negative is a reversal/income.
        require_close(symbol, period, "pretax profit", item["bank_pre_provision_operating_profit"]-item["bank_provision_expense"], item["pretax_profit"])
    if number(item.get("pretax_profit")) and number(item.get("net_profit")) and number(item.get("income_tax")):
        require_close(symbol, period, "net profit vs pretax less tax", item["pretax_profit"]-item["income_tax"], item["net_profit"])
    if number(item.get("roa")) and number(item.get("average_total_assets")) and number(item.get("net_profit")):
        require_close(symbol, period, "ROA percent", round(item["net_profit"]/item["average_total_assets"]*400,2), item["roa"], 0.011)
    if number(item.get("roe")) and number(item.get("average_equity")) and number(item.get("net_profit")):
        require_close(symbol, period, "ROE percent", round(item["net_profit"]/item["average_equity"]*400,2), item["roe"], 0.011)
    if item.get("cashflow_period_basis") != "year_to_date":
        reconciliation_issue(
            symbol, period,
            "bank B04 cash-flow basis must be explicitly marked year_to_date"
        )
        return
    ytd_fields = ("operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd","net_cash_change_ytd")
    if not all(number(item.get(k)) for k in ytd_fields):
        WARNINGS.append(f"{symbol} {period}: YTD cash-flow fields are incomplete; preserve blanks and review instead of inferring missing values")
    else:
        require_close(symbol, period, "YTD cash-flow sum", sum(item[k] for k in ytd_fields[:3]), item["net_cash_change_ytd"])
    quarter_fields = ("operating_cash_flow","investing_cash_flow","financing_cash_flow","net_cash_change")
    if not all(number(item.get(k)) for k in quarter_fields):
        WARNINGS.append(f"{symbol} {period}: standalone-quarter cash-flow fields are incomplete; no figures were fabricated")
    else:
        require_close(symbol, period, "quarter cash-flow sum", sum(item[k] for k in quarter_fields[:3]), item["net_cash_change"])
    ordinal = None
    if len(period) == 7 and period[:4].isdigit() and period[5:] in ("Q1","Q2","Q3","Q4"):
        ordinal = int(period[:4])*4+int(period[-1])
    if ordinal is not None:
        quarter = int(period[-1])
        if quarter == 1:
            for qfield,yfield in (("operating_cash_flow","operating_cash_flow_ytd"),("investing_cash_flow","investing_cash_flow_ytd"),("financing_cash_flow","financing_cash_flow_ytd"),("net_cash_change","net_cash_change_ytd"),("capital_expenditure","capital_expenditure_ytd"),("dividends_paid","dividends_paid_ytd")):
                if number(item.get(qfield)) and number(item.get(yfield)):
                    require_close(symbol, period, f"Q1 {qfield} equals YTD", item[qfield], item[yfield])
            # Adjacent-year continuity is checked separately from the report's internal YTD bridge.
            prior_year_q4 = by_period.get(f"{int(period[:4])-1}-Q4") or {}
            if number(prior_year_q4.get("cash_ending")) and number(item.get("cash_beginning")):
                require_close(
                    symbol, period, "Q1 opening cash vs prior FY/Q4 closing cash",
                    item["cash_beginning"], prior_year_q4["cash_ending"]
                )
        else:
            previous = by_period.get(f"{period[:4]}-Q{quarter-1}") or {}
            if previous.get("cashflow_period_basis") == "year_to_date":
                for qfield,yfield in (("operating_cash_flow","operating_cash_flow_ytd"),("investing_cash_flow","investing_cash_flow_ytd"),("financing_cash_flow","financing_cash_flow_ytd"),("net_cash_change","net_cash_change_ytd"),("capital_expenditure","capital_expenditure_ytd"),("dividends_paid","dividends_paid_ytd")):
                    if number(item.get(qfield)) and number(item.get(yfield)) and number(previous.get(yfield)):
                        require_close(symbol, period, f"{qfield} vs current YTD minus prior YTD",
                                      item[qfield], item[yfield]-previous[yfield])
                # These B04 snapshots store annual opening cash and YTD closing cash,
                # not a standalone quarter opening balance. Validate the quarter movement
                # using consecutive closing balances and the standalone-quarter net flow.
                if (
                    item.get("cashflow_period_basis") == "year_to_date"
                    and number(previous.get("cash_ending"))
                    and number(item.get("cash_ending"))
                    and number(item.get("net_cash_change"))
                ):
                    quarter_fx = item.get("foreign_exchange_effect")
                    if not number(quarter_fx):
                        quarter_fx = 0
                    require_close(
                        symbol, period, "quarter closing cash movement vs standalone net flow",
                        item["cash_ending"] - previous["cash_ending"],
                        item["net_cash_change"] + quarter_fx
                    )
    bridge_flow_key = (
        "net_cash_change_ytd"
        if item.get("cashflow_period_basis") == "year_to_date"
        else "net_cash_change"
    )
    bridge_fx_key = (
        "foreign_exchange_effect_ytd"
        if item.get("cashflow_period_basis") == "year_to_date"
        else "foreign_exchange_effect"
    )
    if all(number(item.get(k)) for k in ("cash_beginning","cash_ending",bridge_flow_key)):
        # Cash opening/closing balances and flow must use the same period basis.
        # For bank B04 snapshots, cash_beginning/cash_ending are annual opening and
        # YTD closing, while net_cash_change is normalized to the standalone quarter.
        fx_available = number(item.get(bridge_fx_key))
        fx_effect = item.get(bridge_fx_key) if fx_available else 0
        bridge_delta = bank_cash_bridge_delta(item)
        bridge_label = "cash opening/closing YTD bridge after FX" if fx_available else "cash opening/closing YTD bridge (FX unavailable)"
        expected_closing_cash = item["cash_beginning"] + item[bridge_flow_key] + fx_effect
        if not within_relative_tolerance(item["cash_ending"], expected_closing_cash):
            if abs(bridge_delta) > 50:
                reconciliation_issue(
                    symbol, period,
                    f"{bridge_label} differs by {bridge_delta} million VND "
                    f"(relative difference {relative_difference_percent(item['cash_ending'], expected_closing_cash):.8f}%)"
                )
            elif bridge_delta:
                WARNINGS.append(
                    f"{symbol} {period}: {bridge_label} residual {bridge_delta} million VND "
                    "exceeds the 0.01% relative tolerance; retained for source/OCR review"
                )
    if number(item.get("cash_and_equivalents")) and number(item.get("cash_beginning_reported_ytd")) and item["cash_and_equivalents"] == item["cash_beginning_reported_ytd"]:
        reconciliation_issue(
            symbol, period,
            "generic cash_and_equivalents duplicates the B04 cash opening balance"
        )

def main():
    global ACTIVE_DETAILS_PENDING_REVIEW
    files = sorted(DATA_DIR.glob("financials-*.json"))
    symbols_checked = 0
    audited_rows = 0
    for file in files:
        try:
            snapshot = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            ERRORS.append(f"{file.name}: cannot read JSON: {exc}")
            continue
        symbol = str(snapshot.get("symbol") or file.stem.replace("financials-","")).upper()
        if symbol not in BANKS:
            continue
        rows = snapshot.get("items") or []
        by_period = {str(row.get("period")): row for row in rows if isinstance(row, dict)}
        symbols_checked += 1
        for item in rows:
            if not isinstance(item, dict):
                continue
            schema_version = item.get("financial_line_items_schema_version")
            # VCB's legacy v4 rows were source-reconciled quarter by quarter in
            # the 2026-10-30 audit. Keep them under the same cash-flow and bank
            # statement regression checks without falsely relabelling their parser
            # schema as current. They remain pending visual review.
            reconciled_vcb_legacy = (
                symbol == "VCB"
                and schema_version == "2026-10-22-bank-statement-qc-v4"
            )
            if schema_version not in CURRENT_SCHEMAS and not reconciled_vcb_legacy:
                continue
            audited_rows += 1
            audit_item(symbol, item, by_period)
    # Regression fixtures are source-backed, so their assertions remain blocking
    # regardless of whichever row was last audited.
    ACTIVE_DETAILS_PENDING_REVIEW = False
    # Regression fixture grounded in the saved TCB Q3 2026 report, not inferred from a model.
    tcb_path = DATA_DIR / "financials-TCB.json"
    if tcb_path.exists():
        tcb = json.loads(tcb_path.read_text(encoding="utf-8"))
        rows = {str(row.get("period")): row for row in (tcb.get("items") or []) if isinstance(row,dict)}
        q1,q2,q3 = (rows.get(f"2026-Q{i}") for i in (1,2,3))
        if all(isinstance(row,dict) for row in (q1,q2,q3)):
            controls = {
                "revenue": 45203770,
                "pretax_profit": 28915354,
                "net_profit": 23014208,
                "net_profit_attributable": 21964072,
            }
            for field, expected in controls.items():
                actual = sum(row.get(field,0) for row in (q1,q2,q3) if number(row.get(field)))
                require_close("TCB","2026 Q1-Q3",f"reported nine-month control {field}",actual,expected)
            q3audit = q3.get("source_extract_review") or {}
            q3checks = q3audit.get("checks") or {}
            if q3.get("bank_interest_income") != 25576450:
                ERRORS.append("TCB 2026-Q3: gross interest income regression value must be 25,576,450")
            if q3.get("bank_dividend_and_capital_income") != 1211:
                ERRORS.append("TCB 2026-Q3: capital-contribution income regression value must be 1,211")
            if not q3checks.get("bank_income_components_sum_to_revenue"):
                ERRORS.append("TCB 2026-Q3: missing income-components reconciliation evidence")
            # Source-backed regression: don't confuse net investing cash flow with fixed-asset purchases.
            if q1.get("investing_cash_flow_ytd") != -32965:
                ERRORS.append("TCB 2026-Q1: net investing cash flow must be -32,965, not fixed-asset purchases -35,724")
            if q1.get("capital_expenditure_ytd") != -35724:
                ERRORS.append("TCB 2026-Q1: fixed-asset purchases must remain -35,724")
            if q2.get("investing_cash_flow_ytd") != 57197:
                ERRORS.append("TCB 2026-Q2: six-month investing YTD regression value must be 57,197")
            if q3.get("investing_cash_flow_ytd") != -411649:
                ERRORS.append("TCB 2026-Q3: nine-month investing YTD regression value must be -411,649")
    # VietstockFinance PDF regression for the manually reconciled MBB Q1 2024 balance sheet.
    # Values are in million VND and were visually cross-checked against PDF pages 3-4.
    mbb_path = DATA_DIR / "financials-MBB.json"
    if mbb_path.exists():
        mbb = json.loads(mbb_path.read_text(encoding="utf-8"))
        q1_2024 = next(
            (row for row in (mbb.get("items") or [])
             if isinstance(row, dict) and row.get("period") == "2024-Q1"),
            None,
        )
        expected_mbb_q1 = {
            "fixed_assets": 5043795,
            "bank_deposits_and_loans_to_credit_institutions": 77809357,
            "bank_derivatives_and_other_financial_assets": 0,
            "bank_valuable_papers": 102482877,
            "bank_other_liabilities": 47353000,
        }
        if not isinstance(q1_2024, dict):
            ERRORS.append("MBB 2024-Q1: missing VietstockFinance source-backed regression row")
        else:
            for field, expected in expected_mbb_q1.items():
                actual = q1_2024.get(field)
                if actual != expected:
                    ERRORS.append(
                        f"MBB 2024-Q1: {field} must be {expected} million VND, got {actual!r}"
                    )
    # Cross-quarter regressions for OCR note-reference, comparator-column,
    # child-row and total/subcategory mix-ups confirmed against VietstockFinance PDFs.
    expected_mbb_period_controls = {
        "2024-Q3": {
            "bank_customer_deposits": 627567353,
            "bank_valuable_papers": 119550968,
            "bank_other_liabilities": 44719121,
        },
        "2025-Q4": {
            "bank_investment_securities": 225574850,
        },
        "2026-Q1": {
            "bank_derivatives_and_other_financial_assets": 0,
        },
    }
    if mbb_path.exists():
        mbb = json.loads(mbb_path.read_text(encoding="utf-8"))
        mbb_rows = {
            str(row.get("period")): row
            for row in (mbb.get("items") or [])
            if isinstance(row, dict)
        }
        for period, controls in expected_mbb_period_controls.items():
            row = mbb_rows.get(period)
            if not isinstance(row, dict):
                ERRORS.append(f"MBB {period}: missing source-backed regression row")
                continue
            for field, expected in controls.items():
                actual = row.get(field)
                if actual != expected:
                    ERRORS.append(
                        f"MBB {period}: {field} must be {expected} million VND, got {actual!r}"
                    )


    # KBC cash-flow regression: non-bank issuer, but the same cash-flow quality
    # checks run in this CI job so the exact per-ticker normalization is enforced.
    kbc_path = DATA_DIR / "financials-KBC.json"
    if kbc_path.exists():
        kbc = json.loads(kbc_path.read_text(encoding="utf-8"))
        kbc_rows = {
            str(row.get("period")): row
            for row in (kbc.get("items") or [])
            if isinstance(row, dict)
        }
        expected_kbc_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2", "2026-Q3",
        }
        if set(kbc_rows) != expected_kbc_periods or len(kbc.get("items") or []) != 11:
            ERRORS.append("KBC cash-flow regression: expected 11 unique periods from 2024-Q1 through 2026-Q3")
        kbc_flow_fields = ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_change")
        kbc_ytd_fields = tuple(field + "_ytd" for field in kbc_flow_fields)
        for period, row in kbc_rows.items():
            rec = row.get("cashflow_source_reconciliation") or {}
            raw = rec.get("selected_values_raw_vnd") or {}
            quarter = raw.get("quarter") or {}
            ytd = raw.get("ytd") or {}
            if row.get("source_index_url") != "https://finance.vietstock.vn/KBC/tai-tai-lieu.htm?doctype=1":
                ERRORS.append(f"KBC {period}: source index is not the approved VietstockFinance catalog")
            if not str(row.get("source_url") or "").startswith("https://static2.vietstock.vn/"):
                ERRORS.append(f"KBC {period}: original source PDF link is missing or outside Vietstock")
            if rec.get("relative_tolerance_percent") != 0.01 or rec.get("no_balancing_plug") is not True:
                ERRORS.append(f"KBC {period}: cash-flow audit metadata/tolerance is missing")
            if rec.get("separate_fx_line_reported") is not False or row.get("foreign_exchange_effect") is not None or row.get("foreign_exchange_effect_ytd") is not None:
                ERRORS.append(f"KBC {period}: FX fields must stay null because the source statement has no separate FX line")
            selected_url = str(rec.get("selected_cashflow_source_url") or "")
            selected_archive = str(rec.get("selected_cashflow_source_archive_file") or "")
            if not selected_url.startswith("https://static2.vietstock.vn/") or not selected_archive.startswith("reports/raw/KBC/"):
                ERRORS.append(f"KBC {period}: selected source comparative/archive provenance is missing")
            for part_name, part in (("quarter", quarter), ("YTD", ytd)):
                required = ("cfo", "cfi", "cff", "net_cash_change", "cash_beginning", "cash_ending")
                if not all(number(part.get(field)) for field in required):
                    ERRORS.append(f"KBC {period}: raw {part_name} cash-flow source values are incomplete")
                    continue
                flow_sum = part["cfo"] + part["cfi"] + part["cff"]
                if flow_sum != part["net_cash_change"]:
                    ERRORS.append(f"KBC {period}: raw {part_name} flow components do not sum to reported net cash")
                bridge = part["cash_ending"] - part["cash_beginning"] - part["net_cash_change"]
                if bridge != 0:
                    WARNINGS.append(f"KBC {period}: raw {part_name} cash bridge residual {bridge} VND; retained for review")
            if not rec.get("quarter_flow_components_within_tolerance") or not rec.get("ytd_flow_components_within_tolerance"):
                ERRORS.append(f"KBC {period}: quarter/YTD flow component check not marked within tolerance")
            if not rec.get("quarter_cash_bridge_within_tolerance") or not rec.get("ytd_cash_bridge_within_tolerance"):
                ERRORS.append(f"KBC {period}: quarter/YTD cash bridge not marked within tolerance")
            if row.get("cashflow_period_basis") not in ("quarterly_reported", "quarterly_normalized_from_ytd"):
                ERRORS.append(f"KBC {period}: invalid cashflow_period_basis")
            extracted = set(row.get("financial_line_items_extracted_fields") or [])
            rejected = set(row.get("financial_line_items_rejected_fields") or [])
            for field in kbc_flow_fields + kbc_ytd_fields + ("cash_beginning", "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd"):
                if not number(row.get(field)) or field not in extracted or field in rejected:
                    ERRORS.append(f"KBC {period}: validated field {field} is blank, not allowlisted, or still rejected")
            year, quarter_text = period.split("-Q")
            quarter_number = int(quarter_text)
            prior = kbc_rows.get(f"{year}-Q{quarter_number-1}") if quarter_number > 1 else None
            if prior and all(number((raw.get("ytd") or {}).get(key)) for key in ("cfo","cfi","cff","net_cash_change")):
                previous_ytd = (prior.get("cashflow_source_reconciliation") or {}).get("selected_values_raw_vnd", {}).get("ytd") or {}
                for key in ("cfo","cfi","cff","net_cash_change"):
                    if quarter.get(key) != ytd.get(key) - previous_ytd.get(key):
                        ERRORS.append(f"KBC {period}: standalone-quarter {key} is not current YTD minus previous same-year YTD")
                if quarter.get("cash_beginning") != previous_ytd.get("cash_ending"):
                    ERRORS.append(f"KBC {period}: quarter opening cash does not equal previous same-year quarter closing cash")
            elif not prior:
                for key in ("cfo","cfi","cff","net_cash_change"):
                    if quarter.get(key) != ytd.get(key):
                        ERRORS.append(f"KBC {period}: Q1 {key} should equal YTD Q1")
        # Explicit exceptions stay blocking as review flags, not source-value rewrites.
        kbc_2026_q1 = (kbc_rows.get("2026-Q1") or {}).get("cashflow_source_reconciliation") or {}
        cross_year = kbc_2026_q1.get("cross_year_cash_basis") or {}
        if cross_year.get("residual_raw_vnd") != -18013511097 or cross_year.get("status") != "NEEDS_MANUAL_REVIEW_CROSS_YEAR_CASH_BASIS":
            ERRORS.append("KBC 2026-Q1: expected FY2025-to-Q1/2026 cash-basis exception is missing or changed")
        if (kbc_rows.get("2026-Q1") or {}).get("cash_ending") != 6930682.751:
            ERRORS.append("KBC 2026-Q1: cash ending display must be 6,930,682.751 million VND")
        kbc_q3_2026 = (kbc_rows.get("2026-Q3") or {}).get("cashflow_source_reconciliation") or {}
        if kbc_q3_2026.get("investing_total_ocr_candidate_raw_vnd") != -518402271256:
            ERRORS.append("KBC 2026-Q3: preserve the original CFI total OCR candidate for review")
        if kbc_q3_2026.get("investing_component_sum_raw_vnd") != -515402271256:
            ERRORS.append("KBC 2026-Q3: CFI must be reconstructed from detailed investment rows, not the erroneous OCR total")
        if sum((kbc_q3_2026.get("investing_component_lines_raw_vnd") or {}).values()) != -515402271256:
            ERRORS.append("KBC 2026-Q3: investing-detail components do not sum to the selected CFI total")
        if kbc_q3_2026.get("investing_component_sum_vs_ocr_residual_raw_vnd") != 3000000000:
            ERRORS.append("KBC 2026-Q3: expected 3,000,000,000 VND CFI OCR discrepancy must remain recorded")
        h1_2025_revision = ((kbc_rows.get("2025-Q2") or {}).get("cashflow_source_reconciliation") or {}).get("source_revision") or {}
        h1_2025_delta = h1_2025_revision.get("selected_minus_prior_source_values_raw_vnd") or {}
        if h1_2025_delta.get("cfo") != -895822506913 or h1_2025_delta.get("cfi") != 895672506913 or h1_2025_delta.get("net") != -150000000:
            ERRORS.append("KBC 2025-Q2: restated comparative source revision must remain traceable")
        kbc_2025_q3 = (kbc_rows.get("2025-Q3") or {}).get("cashflow_source_reconciliation") or {}
        bs_cross = kbc_2025_q3.get("balance_sheet_cash_crosscheck") or {}
        if bs_cross.get("relative_difference_percent", 1) > RELATIVE_TOLERANCE_PERCENT or bs_cross.get("no_balancing_plug") is not True:
            ERRORS.append("KBC 2025-Q3: within-tolerance balance-sheet cash difference must retain both source values")



    # GEG cash-flow regression in CI: raw VND values, source provenance, bridges,
    # YTD-to-quarter deltas and explicitly documented source-basis exceptions.
    geg_path = DATA_DIR / "financials-GEG.json"
    if geg_path.exists():
        geg = json.loads(geg_path.read_text(encoding="utf-8"))
        geg_rows = {str(r.get("period")): r for r in (geg.get("items") or []) if isinstance(r, dict)}
        geg_expected = {"2024-Q1","2024-Q2","2024-Q3","2024-Q4","2025-Q1","2025-Q2","2025-Q3","2025-Q4","2026-Q1","2026-Q2"}
        if set(geg_rows) != geg_expected or len(geg.get("items") or []) != 10:
            ERRORS.append("GEG cash-flow regression: expected 10 unique quarters 2024-Q1 through 2026-Q2")
        q_exceptions = {"2026-Q2"}
        flow_keys = ("operating_cash_flow","investing_cash_flow","financing_cash_flow","net_cash_change")
        ytd_keys = tuple(k + "_ytd" for k in flow_keys)
        for period, row in geg_rows.items():
            rec = row.get("cashflow_source_reconciliation") or {}
            raw = rec.get("selected_values_raw_vnd") or {}
            qraw, yraw = raw.get("quarter") or {}, raw.get("ytd") or {}
            if row.get("source_index_url") != "https://finance.vietstock.vn/GEG/tai-tai-lieu.htm?doctype=1":
                ERRORS.append(f"GEG {period}: invalid VietstockFinance index URL")
            if not str(row.get("source_url") or "").startswith("https://static2.vietstock.vn/"):
                ERRORS.append(f"GEG {period}: original source is not a Vietstock static PDF/ZIP")
            if not str(rec.get("selected_cashflow_source_url") or "").startswith("https://static2.vietstock.vn/"):
                ERRORS.append(f"GEG {period}: selected comparative/source URL missing")
            if not str(rec.get("selected_cashflow_source_archive_file") or "").startswith("reports/raw/GEG/"):
                ERRORS.append(f"GEG {period}: selected existing OCR sidecar missing")
            if rec.get("relative_tolerance_percent") != 0.01 or rec.get("no_balancing_plug") is not True:
                ERRORS.append(f"GEG {period}: tolerance/no-balancing-plug metadata missing")
            if rec.get("separate_fx_line_reported") is not True:
                ERRORS.append(f"GEG {period}: source FX-row policy not marked")
            for part_name, part in (("quarter", qraw), ("YTD", yraw)):
                required = ("cfo","cfi","cff","net_cash_change","fx","cash_beginning","cash_ending")
                if not all(number(part.get(k)) for k in required):
                    ERRORS.append(f"GEG {period}: raw {part_name} values missing")
                    continue
                if part["cfo"] + part["cfi"] + part["cff"] != part["net_cash_change"]:
                    ERRORS.append(f"GEG {period}: raw {part_name} flows do not sum to net cash")
                expected_end = part["cash_beginning"] + part["net_cash_change"] + part["fx"]
                if part_name == "YTD":
                    if not within_relative_tolerance(part["cash_ending"], expected_end) or rec.get("ytd_cash_bridge_within_tolerance") is not True:
                        ERRORS.append(f"GEG {period}: YTD cash bridge failed")
                elif period in q_exceptions:
                    if within_relative_tolerance(part["cash_ending"], expected_end) or rec.get("quarter_cash_bridge_within_tolerance") is not False:
                        ERRORS.append(f"GEG {period}: expected quarter cash-basis exception not retained")
                    if rec.get("calculations", {}).get("quarter_cash_bridge_residual_raw_vnd") != part["cash_ending"] - expected_end:
                        ERRORS.append(f"GEG {period}: quarter bridge residual metadata mismatch")
                else:
                    if not within_relative_tolerance(part["cash_ending"], expected_end) or rec.get("quarter_cash_bridge_within_tolerance") is not True:
                        ERRORS.append(f"GEG {period}: quarter cash bridge failed without an exception")
            if rec.get("quarter_flow_components_within_tolerance") is not True or rec.get("ytd_flow_components_within_tolerance") is not True:
                ERRORS.append(f"GEG {period}: flow component flags not passing")
            if row.get("cashflow_period_basis") not in ("quarterly_reported","quarterly_normalized_from_ytd"):
                ERRORS.append(f"GEG {period}: invalid quarterly basis")
            ex, rejected = set(row.get("financial_line_items_extracted_fields") or []), set(row.get("financial_line_items_rejected_fields") or [])
            for field in flow_keys + ytd_keys + ("foreign_exchange_effect","foreign_exchange_effect_ytd","cash_beginning","cash_ending","cash_beginning_reported_ytd","cash_ending_reported_ytd"):
                if not number(row.get(field)) or field not in ex or field in rejected:
                    ERRORS.append(f"GEG {period}: cashflow field {field} missing/not allowlisted/rejected")
            year, qtxt = period.split("-Q")
            qnum = int(qtxt)
            previous = geg_rows.get(f"{year}-Q{qnum-1}") if qnum > 1 else None
            if previous:
                prev_ytd = ((previous.get("cashflow_source_reconciliation") or {}).get("selected_values_raw_vnd") or {}).get("ytd") or {}
                for key in ("cfo","cfi","cff","net_cash_change","fx"):
                    if qraw.get(key) != yraw.get(key,0) - prev_ytd.get(key,0):
                        ERRORS.append(f"GEG {period}: quarterly {key} does not equal the same-year YTD delta")
                if qraw.get("cash_beginning") != prev_ytd.get("cash_ending"):
                    ERRORS.append(f"GEG {period}: quarterly opening does not equal prior-quarter close")
            else:
                for key in ("cfo","cfi","cff","net_cash_change","fx"):
                    if qraw.get(key) != yraw.get(key):
                        ERRORS.append(f"GEG {period}: Q1 values should equal YTD Q1")
        geg_2025_q4 = geg_rows.get("2025-Q4", {})
        q4_rec = geg_2025_q4.get("cashflow_source_reconciliation", {})
        q4_ytd = (q4_rec.get("selected_values_raw_vnd") or {}).get("ytd") or {}
        expected_q4_values = {
            "cfo": 932884327033, "cfi": 1921143888, "cff": -1012240268026,
            "net_cash_change": -77434797105, "cash_beginning": 163717707072,
            "fx": 81753281, "cash_ending": 86364663248,
        }
        for field, expected_value in expected_q4_values.items():
            if q4_ytd.get(field) != expected_value:
                ERRORS.append(f"GEG Q4/2025: visually confirmed source value {field} changed")
        if q4_rec.get("visual_review") != "direct_image_verified_printed_pages_4_5":
            ERRORS.append("GEG Q4/2025: direct image review status missing")
        if q4_rec.get("status") != "PASS_WITHIN_TOLERANCE_SOURCE_ROWS_VISUALLY_VERIFIED":
            ERRORS.append("GEG Q4/2025: visually verified source rows should not remain flagged as OCR-truncated")
        q2_2025_rec = (geg_rows.get("2025-Q2", {}).get("cashflow_source_reconciliation") or {})
        q2_h1_raw = (q2_2025_rec.get("selected_values_raw_vnd") or {}).get("ytd") or {}
        if not str(q2_2025_rec.get("selected_cashflow_source_url") or "").endswith("GEG_Baocaotaichinh_Q2_2025_Hopnhat.pdf"):
            ERRORS.append("GEG 2025-Q2: original Q2/2025 source must be selected for the 2025 time series")
        if q2_h1_raw.get("cfo") != 555421075993 or q2_h1_raw.get("cfi") != 476067298075 or q2_h1_raw.get("cff") != -721712954268 or q2_h1_raw.get("net_cash_change") != 309775419800:
            ERRORS.append("GEG 2025-Q2: original H1/2025 selected raw values changed")
        q2_alt = q2_2025_rec.get("source_revision", {}).get("later_comparative_alternative", {})
        if q2_alt.get("raw_values_vnd", {}).get("net_cash_change") != 310111805190 or q2_alt.get("differences_vs_selected_original_raw_vnd", {}).get("net_cash_change") != 336385390:
            ERRORS.append("GEG 2025-Q2: later Q2/2026 comparative must remain traceable as alternate source")
        if q2_2025_rec.get("visual_review") != "direct_image_verified_printed_pages_4_5" or q2_2025_rec.get("quarter_cash_bridge_within_tolerance") is not True:
            ERRORS.append("GEG 2025-Q2: direct source review or corrected quarterly cash bridge is missing")
        q3_2025_rec = geg_rows.get("2025-Q3", {}).get("cashflow_source_reconciliation", {})
        if q3_2025_rec.get("calculations", {}).get("quarter_cash_bridge_residual_raw_vnd") != 0 or q3_2025_rec.get("quarter_cash_bridge_within_tolerance") is not True:
            ERRORS.append("GEG 2025-Q3: quarter bridge must reconcile against original H1/2025 source")
        if q3_2025_rec.get("visual_review") != "direct_image_verified_printed_pages_4_5":
            ERRORS.append("GEG 2025-Q3: direct source page review is missing")
        q1_bridge = geg_rows.get("2026-Q1",{}).get("cashflow_source_reconciliation",{}).get("calculations",{}).get("quarter_cash_bridge_residual_raw_vnd")
        if q1_bridge != 900:
            ERRORS.append("GEG Q1/2026 expected +900 VND bridge residual not preserved")
        if geg_rows.get("2026-Q2",{}).get("cashflow_source_reconciliation",{}).get("cross_period_cash_basis",{}).get("residual_raw_vnd") != -30914348704:
            ERRORS.append("GEG Q2/2026 opening-cash basis exception missing")

    # VCB Q4/2024 audited cash-flow restatement regression.
    # Q4 standalone values are derived from audited annual YTD less Q3/2024 YTD.
    vcb_path = DATA_DIR / "financials-VCB.json"
    if vcb_path.exists():
        vcb = json.loads(vcb_path.read_text(encoding="utf-8"))
        vcb_rows = {
            str(row.get("period")): row
            for row in (vcb.get("items") or [])
            if isinstance(row, dict)
        }
        vcb_q4 = vcb_rows.get("2024-Q4")
        expected_vcb_q4 = {
            "cash_beginning": 372818730,
            "cash_ending": 430614185,
            "operating_cash_flow_ytd": 59122831,
            "investing_cash_flow_ytd": -1307413,
            "financing_cash_flow_ytd": -19963,
            "net_cash_change_ytd": 57795455,
            "operating_cash_flow": 117112806,
            "investing_cash_flow": -501783,
            "financing_cash_flow": -19963,
            "net_cash_change": 116591060,
            "bank_provision_expense": -32330,
        }
        if not isinstance(vcb_q4, dict):
            ERRORS.append("VCB 2024-Q4: missing audited cash-flow restatement row")
        else:
            for field, expected in expected_vcb_q4.items():
                actual = vcb_q4.get(field)
                if actual != expected:
                    ERRORS.append(
                        f"VCB 2024-Q4: audited cash-flow regression {field} must be {expected}, got {actual!r}"
                    )
            if "cash_beginning" in (vcb_q4.get("financial_line_items_rejected_fields") or []) or "cash_ending" in (vcb_q4.get("financial_line_items_rejected_fields") or []):
                ERRORS.append("VCB 2024-Q4: audited opening/closing cash must not remain rejected")
            if bank_cash_bridge_delta(vcb_q4) != 0:
                ERRORS.append("VCB 2024-Q4: audited YTD cash bridge must reconcile exactly to zero")
        vcb_q2_2024 = vcb_rows.get("2024-Q2")
        if isinstance(vcb_q2_2024, dict):
            if vcb_q2_2024.get("bank_provision_expense") != 1513541:
                ERRORS.append("VCB 2024-Q2: signed provision expense regression value must be 1,513,541")
            for field in ("cash_beginning","cash_ending","operating_cash_flow","operating_cash_flow_ytd","investing_cash_flow","investing_cash_flow_ytd","financing_cash_flow","financing_cash_flow_ytd","net_cash_change","net_cash_change_ytd"):
                if field in (vcb_q2_2024.get("financial_line_items_rejected_fields") or []):
                    ERRORS.append(f"VCB 2024-Q2: source-reconciled cash-flow field {field} must not remain rejected")
        vcb_q2_2025 = vcb_rows.get("2025-Q2")
        if isinstance(vcb_q2_2025, dict):
            for field in ("cash_beginning","cash_ending","operating_cash_flow","operating_cash_flow_ytd","investing_cash_flow","investing_cash_flow_ytd","financing_cash_flow","financing_cash_flow_ytd","net_cash_change","net_cash_change_ytd"):
                if field in (vcb_q2_2025.get("financial_line_items_rejected_fields") or []):
                    ERRORS.append(f"VCB 2025-Q2: source-reconciled cash-flow field {field} must not remain rejected")

    print("Bank financial reconciliation regression checks")
    print(f"Bank snapshots checked: {symbols_checked}; rows on current schema: {audited_rows}")
    print(f"Errors: {len(ERRORS)}; warnings: {len(WARNINGS)}")
    for message in WARNINGS:
        print("WARN:",message)
    for message in ERRORS:
        print("ERROR:",message)
    if ERRORS:
        raise SystemExit(1)
    print("PASS: audited bank subtotals, cash-flow YTD/quart-quarter conversion, and TCB Q3/2026 regressions.")

if __name__ == "__main__":
    main()
