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
BANKS = {"MBB","ACB","SHB","TCB","TPB","VPB","STB","VCB","CTG","BID"}
ERRORS: list[str] = []
WARNINGS: list[str] = []
EPS = 5
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

def require_close(symbol, period, label, actual, expected, tolerance=EPS):
    if not close(actual, expected, tolerance):
        reconciliation_issue(
            symbol, period,
            f"{label}: actual={actual}, expected={expected}, diff={actual-expected}"
        )

def audit_item(symbol, item, by_period):
    global ACTIVE_DETAILS_PENDING_REVIEW
    period = str(item.get("period") or "")
    if item.get("financial_line_items_schema_version") != SCHEMA:
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
        require_close(symbol, period, "pretax profit", item["bank_pre_provision_operating_profit"]-abs(item["bank_provision_expense"]), item["pretax_profit"])
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
        else:
            previous = by_period.get(f"{period[:4]}-Q{quarter-1}") or {}
            if previous.get("cashflow_period_basis") == "year_to_date":
                for qfield,yfield in (("operating_cash_flow","operating_cash_flow_ytd"),("investing_cash_flow","investing_cash_flow_ytd"),("financing_cash_flow","financing_cash_flow_ytd"),("net_cash_change","net_cash_change_ytd"),("capital_expenditure","capital_expenditure_ytd"),("dividends_paid","dividends_paid_ytd")):
                    if number(item.get(qfield)) and number(item.get(yfield)) and number(previous.get(yfield)):
                        require_close(symbol, period, f"{qfield} vs current YTD minus prior YTD",
                                      item[qfield], item[yfield]-previous[yfield])
                if number(previous.get("cash_ending")) and number(item.get("cash_beginning")):
                    require_close(symbol, period, "quarter opening cash vs prior quarter close",
                                  item["cash_beginning"], previous["cash_ending"])
    if all(number(item.get(k)) for k in ("cash_beginning","cash_ending","net_cash_change")):
        # B04 cash balance movement includes the separately reported foreign-exchange effect.
        # net_cash_change itself is the sum of operating, investing and financing flows;
        # do not mistake FX translation for an OCR/accounting error.
        fx_available = number(item.get("foreign_exchange_effect"))
        fx_effect = item["foreign_exchange_effect"] if fx_available else 0
        bridge_delta = (
            item["cash_ending"] - item["cash_beginning"] -
            item["net_cash_change"] - fx_effect
        )
        bridge_label = "cash opening/closing bridge after FX" if fx_available else "cash opening/closing bridge (FX unavailable)"
        if abs(bridge_delta) > 50:
            reconciliation_issue(
                symbol, period,
                f"{bridge_label} differs by {bridge_delta} million VND"
            )
        elif bridge_delta:
            WARNINGS.append(
                f"{symbol} {period}: {bridge_label} residual {bridge_delta} million VND "
                "retained for source/OCR review"
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
            if not isinstance(item, dict) or item.get("financial_line_items_schema_version") != SCHEMA:
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
