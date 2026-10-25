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
SCHEMA = "2026-10-26-bank-reconciliation-cashflow-v5"
BANKS = {"MBB","ACB","SHB","TCB","TPB","VPB","STB","VCB","CTG","BID"}
ERRORS: list[str] = []
WARNINGS: list[str] = []
EPS = 5

def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def close(a, b, tolerance=EPS):
    return abs(a - b) <= tolerance

def require_close(symbol, period, label, actual, expected, tolerance=EPS):
    if not close(actual, expected, tolerance):
        ERRORS.append(f"{symbol} {period}: {label}: actual={actual}, expected={expected}, diff={actual-expected}")

def audit_item(symbol, item, by_period):
    period = str(item.get("period") or "")
    if item.get("financial_line_items_schema_version") != SCHEMA:
        return
    if symbol not in BANKS:
        return
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
        ERRORS.append(f"{symbol} {period}: bank B04 cash-flow basis must be explicitly marked year_to_date")
        return
    ytd_fields = ("operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd","net_cash_change_ytd")
    if not all(number(item.get(k)) for k in ytd_fields):
        ERRORS.append(f"{symbol} {period}: YTD cash-flow components are incomplete on the upgraded schema")
    else:
        require_close(symbol, period, "YTD cash-flow sum", sum(item[k] for k in ytd_fields[:3]), item["net_cash_change_ytd"])
    quarter_fields = ("operating_cash_flow","investing_cash_flow","financing_cash_flow","net_cash_change")
    if not all(number(item.get(k)) for k in quarter_fields):
        ERRORS.append(f"{symbol} {period}: standalone-quarter cash-flow components are incomplete")
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
        bridge_delta = item["cash_ending"]-item["cash_beginning"]-item["net_cash_change"]
        if abs(bridge_delta) > 50:
            ERRORS.append(f"{symbol} {period}: cash opening/closing bridge differs by {bridge_delta} million VND")
        elif bridge_delta:
            WARNINGS.append(f"{symbol} {period}: cash bridge residual {bridge_delta} million VND retained as OCR/source variance")
    if number(item.get("cash_and_equivalents")) and number(item.get("cash_beginning_reported_ytd")) and item["cash_and_equivalents"] == item["cash_beginning_reported_ytd"]:
        ERRORS.append(f"{symbol} {period}: generic cash_and_equivalents duplicates the B04 cash opening balance")

def main():
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
