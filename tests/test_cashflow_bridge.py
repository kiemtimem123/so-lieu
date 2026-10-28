"""Regression tests for the FX-aware cash-flow bridge in validate-bank-reconciliation.py."""
import json
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = runpy.run_path(
    str(ROOT / "scripts" / "validate-bank-reconciliation.py"),
    run_name="cashflow_validator_module",
)
cash_bridge_delta = VALIDATOR["cash_bridge_delta"]


class CashFlowBridgeTests(unittest.TestCase):
    def test_tcb_2024_q1_bridge_includes_negative_fx_effect(self):
        row = {
            "cash_beginning": 110500219,
            "cash_ending": 124179846,
            "net_cash_change": 13699760,
            "foreign_exchange_effect": -20133,
        }
        self.assertEqual(cash_bridge_delta(row), 0)

    def test_tcb_2024_q2_bridge_includes_positive_fx_effect(self):
        row = {
            "cash_beginning": 124179846,
            "cash_ending": 124891909,
            "net_cash_change": 705129,
            "foreign_exchange_effect": 6934,
        }
        self.assertEqual(cash_bridge_delta(row), 0)

    def test_missing_fx_field_is_not_fabricated(self):
        row = {
            "cash_beginning": 170247424,
            "cash_ending": 177278961,
            "net_cash_change": 7031557,
        }
        # Without an FX line, retain the small residual for review; do not infer FX.
        self.assertEqual(cash_bridge_delta(row), -20)

    def test_missing_core_input_returns_none(self):
        self.assertIsNone(cash_bridge_delta({
            "cash_beginning": 100,
            "cash_ending": 120,
        }))


    def test_tcb_2025_q4_uses_audited_fy2025_cashflow(self):
        snapshot = json.loads((ROOT / "data" / "financials-TCB.json").read_text(encoding="utf-8"))
        rows = {row["period"]: row for row in snapshot["items"]}
        q3 = rows["2025-Q3"]
        q4 = rows["2025-Q4"]

        # Audited FY2025 report, PDF pages 15-16 (printed pages 10-11).
        self.assertEqual(q4["cashflow_audit_revision"]["source_archive_file"],
                         "reports/raw/TCB/vietstock-tcb-2024-2026-20261019/553195cdc772f58a.pdf")
        self.assertEqual(q4["operating_cash_flow_ytd"], 39923618)
        self.assertEqual(q4["investing_cash_flow_ytd"], -816440)
        self.assertEqual(q4["financing_cash_flow_ytd"], 5235750)
        self.assertEqual(q4["net_cash_change_ytd"], 44342928)
        self.assertEqual(q4["cash_beginning_reported_ytd"], 147484415)
        self.assertEqual(q4["cash_ending_reported_ytd"], 191827343)

        # Standalone Q4 = audited FY2025 YTD minus Q3 2025 YTD.
        self.assertEqual(q4["operating_cash_flow"], 39923618 - q3["operating_cash_flow_ytd"])
        self.assertEqual(q4["investing_cash_flow"], -816440 - q3["investing_cash_flow_ytd"])
        self.assertEqual(q4["financing_cash_flow"], 5235750 - q3["financing_cash_flow_ytd"])
        self.assertEqual(q4["net_cash_change"], 44342928 - q3["net_cash_change_ytd"])
        self.assertEqual(q4["cash_beginning"], q3["cash_ending"])
        self.assertEqual(q4["cash_ending"], 191827343)
        self.assertEqual(
            q4["operating_cash_flow"] + q4["investing_cash_flow"] + q4["financing_cash_flow"],
            q4["net_cash_change"],
        )
        self.assertEqual(cash_bridge_delta(q4), 0)

    def test_tcb_2026_q3_300dpi_source_rescan_corrects_cash_bridge(self):
        snapshot = json.loads((ROOT / "data" / "financials-TCB.json").read_text(encoding="utf-8"))
        q3 = next(row for row in snapshot["items"] if row["period"] == "2026-Q3")
        correction = q3["financial_line_items_value_corrections"]["cash_ending"]
        self.assertEqual(q3["cash_ending"], 177278981)
        self.assertEqual(q3["cash_ending_reported_ytd"], 177278981)
        self.assertEqual(correction["source_pdf_page"], 12)
        self.assertEqual(correction["source_ocr_engine"], "tesseract-vie+eng-psm6-300dpi-targeted-rescan")
        self.assertEqual(cash_bridge_delta(q3), 0)
        self.assertEqual(
            q3["cash_ending_reported_ytd"] - q3["cash_beginning_reported_ytd"] - q3["net_cash_change_ytd"],
            0,
        )


    def test_mbb_cashflow_normalization_reconciles_all_periods_except_flagged_q2_2025(self):
        snapshot = json.loads((ROOT / "data" / "financials-MBB.json").read_text(encoding="utf-8"))
        rows = {row["period"]: row for row in snapshot["items"]}
        self.assertEqual(len(rows), 10)

        # Check source-backed totals and both cash bridges for each MBB quarter.
        for period, row in rows.items():
            with self.subTest(period=period):
                self.assertEqual(
                    row["operating_cash_flow"] + row["investing_cash_flow"] + row["financing_cash_flow"],
                    row["net_cash_change"],
                )
                self.assertEqual(
                    row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] + row["financing_cash_flow_ytd"],
                    row["net_cash_change_ytd"],
                )
                ytd_bridge = (
                    row["cash_ending_reported_ytd"]
                    - row["cash_beginning_reported_ytd"]
                    - row["net_cash_change_ytd"]
                )
                self.assertEqual(ytd_bridge, 0)
                if period == "2025-Q2":
                    self.assertEqual(cash_bridge_delta(row), -2)
                    self.assertEqual(
                        row["cashflow_source_reconciliation"]["status"],
                        "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BRIDGE_2_MILLION",
                    )
                else:
                    self.assertEqual(cash_bridge_delta(row), 0)

        # Previously blank or mis-mapped source values that must not regress.
        self.assertEqual(rows["2024-Q1"]["financing_cash_flow"], 1050000)
        self.assertEqual(rows["2024-Q1"]["cash_ending"], 83716470)
        self.assertEqual(rows["2024-Q3"]["cash_beginning_reported_ytd"], 109095118)
        self.assertEqual(rows["2024-Q4"]["operating_cash_flow_ytd"], -18576384)
        self.assertEqual(rows["2024-Q4"]["financing_cash_flow_ytd"], 8759748)
        self.assertEqual(rows["2024-Q4"]["cash_ending_reported_ytd"], 97040273)
        self.assertTrue(rows["2024-Q4"]["cashflow_source_reconciliation"]["reference_sources"][0]["visually_checked"])

        # Latest, visually checked H1/2025 comparative replaces stale values from the Q2/2025 report.
        q2 = rows["2025-Q2"]
        for row in rows.values():
            for field in (
                "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
                "net_cash_change", "cash_beginning", "cash_ending",
                "operating_cash_flow_ytd", "investing_cash_flow_ytd",
                "financing_cash_flow_ytd", "net_cash_change_ytd",
                "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            ):
                self.assertIn(field, row["financial_line_items_extracted_fields"])
        self.assertEqual(q2["operating_cash_flow_ytd"], 1516540)
        self.assertEqual(q2["investing_cash_flow_ytd"], -400976)
        self.assertEqual(q2["financing_cash_flow_ytd"], 5698563)
        self.assertEqual(q2["net_cash_change_ytd"], 6814127)
        self.assertEqual(q2["cash_beginning_reported_ytd"], 97040273)
        self.assertEqual(q2["cash_ending_reported_ytd"], 103854400)
        self.assertEqual(q2["cashflow_balance_bridge_recovery"]["bridge_residual"], -2)



if __name__ == "__main__":
    unittest.main()
