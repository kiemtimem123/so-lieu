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
within_relative_tolerance = VALIDATOR["within_relative_tolerance"]
relative_difference_percent = VALIDATOR["relative_difference_percent"]


class CashFlowBridgeTests(unittest.TestCase):

    def test_relative_tolerance_accepts_up_to_0_01_percent_only(self):
        self.assertTrue(within_relative_tolerance(100.0, 100.009))
        self.assertTrue(within_relative_tolerance(100000000, 100009000))
        self.assertFalse(within_relative_tolerance(100.0, 100.02))
        self.assertAlmostEqual(relative_difference_percent(100, 100.02), 0.019996, places=5)

    def test_mbb_small_cross_report_residuals_are_accepted_but_retained(self):
        snapshot = json.loads((ROOT / "data" / "financials-MBB.json").read_text(encoding="utf-8"))
        rows = {row["period"]: row for row in snapshot["items"]}
        prior_close = rows["2024-Q4"]["cash_ending"]
        q1_open = rows["2025-Q1"]["cash_beginning"]
        self.assertEqual(q1_open - prior_close, 2)
        self.assertTrue(within_relative_tolerance(q1_open, prior_close))
        q2 = rows["2025-Q2"]
        residual = cash_bridge_delta(q2)
        self.assertEqual(residual, -2)
        expected_close = q2["cash_beginning"] + q2["net_cash_change"] + q2.get("foreign_exchange_effect", 0)
        self.assertTrue(within_relative_tolerance(q2["cash_ending"], expected_close))
        self.assertEqual(
            q2["cashflow_source_reconciliation"]["status"],
            "ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT",
        )

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
        # Synthetic fixture: never reuse a real ticker's corrected/previous OCR value here.
        row = {
            "cash_beginning": 1000,
            "cash_ending": 1230,
            "net_cash_change": 250,
        }
        # Without an FX line, retain the residual for review; do not infer FX.
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


    def test_mbb_cashflow_normalization_reconciles_all_periods_with_small_residual_tolerance(self):
        snapshot = json.loads((ROOT / "data" / "financials-MBB.json").read_text(encoding="utf-8"))
        rows = {row["period"]: row for row in snapshot["items"]}
        self.assertEqual(len(rows), 10)

        # Check source-backed totals, standalone-vs-YTD math and cash bridges.
        flow_pairs = (
            ("operating_cash_flow", "operating_cash_flow_ytd"),
            ("investing_cash_flow", "investing_cash_flow_ytd"),
            ("financing_cash_flow", "financing_cash_flow_ytd"),
            ("net_cash_change", "net_cash_change_ytd"),
        )
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
                year, qtr = period.split("-Q")
                if int(qtr) == 1:
                    for quarterly_field, ytd_field in flow_pairs:
                        self.assertEqual(row[quarterly_field], row[ytd_field])
                else:
                    prior = rows[f"{year}-Q{int(qtr) - 1}"]
                    for quarterly_field, ytd_field in flow_pairs:
                        self.assertEqual(row[quarterly_field], row[ytd_field] - prior[ytd_field])

                ytd_bridge = (
                    row["cash_ending_reported_ytd"]
                    - row["cash_beginning_reported_ytd"]
                    - row["net_cash_change_ytd"]
                )
                self.assertEqual(ytd_bridge, 0)
                if period == "2025-Q2":
                    self.assertEqual(cash_bridge_delta(row), -2)
                    self.assertTrue(within_relative_tolerance(
                        row["cash_ending"],
                        row["cash_beginning"] + row["net_cash_change"] + row.get("foreign_exchange_effect", 0),
                    ))
                    self.assertEqual(
                        row["cashflow_source_reconciliation"]["status"],
                        "ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT",
                    )
                else:
                    self.assertEqual(cash_bridge_delta(row), 0)

        # Adjacent-quarter continuity must be tested separately from each row's internal cash bridge.
        quarter_periods = sorted(rows)
        continuity_residuals = {}
        for prior_period, current_period in zip(quarter_periods, quarter_periods[1:]):
            prior, current = rows[prior_period], rows[current_period]
            if prior_period[:4] != current_period[:4]:
                # Quarter-to-quarter cash continuity still applies across a calendar-year boundary.
                residual = current["cash_beginning"] - prior["cash_ending"]
            else:
                residual = current["cash_beginning"] - prior["cash_ending"]
            continuity_residuals[(prior_period, current_period)] = residual
        self.assertEqual(
            {pair: value for pair, value in continuity_residuals.items() if value != 0},
            {("2024-Q4", "2025-Q1"): 2},
        )
        self.assertEqual(
            rows["2025-Q1"]["cashflow_balance_bridge_recovery"]["opening_minus_prior_closing_residual"],
            2,
        )
        self.assertEqual(
            rows["2025-Q2"]["cashflow_balance_bridge_recovery"]["prior_year_end_to_q1_opening_residual"],
            2,
        )
        self.assertEqual(
            rows["2025-Q2"]["cashflow_source_reconciliation"]["checks"]["prior_year_end_to_q1_opening_residual"],
            2,
        )
        self.assertEqual(
            rows["2025-Q2"]["cashflow_balance_bridge_recovery"]["q2_quarter_bridge_residual"],
            -2,
        )
        q1_reference_urls = {
            item["source_url"] for item in rows["2025-Q1"]["cashflow_source_reconciliation"]["reference_sources"]
        }
        self.assertIn(
            "https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/MBB_Baocaotaichinh_Q1_2026_Hopnhat.pdf",
            q1_reference_urls,
        )

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


class ACBCashFlowNormalizationTests(unittest.TestCase):
    """Regression tests for the source-reconciled ACB cash-flow series."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-ACB.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_acb_all_periods_reconcile_with_fx_and_quarter_ytd_basis(self):
        core_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
        )
        self.assertEqual(len(self.rows), 10)
        self.assertEqual(set(self.rows), {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        })
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertTrue(all(isinstance(row.get(field), (int, float))
                                    and not isinstance(row.get(field), bool)
                                    for field in core_fields))
                self.assertEqual(row["operating_cash_flow"] +
                                 row["investing_cash_flow"] +
                                 row["financing_cash_flow"], row["net_cash_change"])
                self.assertEqual(row["operating_cash_flow_ytd"] +
                                 row["investing_cash_flow_ytd"] +
                                 row["financing_cash_flow_ytd"], row["net_cash_change_ytd"])
                self.assertEqual(row["cash_ending_reported_ytd"] -
                                 row["cash_beginning_reported_ytd"] -
                                 row["net_cash_change_ytd"] -
                                 row["foreign_exchange_effect_ytd"], 0)
                self.assertEqual(row["cash_ending"] - row["cash_beginning"] -
                                 row["net_cash_change"] -
                                 row["foreign_exchange_effect"], 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"], 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["quarter_cash_bridge_residual"], 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["status"], "PASS_ARITHMETIC_RECONCILED")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertTrue(row["source_index_url"].startswith(
                    "https://finance.vietstock.vn/ACB/tai-tai-lieu.htm?doctype=1"))
                for field in core_fields:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow],
                                         row[flow + "_ytd"] - prior[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"] -
                                     prior["foreign_exchange_effect_ytd"])
                    self.assertEqual(row["cash_beginning"], prior["cash_ending"])

    def test_acb_uses_later_vietstock_comparative_basis_for_prior_periods(self):
        q42024 = self.rows["2024-Q4"]
        self.assertEqual(q42024["operating_cash_flow_ytd"], 8370231)
        self.assertEqual(q42024["investing_cash_flow_ytd"], -733310)
        self.assertEqual(q42024["net_cash_change_ytd"], 3752870)
        self.assertIn("Q4_2025", q42024["cashflow_audit_revision"]["selected_source_url"])

        q12025 = self.rows["2025-Q1"]
        self.assertEqual(q12025["operating_cash_flow_ytd"], -4309694)
        self.assertEqual(q12025["net_cash_change_ytd"], -4486631)
        self.assertIn("Q1_2026", q12025["cashflow_audit_revision"]["selected_source_url"])

        q22025 = self.rows["2025-Q2"]
        self.assertEqual(q22025["operating_cash_flow_ytd"], -9800290)
        self.assertEqual(q22025["investing_cash_flow_ytd"], -223472)
        self.assertEqual(q22025["net_cash_change_ytd"], -14490420)
        self.assertIn("Q2_2026", q22025["cashflow_audit_revision"]["selected_source_url"])

    def test_acb_q2_2026_cash_balance_ocr_correction_is_source_backed(self):
        row = self.rows["2026-Q2"]
        self.assertEqual(row["cash_ending_reported_ytd"], 116533043)
        correction = row["cashflow_source_reconciliation"]["source_ocr_correction"]
        self.assertEqual(correction["misread_value"], 416533043)
        self.assertEqual(correction["corrected_source_value"], 116533043)
        self.assertEqual(correction["units"], "triệu VND")
        self.assertEqual(row["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"], 0)


class FTPCashFlowNormalizationTests(unittest.TestCase):
    """Regression checks for FPT YTD/quarter derivation and relative tolerance."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-FPT.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    @staticmethod
    def relative_residual_percent(residual, *reference_values):
        scale = max([abs(value) for value in reference_values] + [1])
        return abs(residual) / scale * 100

    def test_fpt_all_ten_periods_use_source_ytd_and_quarter_math(self):
        core_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
        )
        self.assertEqual(len(self.rows), 10)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertTrue(all(isinstance(row.get(field), (int, float))
                                    and not isinstance(row.get(field), bool)
                                    for field in core_fields))
                for field in core_fields:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/FPT/tai-tai-lieu.htm?doctype=1")
                ytd_flow_sum = (row["operating_cash_flow_ytd"] +
                                row["investing_cash_flow_ytd"] +
                                row["financing_cash_flow_ytd"])
                quarter_flow_sum = (row["operating_cash_flow"] +
                                    row["investing_cash_flow"] +
                                    row["financing_cash_flow"])
                ytd_residual = ytd_flow_sum - row["net_cash_change_ytd"]
                quarter_residual = quarter_flow_sum - row["net_cash_change"]
                self.assertLessEqual(self.relative_residual_percent(
                    ytd_residual, row["operating_cash_flow_ytd"],
                    row["investing_cash_flow_ytd"], row["financing_cash_flow_ytd"],
                    row["net_cash_change_ytd"]), 0.01)
                self.assertLessEqual(self.relative_residual_percent(
                    quarter_residual, row["operating_cash_flow"],
                    row["investing_cash_flow"], row["financing_cash_flow"],
                    row["net_cash_change"]), 0.01)

                ytd_bridge = (row["cash_ending_reported_ytd"] -
                              row["cash_beginning_reported_ytd"] -
                              row["net_cash_change_ytd"] -
                              row["foreign_exchange_effect_ytd"])
                self.assertLessEqual(self.relative_residual_percent(
                    ytd_bridge, row["cash_ending_reported_ytd"],
                    row["cash_beginning_reported_ytd"]), 0.01)
                quarter_bridge = cash_bridge_delta(row)
                self.assertLessEqual(self.relative_residual_percent(
                    quarter_bridge, row["cash_ending"], row["cash_beginning"]), 0.01)
                self.assertEqual(row["cashflow_source_reconciliation"]["status"]
                                 in ("PASS_ARITHMETIC_RECONCILED",
                                     "ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT",
                                     "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT"), True)

                year, quarter_text = period.split("-Q")
                q = int(quarter_text)
                if q == 1:
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"])
                else:
                    previous = self.rows[f"{year}-Q{q-1}"]
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow],
                                         row[flow + "_ytd"] - previous[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"] -
                                     previous["foreign_exchange_effect_ytd"])
                    self.assertEqual(row["cash_beginning"], previous["cash_ending"])

    def test_fpt_later_comparatives_are_used_for_revised_fy2024_and_h1_2025(self):
        fy2024 = self.rows["2024-Q4"]
        self.assertEqual(fy2024["operating_cash_flow_ytd"], 11703777)
        self.assertEqual(fy2024["investing_cash_flow_ytd"], -8461812)
        self.assertEqual(fy2024["financing_cash_flow_ytd"], -2197766)
        self.assertEqual(fy2024["net_cash_change_ytd"], 1044199)
        self.assertIn("Q4_2025", fy2024["cashflow_audit_revision"]["selected_source_url"])

        h12025 = self.rows["2025-Q2"]
        self.assertEqual(h12025["operating_cash_flow_ytd"], 1683573)
        self.assertEqual(h12025["investing_cash_flow_ytd"], -7233992)
        self.assertEqual(h12025["financing_cash_flow_ytd"], 6254833)
        self.assertEqual(h12025["net_cash_change_ytd"], 704415)
        self.assertEqual(h12025["foreign_exchange_effect_ytd"], -224)
        self.assertIn("Q2_2026", h12025["cashflow_audit_revision"]["selected_source_url"])

    def test_fpt_q1_2026_cash_opening_continuity_issue_exceeds_tolerance(self):
        previous = self.rows["2025-Q4"]
        current = self.rows["2026-Q1"]
        residual = current["cash_beginning"] - previous["cash_ending"]
        self.assertEqual(residual, -18076)
        percent = self.relative_residual_percent(
            residual, current["cash_beginning"], previous["cash_ending"])
        self.assertGreater(percent, 0.01)
        self.assertEqual(
            current["cashflow_source_reconciliation"]["cross_period_continuity"]["status"],
            "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT",
        )
        # Keep both printed balances; each report's own cash bridge remains within tolerance.
        self.assertLessEqual(self.relative_residual_percent(
            cash_bridge_delta(current), current["cash_beginning"], current["cash_ending"]), 0.01)
