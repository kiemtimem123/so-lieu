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


class SHBCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for SHB source revisions, YTD math and 0.01% continuity rule."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-SHB.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_shb_all_ten_periods_reconcile_from_selected_ytd_basis(self):
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
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/SHB/tai-tai-lieu.htm?doctype=1")
                for field in core_fields:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                self.assertEqual(row["operating_cash_flow"] + row["investing_cash_flow"] +
                                 row["financing_cash_flow"], row["net_cash_change"])
                self.assertEqual(row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] +
                                 row["financing_cash_flow_ytd"], row["net_cash_change_ytd"])
                self.assertEqual(
                    row["cash_ending_reported_ytd"] - row["cash_beginning_reported_ytd"] -
                    row["net_cash_change_ytd"] - row["foreign_exchange_effect_ytd"], 0)
                self.assertEqual(
                    row["cash_ending"] - row["cash_beginning"] - row["net_cash_change"] -
                    row["foreign_exchange_effect"], 0)
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(rec["ytd_cash_bridge_residual"], 0)
                self.assertEqual(rec["quarter_cash_bridge_residual"], 0)
                self.assertEqual(rec["status"], "PASS_ARITHMETIC_RECONCILED")

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
                        self.assertEqual(row[flow], row[flow + "_ytd"] - previous[flow + "_ytd"])
                    self.assertEqual(row["cash_beginning"], previous["cash_ending"])

    def test_shb_uses_later_vietstock_comparatives_for_2024(self):
        q1 = self.rows["2024-Q1"]
        self.assertEqual(q1["operating_cash_flow_ytd"], -52416402)
        self.assertEqual(q1["investing_cash_flow_ytd"], 202387)
        self.assertEqual(q1["financing_cash_flow_ytd"], -327)
        self.assertEqual(q1["net_cash_change_ytd"], -52214342)
        self.assertIn("Q1_2025", q1["cashflow_audit_revision"]["selected_source_url"])
        self.assertEqual(
            q1["cashflow_audit_revision"]["previous_original_basis_values_superseded"]["net_cash_change_ytd"],
            -62214342)

        q2 = self.rows["2024-Q2"]
        self.assertEqual(q2["operating_cash_flow_ytd"], -22155105)
        self.assertEqual(q2["investing_cash_flow_ytd"], -66706)
        self.assertEqual(q2["financing_cash_flow_ytd"], 434732)
        self.assertEqual(q2["net_cash_change_ytd"], -21787079)
        self.assertIn("Q2_2025", q2["cashflow_audit_revision"]["selected_source_url"])

        q3 = self.rows["2024-Q3"]
        self.assertEqual(q3["operating_cash_flow_ytd"], 5828557)
        self.assertEqual(q3["investing_cash_flow_ytd"], -88386)
        self.assertEqual(q3["financing_cash_flow_ytd"], 400074)
        self.assertEqual(q3["net_cash_change_ytd"], 6140245)
        self.assertIn("Q3_2025", q3["cashflow_audit_revision"]["selected_source_url"])

        q4 = self.rows["2024-Q4"]
        self.assertEqual(q4["operating_cash_flow_ytd"], 11949125)
        self.assertEqual(q4["investing_cash_flow_ytd"], -179988)
        self.assertEqual(q4["financing_cash_flow_ytd"], -1311389)
        self.assertEqual(q4["net_cash_change_ytd"], 10457748)
        self.assertEqual(q4["cash_ending_reported_ytd"], 121317534)
        self.assertIn("Q4_2025", q4["cashflow_audit_revision"]["selected_source_url"])

    def test_shb_q4_to_q1_2026_cash_basis_residual_exceeds_0_01_percent(self):
        prior = self.rows["2025-Q4"]
        current = self.rows["2026-Q1"]
        residual = current["cash_beginning"] - prior["cash_ending"]
        self.assertEqual(residual, -719944)
        self.assertFalse(within_relative_tolerance(
            current["cash_beginning"], prior["cash_ending"]))
        continuity = current["cashflow_source_reconciliation"]["cross_period_continuity"]
        self.assertEqual(continuity["residual_million_vnd"], -719944)
        self.assertGreater(continuity["relative_difference_percent"], 0.01)
        self.assertEqual(continuity["status"],
                         "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT")
        self.assertEqual(current["cash_ending"], 179435919)
        self.assertEqual(prior["cash_ending"], 162627663)
        # Both source balances are kept as printed; each row's internal bridge is exact.
        self.assertEqual(cash_bridge_delta(current), 0)


class HCMCashFlowNormalizationTests(unittest.TestCase):
    """Cash-flow regression tests for HCM: comparative basis, quarter/YTD math, and tolerance."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-HCM.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    @staticmethod
    def relative_percent(actual, expected):
        scale = max(abs(actual), abs(expected), 1)
        return abs(actual - expected) / scale * 100

    def test_hcm_all_ten_periods_cashflow_sums_and_ytd_deltas(self):
        core = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "cashflow_period_basis",
        )
        self.assertEqual(len(self.rows), 10)
        self.assertEqual(set(self.rows), {
            "2024-Q1","2024-Q2","2024-Q3","2024-Q4","2025-Q1",
            "2025-Q2","2025-Q3","2025-Q4","2026-Q1","2026-Q2",
        })
        for period, row in self.rows.items():
            with self.subTest(period=period):
                numeric_core = tuple(field for field in core if field != "cashflow_period_basis")
                self.assertTrue(all(isinstance(row.get(field), (int, float))
                                    and not isinstance(row.get(field), bool)
                                    for field in numeric_core))
                self.assertIsInstance(row["cashflow_period_basis"], str)
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/HCM/tai-tai-lieu.htm?doctype=1")
                self.assertEqual(row["unit"], "triệu VND")
                for field in core:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                self.assertLessEqual(self.relative_percent(
                    row["operating_cash_flow"] + row["investing_cash_flow"] +
                    row["financing_cash_flow"], row["net_cash_change"]), 0.01)
                self.assertLessEqual(self.relative_percent(
                    row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] +
                    row["financing_cash_flow_ytd"], row["net_cash_change_ytd"]), 0.01)
                rec = row["cashflow_source_reconciliation"]
                self.assertLessEqual(self.relative_percent(
                    row["cash_ending_reported_ytd"],
                    row["cash_beginning_reported_ytd"] + row["net_cash_change_ytd"]), 0.01)
                self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)

                year, qtxt = period.split("-Q")
                q = int(qtxt)
                if q == 1:
                    for flow in ("operating_cash_flow","investing_cash_flow",
                                 "financing_cash_flow","net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                else:
                    previous = self.rows[f"{year}-Q{q-1}"]
                    for flow in ("operating_cash_flow","investing_cash_flow",
                                 "financing_cash_flow","net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"] - previous[flow + "_ytd"])
                    self.assertEqual(row["cash_beginning"], previous["cash_ending"])

                # Keep any cash bridge exceeding 0.01% explicitly classified for manual review.
                if rec["quarter_cash_bridge_relative_difference_percent"] > 0.01:
                    self.assertEqual(rec["status"],
                                     "NEEDS_MANUAL_REVIEW_CROSS_REPORT_BASIS_GT_0_01_PERCENT")
                    self.assertTrue(rec["cross_report_basis_issues"])
                elif rec["status"] == "NEEDS_MANUAL_REVIEW_CROSS_REPORT_BASIS_GT_0_01_PERCENT":
                    self.assertTrue(rec["cross_report_basis_issues"])

    def test_hcm_later_2024_comparatives_are_selected_and_auditable(self):
        expected = {
            "2024-Q1": (44577, -9701, 501814, 536691),
            "2024-Q2": (-9127478, -12044, 8899293, -240229),
            "2024-Q3": (-14508550, -14545, 13940108, -582988),
            "2024-Q4": (-13164858, -17930, 12382167, -800622),
        }
        comparison_period_source = {
            "2024-Q1": "Q1_2025",
            "2024-Q2": "Q2_2025",
            "2024-Q3": "Q3_2025",
            "2024-Q4": "Q4_2025",
        }
        for period, values in expected.items():
            with self.subTest(period=period):
                row = self.rows[period]
                self.assertEqual((
                    row["operating_cash_flow_ytd"], row["investing_cash_flow_ytd"],
                    row["financing_cash_flow_ytd"], row["net_cash_change_ytd"]
                ), values)
                self.assertIn(comparison_period_source[period],
                              row["cashflow_audit_revision"]["selected_source_url"])

    def test_hcm_h1_2025_later_comparative_overrides_old_snapshot_basis(self):
        row = self.rows["2025-Q2"]
        self.assertEqual(row["operating_cash_flow_ytd"], -4154431)
        self.assertEqual(row["investing_cash_flow_ytd"], -9068)
        self.assertEqual(row["financing_cash_flow_ytd"], 3273395)
        self.assertEqual(row["net_cash_change_ytd"], -890104)
        self.assertEqual(row["cash_beginning_reported_ytd"], 1963445)
        self.assertEqual(row["cash_ending_reported_ytd"], 1073341)
        self.assertIn("Q2_2026", row["cashflow_audit_revision"]["selected_source_url"])
        self.assertEqual(
            row["cashflow_audit_revision"]["previous_original_basis_values_superseded"]["net_cash_change_ytd"],
            -714404
        )
        self.assertEqual(
            row["cashflow_source_reconciliation"]["selected_ytd_opening_vs_prior_fy_close"]["residual_million_vnd"],
            -60500
        )

    def test_hcm_cross_report_basis_mismatches_over_tolerance_are_not_plugged(self):
        q2_2025 = self.rows["2025-Q2"]["cashflow_source_reconciliation"]
        q3_2025 = self.rows["2025-Q3"]["cashflow_source_reconciliation"]
        q2_2026 = self.rows["2026-Q2"]["cashflow_source_reconciliation"]
        self.assertEqual(q2_2025["quarter_cash_bridge_residual_million_vnd"], -60500)
        self.assertGreater(q2_2025["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertEqual(q3_2025["quarter_cash_bridge_residual_million_vnd"], 60500)
        self.assertGreater(q3_2025["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertEqual(q2_2026["quarter_cash_bridge_residual_million_vnd"], -320499)
        self.assertGreater(q2_2026["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertEqual(self.rows["2026-Q2"]["cash_ending"], 2202389)
        self.assertEqual(self.rows["2026-Q1"]["cash_ending"], 1208989)
        self.assertEqual(self.rows["2026-Q2"]["cashflow_source_reconciliation"]["selected_ytd_opening_vs_prior_fy_close"]["residual_million_vnd"], -320500)


class VNDCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for VNDIRECT's company B03b-CTCK cash-flow statement."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-VND.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.core = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
        )

    def test_vnd_all_eleven_periods_use_ytd_and_reconcile_with_001_percent_tolerance(self):
        self.assertEqual(len(self.rows), 11)
        self.assertEqual(set(self.rows), {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2", "2026-Q3",
        })
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/VND/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(all(isinstance(row.get(k), (int, float))
                                    and not isinstance(row.get(k), bool)
                                    for k in self.core))
                self.assertTrue(all(k in row["financial_line_items_extracted_fields"]
                                    for k in self.core))
                self.assertTrue(all(k not in row.get("financial_line_items_rejected_fields", [])
                                    for k in self.core))

                self.assertTrue(within_relative_tolerance(
                    row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] +
                    row["financing_cash_flow_ytd"], row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(
                    row["operating_cash_flow"] + row["investing_cash_flow"] +
                    row["financing_cash_flow"], row["net_cash_change"]))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending_reported_ytd"],
                    row["cash_beginning_reported_ytd"] + row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending"], row["cash_beginning"] + row["net_cash_change"]))

                rec = row["cashflow_source_reconciliation"]
                self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
                self.assertTrue(rec["foreign_exchange_effect_separately_reported"] is False)
                self.assertIsNone(row.get("foreign_exchange_effect"))
                self.assertIsNone(row.get("foreign_exchange_effect_ytd"))
                self.assertNotIn("foreign_exchange_effect", row["financial_line_items_extracted_fields"])
                self.assertNotIn("foreign_exchange_effect_ytd", row["financial_line_items_extracted_fields"])

                year, qtext = period.split("-Q")
                quarter = int(qtext)
                if quarter == 1:
                    for field in self.core[:4]:
                        self.assertEqual(row[field], row[field + "_ytd"])
                else:
                    previous = self.rows[f"{year}-Q{quarter-1}"]
                    for field in self.core[:4]:
                        self.assertEqual(row[field], row[field + "_ytd"] - previous[field + "_ytd"])
                    self.assertEqual(row["cash_beginning"], previous["cash_ending"])

    def test_vnd_q2_2024_comparator_cff_conflict_is_retained_for_manual_review(self):
        row = self.rows["2024-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(rec["status"],
                         "NEEDS_MANUAL_REVIEW_SOURCE_COMPARATOR_CFF_GT_0_01_PERCENT")
        issue = rec["source_candidates_pending_manual_review"][0]
        self.assertEqual(issue["field"], "financing_cash_flow_ytd")
        self.assertEqual(issue["selected_value_million_vnd"], 1076402)
        self.assertEqual(issue["newer_comparative_ocr_candidate_million_vnd"], 1078402)
        self.assertEqual(issue["difference_million_vnd"], 2000)
        self.assertGreater(issue["relative_difference_percent"], 0.01)
        # Use the source-backed value that reconciles; never plug in the newer OCR candidate.
        self.assertEqual(row["financing_cash_flow_ytd"], 1076402)
        self.assertEqual(
            row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] +
            row["financing_cash_flow_ytd"], row["net_cash_change_ytd"]
        )

    def test_vnd_q2_2026_rounding_residual_is_accepted_not_plugged(self):
        row = self.rows["2026-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
        self.assertEqual(rec["ytd_flow_components_residual_million_vnd"], -3)
        self.assertEqual(row["net_cash_change_ytd"], -296409)
        self.assertEqual(row["cash_beginning_reported_ytd"], 1622127)
        self.assertEqual(row["cash_ending_reported_ytd"], 1325719)



class SHSCashFlowNormalizationTests(unittest.TestCase):
    """Source-based regression tests for SHS B03b-CTCK cash-flow line mapping."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-SHS.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.flows = (
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "net_cash_change",
        )
        cls.ytd = tuple(field + "_ytd" for field in cls.flows)
        cls.numeric_cash = (
            "cash_beginning", "cash_ending",
            "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
        )

    @staticmethod
    def relative_difference_percent(actual, expected):
        return abs(actual - expected) / max(abs(actual), abs(expected), 1) * 100

    def test_shs_cashflow_series_uses_correct_company_statement_lines_and_tolerance(self):
        self.assertEqual(len(self.rows), 10)
        self.assertEqual(set(self.rows), {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2",
        })
        manual_only = {"2024-Q2", "2024-Q3"}
        complete_ytd = set(self.rows) - {"2024-Q2"}
        complete_quarter = set(self.rows) - manual_only

        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(rec["source_index_url"],
                                 "https://finance.vietstock.vn/SHS/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(rec["source_url"].startswith("https://static2.vietstock.vn/data/HNX/"))
                self.assertEqual(rec["relative_tolerance_percent"], 0.01)
                self.assertEqual(rec["fx_line_present"], True)
                self.assertEqual(rec["fx_line_reported_as"], "-")
                self.assertEqual(row["foreign_exchange_effect"], 0)
                self.assertEqual(row["foreign_exchange_effect_ytd"], 0)
                for field in self.numeric_cash:
                    self.assertIsInstance(row.get(field), (int, float))
                self.assertIn("cashflow_period_basis", row["financial_line_items_extracted_fields"])

                if period in complete_ytd:
                    ytd_values = [row[field] for field in self.ytd]
                    self.assertTrue(all(isinstance(v, (int, float)) for v in ytd_values))
                    ytd_sum = sum(ytd_values[:3])
                    self.assertLessEqual(
                        self.relative_difference_percent(ytd_sum, ytd_values[3]), 0.01
                    )
                    ytd_bridge_actual = row["cash_ending_reported_ytd"]
                    ytd_bridge_expected = (
                        row["cash_beginning_reported_ytd"] +
                        row["net_cash_change_ytd"] +
                        row["foreign_exchange_effect_ytd"]
                    )
                    self.assertLessEqual(
                        self.relative_difference_percent(ytd_bridge_actual, ytd_bridge_expected),
                        0.01,
                    )
                    for field in self.ytd:
                        self.assertIn(field, row["financial_line_items_extracted_fields"])
                        self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                else:
                    self.assertEqual(period, "2024-Q2")
                    self.assertTrue(all(row.get(field) is None for field in self.ytd))
                    self.assertEqual(
                        rec["status"], "NEEDS_MANUAL_REVIEW_H1_2024_SOURCE_TOTALS_UNREADABLE"
                    )

                if period in complete_quarter:
                    q_values = [row[field] for field in self.flows]
                    self.assertTrue(all(isinstance(v, (int, float)) for v in q_values))
                    q_sum = sum(q_values[:3])
                    self.assertLessEqual(
                        self.relative_difference_percent(q_sum, q_values[3]), 0.01
                    )
                    q_bridge_actual = row["cash_ending"]
                    q_bridge_expected = (
                        row["cash_beginning"] + row["net_cash_change"] +
                        row["foreign_exchange_effect"]
                    )
                    self.assertLessEqual(
                        self.relative_difference_percent(q_bridge_actual, q_bridge_expected),
                        0.01,
                    )
                    for field in self.flows:
                        self.assertIn(field, row["financial_line_items_extracted_fields"])
                        self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                    year, qtext = period.split("-Q")
                    quarter = int(qtext)
                    if quarter == 1:
                        for qfield, yfield in zip(self.flows, self.ytd):
                            self.assertEqual(row[qfield], row[yfield])
                    else:
                        previous = self.rows[f"{year}-Q{quarter - 1}"]
                        for qfield, yfield in zip(self.flows, self.ytd):
                            self.assertEqual(row[qfield], row[yfield] - previous[yfield])
                        self.assertEqual(row["cash_beginning"], previous["cash_ending"])
                else:
                    self.assertTrue(all(row.get(field) is None for field in self.flows))
                    self.assertTrue(all(field not in row["financial_line_items_extracted_fields"]
                                        for field in self.flows))
                    expected_status = (
                        "NEEDS_MANUAL_REVIEW_H1_2024_SOURCE_TOTALS_UNREADABLE"
                        if period == "2024-Q2"
                        else "NEEDS_MANUAL_REVIEW_Q2_BASE_MISSING_FOR_STANDALONE_QUARTER"
                    )
                    self.assertEqual(rec["status"], expected_status)

    def test_shs_q1_2024_uses_corrected_cfo_not_pretax_profit(self):
        row = self.rows["2024-Q1"]
        self.assertEqual(row["operating_cash_flow_ytd"], -382576)
        self.assertEqual(row["investing_cash_flow_ytd"], -650)
        self.assertEqual(row["financing_cash_flow_ytd"], -46000)
        self.assertEqual(row["net_cash_change_ytd"], -429226)
        self.assertEqual(row["cash_beginning_reported_ytd"], 851889)
        self.assertEqual(row["cash_ending_reported_ytd"], 422664)
        self.assertEqual(row["cashflow_audit_revision"]["previous_incorrect_mapping"]["operating_cash_flow_ytd"],
                         443875769888)
        self.assertEqual(row["cashflow_audit_revision"]["previous_incorrect_mapping"]["reason"].split()[0],
                         "The")

    def test_shs_q2_2024_comparator_is_not_used_to_fill_unreadable_h1_flows(self):
        row = self.rows["2024-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(row["cash_ending"], 971739)
        self.assertEqual(row["cash_beginning_reported_ytd"], 851889)
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_H1_2024_SOURCE_TOTALS_UNREADABLE")
        self.assertEqual(len(rec["source_candidates_pending_manual_review"]), 1)
        self.assertTrue(all(row.get(field) is None for field in self.ytd))
        self.assertTrue(all(row.get(field) is None for field in self.flows))

    def test_shs_q4_2024_later_comparator_reclassification_remains_flagged(self):
        row = self.rows["2024-Q4"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_PRIOR_YEAR_COMPARATIVE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(row["operating_cash_flow_ytd"], -1403639)
        self.assertEqual(row["investing_cash_flow_ytd"], -16486)
        self.assertEqual(row["financing_cash_flow_ytd"], 1248994)
        self.assertEqual(row["net_cash_change_ytd"], -171130)
        review = rec["source_reclassification_review"]
        self.assertGreater(review["relative_differences_percent"]["investing_cash_flow"], 0.01)
        self.assertEqual(row["cash_ending_reported_ytd"], 680759)
        self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])

    def test_shs_h1_2025_comparator_difference_above_threshold_is_reviewed_not_plugged(self):
        row = self.rows["2025-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(row["operating_cash_flow_ytd"], -2580587)
        self.assertEqual(row["investing_cash_flow_ytd"], -5146)
        self.assertEqual(row["financing_cash_flow_ytd"], 2695969)
        self.assertEqual(row["net_cash_change_ytd"], 110236)
        self.assertGreater(
            rec["source_reclassification_review"]["relative_differences_percent"]["investing_cash_flow"],
            0.01,
        )
        self.assertLessEqual(
            rec["ytd_flow_components_relative_difference_percent"], 0.01
        )
        self.assertEqual(rec["selected_values_not_adjusted_for_tolerance"], True)


class NLGCashFlowNormalizationTests(unittest.TestCase):
    """Regression tests for NLG source-line mapping, relative tolerance and source holds."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-NLG.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.flows = ("operating_cash_flow", "investing_cash_flow",
                     "financing_cash_flow", "net_cash_change")
        cls.ytd_flows = tuple(field + "_ytd" for field in cls.flows)

    def test_nlg_all_periods_use_source_totals_and_apply_0_01_percent_rule(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), expected_periods)
        index_url = "https://finance.vietstock.vn/NLG/tai-tai-lieu.htm?doctype=1"

        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(rec["source_index_url"], index_url)
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(rec["relative_tolerance_percent"], 0.01)
                self.assertEqual(rec["selected_values_not_adjusted_for_tolerance"], True)

                ytd_values = [row.get("operating_cash_flow_ytd"),
                              row.get("investing_cash_flow_ytd"),
                              row.get("financing_cash_flow_ytd")]
                if all(isinstance(v, (int, float)) for v in ytd_values):
                    residual = sum(ytd_values) - row["net_cash_change_ytd"]
                    self.assertLessEqual(relative_difference_percent(
                        sum(ytd_values), row["net_cash_change_ytd"]), 0.01)
                    self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                    self.assertAlmostEqual(residual, rec["ytd_flow_components_residual"])
                else:
                    self.assertIn("NEEDS_MANUAL_REVIEW", rec["status"])

                self.assertLessEqual(
                    rec["ytd_cash_bridge_relative_difference_percent"], 0.01
                )

                q_values = [row.get("operating_cash_flow"),
                            row.get("investing_cash_flow"),
                            row.get("financing_cash_flow")]
                if all(isinstance(v, (int, float)) for v in q_values):
                    self.assertLessEqual(relative_difference_percent(
                        sum(q_values), row["net_cash_change"]), 0.01)
                    self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)

                if period == "2026-Q2":
                    self.assertGreater(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
                else:
                    self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q > 1:
                    previous = self.rows[f"{year}-Q{q-1}"]
                    for qfield, yfield in zip(self.flows, self.ytd_flows):
                        if (isinstance(row.get(qfield), (int, float)) and
                            isinstance(row.get(yfield), (int, float)) and
                            isinstance(previous.get(yfield), (int, float))):
                            self.assertEqual(row[qfield], row[yfield] - previous[yfield])
                else:
                    for qfield, yfield in zip(self.flows, self.ytd_flows):
                        if isinstance(row.get(qfield), (int, float)) and isinstance(row.get(yfield), (int, float)):
                            self.assertEqual(row[qfield], row[yfield])

    def test_nlg_h1_2024_later_comparator_reclassification_is_retained(self):
        row = self.rows["2024-Q2"]
        rec = row["cashflow_source_reconciliation"]
        review = rec["source_reclassification_review"]
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(row["operating_cash_flow_ytd"], -957220)
        self.assertEqual(row["investing_cash_flow_ytd"], 230888)
        self.assertEqual(row["financing_cash_flow_ytd"], 259631)
        self.assertEqual(row["net_cash_change_ytd"], -466701)
        self.assertGreater(review["relative_differences_percent"]["operating_cash_flow"], 0.01)
        self.assertGreater(review["relative_differences_percent"]["investing_cash_flow"], 0.01)
        self.assertTrue(review["net_cash_change_unchanged"])
        self.assertTrue(review["cash_balances_unchanged"])
        self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
        self.assertEqual(rec["ytd_cash_bridge_residual"], 0)

    def test_nlg_fy2024_later_comparator_ocr_mismatch_is_not_substituted(self):
        row = self.rows["2024-Q4"]
        rec = row["cashflow_source_reconciliation"]
        review = rec["later_comparator_review"]
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_LATER_COMPARATOR_OCR_UNRECONCILED")
        self.assertEqual(row["operating_cash_flow_ytd"], 1202932)
        self.assertEqual(row["investing_cash_flow_ytd"], 1028063)
        self.assertEqual(row["financing_cash_flow_ytd"], 672202)
        self.assertEqual(row["net_cash_change_ytd"], 2903197)
        self.assertEqual(review["component_sum_residual_million_vnd"], 3000000)
        self.assertGreater(review["relative_difference_percent"], 0.01)
        self.assertIn("pending", review["visual_review"])
        self.assertEqual(rec["ytd_cash_bridge_residual"], 0)

    def test_nlg_q1_2026_unreconciled_ocr_components_are_withheld(self):
        row = self.rows["2026-Q1"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_OCR_FLOW_COMPONENTS_GT_0_01_PERCENT")
        self.assertIsNone(row["operating_cash_flow_ytd"])
        self.assertIsNone(row["investing_cash_flow_ytd"])
        self.assertIsNone(row["financing_cash_flow_ytd"])
        self.assertIsNone(row["operating_cash_flow"])
        self.assertIsNone(row["investing_cash_flow"])
        self.assertIsNone(row["financing_cash_flow"])
        self.assertGreater(rec["ocr_flow_candidates"]["relative_difference_percent"], 0.01)
        self.assertEqual(rec["ocr_flow_candidates"]["residual_million_vnd"], -99999)
        self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
        for field in ("operating_cash_flow_ytd", "investing_cash_flow_ytd", "financing_cash_flow_ytd"):
            self.assertIn(field, row["financial_line_items_rejected_fields"])
            self.assertNotIn(field, row["financial_line_items_extracted_fields"])

    def test_nlg_q2_2026_ytd_passes_but_cross_period_cash_basis_remains_reviewed(self):
        row = self.rows["2026-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(row["operating_cash_flow_ytd"], -1087391)
        self.assertEqual(row["investing_cash_flow_ytd"], -1181784)
        self.assertEqual(row["financing_cash_flow_ytd"], -744326)
        self.assertEqual(row["net_cash_change_ytd"], -3013501)
        self.assertEqual(rec["ytd_flow_components_residual"], 0)
        self.assertEqual(rec["ytd_cash_bridge_residual"], 0)
        review = rec["selected_ytd_opening_vs_prior_fy_close"]
        self.assertEqual(review["residual_million_vnd"], -33085)
        self.assertGreater(review["relative_difference_percent"], 0.01)
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT")
        self.assertEqual(row["net_cash_change"], -1227030)
        self.assertEqual(rec["quarter_cash_bridge_residual"], -33085)
        self.assertGreater(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertIsNone(row["operating_cash_flow"])
        self.assertIsNone(row["investing_cash_flow"])
        self.assertIsNone(row["financing_cash_flow"])




class BSRCashFlowNormalizationTests(unittest.TestCase):
    """Source-aware regression coverage for the 10-period BSR cash-flow snapshot."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-BSR.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.core_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd", "cashflow_period_basis",
        )

    def test_bsr_all_ten_periods_reconcile_with_relative_tolerance(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), expected_periods)
        index_url = "https://finance.vietstock.vn/BSR/tai-tai-lieu.htm?doctype=1"
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["cashflow_source_reconciliation"]["source_index_url"], index_url)
                self.assertEqual(row["cashflow_source_reconciliation"]["relative_tolerance_percent"], 0.01)
                self.assertTrue(row["cashflow_source_reconciliation"]["selected_values_not_adjusted_for_tolerance"])
                for field in self.core_fields:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                numeric_fields = [f for f in self.core_fields if f != "cashflow_period_basis"]
                self.assertTrue(all(isinstance(row.get(f), (int, float)) and
                                    not isinstance(row.get(f), bool) for f in numeric_fields))
                rec = row["cashflow_source_reconciliation"]
                self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
                # Small residuals caused by rounding to million VND are retained, not plugged.
                self.assertAlmostEqual(
                    rec["ytd_flow_components_residual"],
                    row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] +
                    row["financing_cash_flow_ytd"] - row["net_cash_change_ytd"],
                )
                self.assertAlmostEqual(
                    rec["quarter_cash_bridge_residual"],
                    cash_bridge_delta(row),
                )
                year, quarter = period.split("-Q")
                q = int(quarter)
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

    def test_bsr_later_comparatives_are_traced_and_material_reclassifications_flagged(self):
        expected = {
            "2024-Q2": {
                "operating_cash_flow_ytd": -3828935,
                "investing_cash_flow_ytd": 7780875,
                "net_cash_change_ytd": 8996642,
                "source_url_fragment": "QUY%202/BSR_Baocaotaichinh_Q2_2025_Hopnhat.pdf",
                "changed_field": "operating_cash_flow_ytd",
            },
            "2024-Q4": {
                "operating_cash_flow_ytd": -80470,
                "financing_cash_flow_ytd": 3832872,
                "net_cash_change_ytd": 11742162,
                "source_url_fragment": "QUY%204/BSR_Baocaotaichinh_Q4_2025_Hopnhat.pdf",
                "changed_field": "operating_cash_flow_ytd",
            },
            "2025-Q2": {
                "operating_cash_flow_ytd": 3007957,
                "investing_cash_flow_ytd": -10495574,
                "net_cash_change_ytd": -11998302,
                "source_url_fragment": "QUY%202/BSR_Baocaotaichinh_Q2_2026_Hopnhat.pdf",
                "changed_field": "investing_cash_flow_ytd",
            },
        }
        for period, controls in expected.items():
            row = self.rows[period]
            rec = row["cashflow_source_reconciliation"]
            audit = row["cashflow_audit_revision"]
            with self.subTest(period=period):
                self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
                self.assertIn(controls["source_url_fragment"], audit["selected_source_url"])
                self.assertTrue(audit["previous_values_raw_vnd"])
                difference = audit["relative_differences_percent"][controls["changed_field"]]
                self.assertGreater(difference["relative_difference_percent"], 0.01)
                for field, value in controls.items():
                    if field.endswith("_ytd") and field in row:
                        self.assertEqual(row[field], value)

    def test_bsr_q3_2025_cash_ending_and_2026_q1_cross_year_opening(self):
        q3_2025 = self.rows["2025-Q3"]
        self.assertEqual(q3_2025["cash_ending_reported_ytd"], 11009664)
        self.assertEqual(q3_2025["cashflow_audit_revision"]["visual_review"],
                         "visually_checked_balance_formula_reconciled")
        q4_2025 = self.rows["2025-Q4"]
        q1_2026 = self.rows["2026-Q1"]
        self.assertEqual(q4_2025["cash_ending"], 7625816)
        self.assertEqual(q1_2026["cash_beginning"], 7625823)
        continuity = q1_2026["cashflow_source_reconciliation"]["cross_period_cash_continuity"]
        self.assertEqual(continuity["residual_million_vnd"], 7)
        self.assertLessEqual(continuity["relative_difference_percent"], 0.01)
        self.assertEqual(continuity["status"], "ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT")
        self.assertEqual(self.rows["2026-Q2"]["net_cash_change_ytd"], -898789)
        self.assertEqual(self.rows["2026-Q2"]["cash_ending_reported_ytd"], 6659657)
        self.assertEqual(
            self.rows["2026-Q2"]["cashflow_source_reconciliation"]["visual_review"],
            "ocr_text_reconciled_visual_review_pending",
        )




class VHMCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for the VHM 2024-Q1 to 2026-Q2 consolidated cash-flow series."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-VHM.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.flow_fields = (
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "net_cash_change",
        )
        cls.core_fields = (
            *cls.flow_fields,
            "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd",
            "cash_beginning", "cash_ending",
            "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "cashflow_period_basis",
        )

    def test_vhm_all_ten_periods_reconcile_at_source_precision(self):
        self.assertEqual(set(self.rows), {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2",
        })
        index_url = "https://finance.vietstock.vn/VHM/tai-tai-lieu.htm?doctype=1"
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], index_url)
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertTrue(row["cashflow_source_reconciliation"]["selected_values_not_adjusted_for_tolerance"])
                self.assertEqual(row["cashflow_source_reconciliation"]["relative_tolerance_percent"], 0.01)
                for field in self.core_fields:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                    if field != "cashflow_period_basis":
                        self.assertIsInstance(row.get(field), (int, float))
                        self.assertNotIsInstance(row.get(field), bool)

                # VHM source amounts under 'Triệu VND' use dot-grouped integer millions; preserve integer-million values exactly.
                # Preserve reported precision; do not round components independently or add a plug.
                ytd_component_sum = (
                    row["operating_cash_flow_ytd"] +
                    row["investing_cash_flow_ytd"] +
                    row["financing_cash_flow_ytd"]
                )
                quarter_component_sum = (
                    row["operating_cash_flow"] +
                    row["investing_cash_flow"] +
                    row["financing_cash_flow"]
                )
                rec = row["cashflow_source_reconciliation"]
                if period == "2026-Q2":
                    # Source PDF visibly reports line 40 = 68,675,210 and line 50 = 4,092,385 (Triệu VND).
                    # The >0.01% mismatch is a source-report exception: retain both rows, no plug.
                    self.assertAlmostEqual(ytd_component_sum - row["net_cash_change_ytd"], -1000000.0, places=6)
                    self.assertAlmostEqual(quarter_component_sum - row["net_cash_change"], -1000000.0, places=6)
                    self.assertGreater(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                    self.assertGreater(rec["quarter_flow_components_relative_difference_percent"], 0.01)
                    self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT")
                    self.assertEqual(rec["source_component_sum_exception"]["row_40_financing_cash_flow_ytd"], 68675210)
                    self.assertEqual(rec["source_component_sum_exception"]["row_50_reported_net_cash_change_ytd"], 4092385)
                else:
                    self.assertAlmostEqual(ytd_component_sum, row["net_cash_change_ytd"], places=7)
                    self.assertAlmostEqual(quarter_component_sum, row["net_cash_change"], places=7)
                    self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                    self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(
                    row["cashflow_source_reconciliation"]["ytd_cash_bridge_relative_difference_percent"],
                    0.01
                )
                self.assertLessEqual(
                    row["cashflow_source_reconciliation"]["quarter_cash_bridge_relative_difference_percent"],
                    0.01
                )
                self.assertAlmostEqual(
                    row["cash_ending_reported_ytd"] -
                    row["cash_beginning_reported_ytd"] -
                    row["net_cash_change_ytd"],
                    0, places=7
                )
                self.assertAlmostEqual(cash_bridge_delta(row), 0, places=7)

                # These statements do not show a separate FX cash-movement row.
                # Leave FX fields blank instead of manufacturing an adjustment.
                self.assertIsNone(row.get("foreign_exchange_effect"))
                self.assertIsNone(row.get("foreign_exchange_effect_ytd"))
                self.assertNotIn("foreign_exchange_effect", row["financial_line_items_extracted_fields"])
                self.assertNotIn("foreign_exchange_effect_ytd", row["financial_line_items_extracted_fields"])
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["foreign_exchange_effect_source_status"],
                    "not_reported_separately"
                )

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for field in self.flow_fields:
                        self.assertAlmostEqual(row[field], row[field + "_ytd"], places=7)
                else:
                    previous = self.rows[f"{year}-Q{q-1}"]
                    for field in self.flow_fields:
                        self.assertAlmostEqual(
                            row[field],
                            row[field + "_ytd"] - previous[field + "_ytd"],
                            places=7
                        )
                    self.assertAlmostEqual(row["cash_beginning"], previous["cash_ending"], places=7)

    def test_vhm_later_h1_comparatives_preserve_material_source_reclassifications(self):
        h1_2024 = self.rows["2024-Q2"]
        audit_2024 = h1_2024["cashflow_audit_revision"]
        rec_2024 = h1_2024["cashflow_source_reconciliation"]
        self.assertIn("QUY%202/VHM_Baocaotaichinh_Q2_2025_Hopnhat.pdf", audit_2024["selected_source_url"])
        self.assertEqual(rec_2024["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        old_2024 = audit_2024["previous_source_values_million_vnd"]
        new_2024 = audit_2024["selected_source_values_million_vnd"]
        self.assertEqual(old_2024["operating_cash_flow_ytd"], 6474315)
        self.assertEqual(new_2024["operating_cash_flow_ytd"], -10945610)
        self.assertGreater(audit_2024["relative_differences_percent"]["operating_cash_flow_ytd"]["relative_difference_percent"], 0.01)
        self.assertTrue(within_relative_tolerance(old_2024["net_cash_change_ytd"], new_2024["net_cash_change_ytd"]))
        self.assertTrue(within_relative_tolerance(old_2024["cash_ending_reported_ytd"], new_2024["cash_ending_reported_ytd"]))

        h1_2025 = self.rows["2025-Q2"]
        audit_2025 = h1_2025["cashflow_audit_revision"]
        rec_2025 = h1_2025["cashflow_source_reconciliation"]
        self.assertIn("QUY%202/VHM_Baocaotaichinh_Q2_2026_Hopnhat.pdf", audit_2025["selected_source_url"])
        self.assertEqual(rec_2025["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        old_2025 = audit_2025["previous_source_values_million_vnd"]
        new_2025 = audit_2025["selected_source_values_million_vnd"]
        self.assertEqual(old_2025["operating_cash_flow_ytd"], 50458755)
        self.assertEqual(new_2025["operating_cash_flow_ytd"], 41093814)
        self.assertGreater(audit_2025["relative_differences_percent"]["investing_cash_flow_ytd"]["relative_difference_percent"], 0.01)
        self.assertTrue(within_relative_tolerance(old_2025["net_cash_change_ytd"], new_2025["net_cash_change_ytd"]))
        self.assertTrue(within_relative_tolerance(old_2025["cash_ending_reported_ytd"], new_2025["cash_ending_reported_ytd"]))

    def test_vhm_q1_2026_cross_year_cash_difference_over_tolerance_is_preserved(self):
        prior = self.rows["2025-Q4"]
        current = self.rows["2026-Q1"]
        rec = current["cashflow_source_reconciliation"]["cross_period_cash_continuity"]
        self.assertEqual(prior["cash_ending"], 49948510)
        self.assertEqual(current["cash_beginning"], 49086598)
        self.assertAlmostEqual(rec["residual_million_vnd"], -861912, places=7)
        self.assertGreater(rec["relative_difference_percent"], 0.01)
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT")
        self.assertEqual(
            current["cashflow_source_reconciliation"]["status"],
            "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT"
        )

    def test_vhm_h1_2026_cashflow_components_are_source_supported(self):
        row = self.rows["2026-Q2"]
        self.assertEqual(row["operating_cash_flow_ytd"], 88467954)
        self.assertEqual(row["investing_cash_flow_ytd"], -154050779)
        self.assertEqual(row["financing_cash_flow_ytd"], 68675210)
        self.assertEqual(row["net_cash_change_ytd"], 4092385)
        self.assertEqual(
            row["cashflow_source_reconciliation"]["status"],
            "NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT",
        )
        self.assertAlmostEqual(
            row["cashflow_source_reconciliation"]["source_component_sum_exception"]["ytd_component_sum_residual_million_vnd"],
            -1000000, places=6
        )
        self.assertEqual(row["cash_beginning_reported_ytd"], 49086598)
        self.assertEqual(row["cash_ending_reported_ytd"], 53178983)
        self.assertEqual(
            row["cashflow_source_reconciliation"]["visual_review"],
            "visually_checked_source_line_40_68_675_210_component_sum_conflict_flagged",
        )




class TPBCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for TPB quarterly and YTD cash-flow figures sourced from VietstockFinance."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-TPB.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.flow_fields = (
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "net_cash_change",
        )
        cls.core_fields = (
            *cls.flow_fields,
            "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd",
            "cash_beginning", "cash_ending",
            "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
            "cashflow_period_basis",
        )

    def test_tpb_all_ten_periods_reconcile_with_fx_and_ytd_difference(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), expected_periods)
        index_url = "https://finance.vietstock.vn/TPB/tai-tai-lieu.htm?doctype=1"
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], index_url)
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["cashflow_source_reconciliation"]["relative_tolerance_percent"], 0.01)
                self.assertTrue(row["cashflow_source_reconciliation"]["selected_values_not_adjusted_for_tolerance"])
                for field in self.core_fields:
                    self.assertIn(field, row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                    if field != "cashflow_period_basis":
                        self.assertIsInstance(row.get(field), (int, float))
                        self.assertNotIsInstance(row.get(field), bool)

                # TPB reports integer million VND; all source bridge equations must reconcile.
                self.assertEqual(
                    row["operating_cash_flow_ytd"] +
                    row["investing_cash_flow_ytd"] +
                    row["financing_cash_flow_ytd"],
                    row["net_cash_change_ytd"],
                )
                self.assertEqual(
                    row["operating_cash_flow"] +
                    row["investing_cash_flow"] +
                    row["financing_cash_flow"],
                    row["net_cash_change"],
                )
                self.assertEqual(
                    row["cash_ending_reported_ytd"] -
                    row["cash_beginning_reported_ytd"] -
                    row["net_cash_change_ytd"] -
                    row["foreign_exchange_effect_ytd"],
                    0,
                )
                self.assertEqual(
                    row["cash_ending"] - row["cash_beginning"] -
                    row["net_cash_change"] - row["foreign_exchange_effect"],
                    0,
                )
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(rec["ytd_flow_components_residual"], 0)
                self.assertEqual(rec["quarter_flow_components_residual"], 0)
                self.assertEqual(rec["ytd_cash_bridge_residual"], 0)
                self.assertEqual(rec["quarter_cash_bridge_residual"], 0)
                self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for field in self.flow_fields:
                        self.assertEqual(row[field], row[field + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"], row["foreign_exchange_effect_ytd"])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for field in self.flow_fields:
                        self.assertEqual(row[field], row[field + "_ytd"] - prior[field + "_ytd"])
                    self.assertEqual(
                        row["foreign_exchange_effect"],
                        row["foreign_exchange_effect_ytd"] - prior["foreign_exchange_effect_ytd"],
                    )
                    self.assertEqual(row["cash_beginning"], prior["cash_ending"])

    def test_tpb_later_h1_2024_comparator_records_material_cfi_reclassification(self):
        row = self.rows["2024-Q2"]
        audit = row["cashflow_audit_revision"]
        rec = row["cashflow_source_reconciliation"]
        self.assertIn("QUY%202/TPB_Baocaotaichinh_Q2_2025_Hopnhat.pdf", audit["selected_source_url"])
        self.assertIn("TPB_Baocaotaichinh_Q2_2024_Hopnhat.zip", audit["previous_source_url"])
        self.assertEqual(row["investing_cash_flow_ytd"], -223559)
        self.assertEqual(row["net_cash_change_ytd"], 5449243)
        self.assertEqual(audit["previous_source_values_million_vnd"]["investing_cash_flow_ytd"], -201252)
        self.assertGreater(
            audit["relative_differences_percent"]["investing_cash_flow_ytd"]["relative_difference_percent"],
            0.01,
        )
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(row["cash_ending_reported_ytd"], 50890845)

    def test_tpb_fy2024_later_comparator_preserves_cff_reclassification(self):
        row = self.rows["2024-Q4"]
        audit = row["cashflow_audit_revision"]
        rec = row["cashflow_source_reconciliation"]
        self.assertIn("QUY%204/TPB_Baocaotaichinh_Q4_2025_Hopnhat.pdf", audit["selected_source_url"])
        self.assertEqual(row["operating_cash_flow_ytd"], 40343273)
        self.assertEqual(row["investing_cash_flow_ytd"], -399918)
        self.assertEqual(row["financing_cash_flow_ytd"], 763682)
        self.assertEqual(row["net_cash_change_ytd"], 40707037)
        old = audit["previous_source_values_million_vnd"]
        self.assertEqual(old["financing_cash_flow_ytd"], 764198)
        self.assertGreater(
            audit["relative_differences_percent"]["financing_cash_flow_ytd"]["relative_difference_percent"],
            0.01,
        )
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(row["cash_ending_reported_ytd"], 86148639)

    def test_tpb_source_visual_review_is_explicit_for_remaining_large_reports(self):
        for period in ("2025-Q4", "2026-Q1", "2026-Q2"):
            with self.subTest(period=period):
                row = self.rows[period]
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["visual_review"],
                    "ocr_text_reconciled_visual_review_pending",
                )
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["status"],
                    "NEEDS_MANUAL_REVIEW_SOURCE_VISUAL_PENDING",
                )

    def test_tpb_h1_2026_ytd_fields_match_reported_rows(self):
        row = self.rows["2026-Q2"]
        self.assertEqual(row["operating_cash_flow_ytd"], -16932973)
        self.assertEqual(row["investing_cash_flow_ytd"], -127716)
        self.assertEqual(row["financing_cash_flow_ytd"], -1663300)
        self.assertEqual(row["net_cash_change_ytd"], -18723989)
        self.assertEqual(row["cash_beginning_reported_ytd"], 115747324)
        self.assertEqual(row["cash_ending_reported_ytd"], 97023335)


class VPBCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for VPB consolidated cash flow, source comparatives and OCR holdback."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-VPB.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.flow_fields = (
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "net_cash_change",
        )
        cls.ytd_fields = tuple(field + "_ytd" for field in cls.flow_fields)
        cls.index_url = "https://finance.vietstock.vn/VPB/tai-tai-lieu.htm?doctype=1"

    def test_vpb_11_periods_have_source_trace_and_reconcile_except_explicit_h1_2026_holdback(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2", "2026-Q3",
        }
        self.assertEqual(set(self.rows), expected_periods)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], self.index_url)
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(rec["source_index_url"], self.index_url)
                self.assertEqual(rec["relative_tolerance_percent"], 0.01)
                self.assertFalse(rec["separate_fx_line_reported"])
                self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])
                self.assertTrue(rec["source_url"].startswith("https://"))
                self.assertTrue(rec["source_archive_file"].startswith("reports/raw/VPB/"))
                self.assertIn("source_pdf_pages", rec)
                self.assertNotIn("foreign_exchange_effect", row.get("financial_line_items_extracted_fields", []))
                self.assertNotIn("foreign_exchange_effect_ytd", row.get("financial_line_items_extracted_fields", []))

                # Cash flow values are explicitly allow-listed only when the source-backed value exists.
                extracted = set(row.get("financial_line_items_extracted_fields", []))
                for field in ("cashflow_period_basis",):
                    self.assertIn(field, extracted)
                for field in self.flow_fields + self.ytd_fields:
                    if period == "2026-Q2" and field in ("net_cash_change", "net_cash_change_ytd"):
                        self.assertNotIn(field, extracted)
                        self.assertIn(field, row.get("financial_line_items_rejected_fields", []))
                        self.assertIsNone(row.get(field))
                    else:
                        self.assertIsInstance(row.get(field), (int, float))
                        self.assertNotIsInstance(row.get(field), bool)
                        self.assertIn(field, extracted)
                        self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))

                if period != "2026-Q2":
                    self.assertEqual(
                        row["operating_cash_flow_ytd"] +
                        row["investing_cash_flow_ytd"] +
                        row["financing_cash_flow_ytd"],
                        row["net_cash_change_ytd"],
                    )
                    self.assertEqual(
                        row["operating_cash_flow"] +
                        row["investing_cash_flow"] +
                        row["financing_cash_flow"],
                        row["net_cash_change"],
                    )
                    self.assertEqual(rec["ytd_flow_components_residual"], 0)
                    self.assertEqual(rec["quarter_flow_components_residual"], 0)
                    self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"], 0.01)
                    self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"], 0.01)

                if all(isinstance(row.get(k), (int, float)) and not isinstance(row.get(k), bool)
                       for k in ("cash_beginning_reported_ytd", "cash_ending_reported_ytd",
                                 "net_cash_change_ytd")):
                    self.assertEqual(
                        row["cash_ending_reported_ytd"] -
                        row["cash_beginning_reported_ytd"] -
                        row["net_cash_change_ytd"], 0
                    )
                    self.assertEqual(rec["ytd_cash_bridge_residual"], 0)

                if all(isinstance(row.get(k), (int, float)) and not isinstance(row.get(k), bool)
                       for k in ("cash_beginning", "cash_ending", "net_cash_change")):
                    self.assertEqual(
                        row["cash_ending"] - row["cash_beginning"] -
                        row["net_cash_change"], 0
                    )
                    self.assertEqual(rec["quarter_cash_bridge_residual"], 0)

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for flow in self.flow_fields:
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for flow in self.flow_fields[:3]:
                        self.assertEqual(row[flow],
                                         row[flow + "_ytd"] - prior[flow + "_ytd"])
                    # Q2/2026's net YTD is withheld due a >0.01% OCR/source-total mismatch.
                    # Q3/2026 net is transparently derived from its three component deltas.
                    if (period != "2026-Q2" and period != "2026-Q3"
                            and isinstance(prior.get("net_cash_change_ytd"), (int, float))):
                        self.assertEqual(row["net_cash_change"],
                                         row["net_cash_change_ytd"] -
                                         prior["net_cash_change_ytd"])

                if period not in ("2026-Q2", "2026-Q3"):
                    self.assertEqual(
                        row["cash_beginning"], row["cash_beginning_reported_ytd"]
                        if q == 1 else self.rows[f"{year}-Q{q-1}"]["cash_ending"]
                    )

    def test_vpb_later_comparatives_correct_prior_cashflow_mapping(self):
        q1_2024 = self.rows["2024-Q1"]
        self.assertEqual(q1_2024["operating_cash_flow_ytd"], -5358644)
        self.assertEqual(q1_2024["investing_cash_flow_ytd"], -69)
        self.assertEqual(q1_2024["financing_cash_flow_ytd"], 0)
        self.assertEqual(q1_2024["net_cash_change_ytd"], -5358713)
        self.assertIn("Q1_2025", q1_2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertEqual(
            q1_2024["cashflow_audit_revision"]["previous_snapshot_values"]["operating_cash_flow"],
            6834558,
        )

        h1_2024 = self.rows["2024-Q2"]
        self.assertEqual(h1_2024["operating_cash_flow_ytd"], 16535602)
        self.assertEqual(h1_2024["investing_cash_flow_ytd"], -565)
        self.assertEqual(h1_2024["financing_cash_flow_ytd"], -7935139)
        self.assertEqual(h1_2024["net_cash_change_ytd"], 8599898)
        self.assertIn("Q2_2025", h1_2024["cashflow_audit_revision"]["selected_source_url"])

        fy2024 = self.rows["2024-Q4"]
        self.assertEqual(fy2024["operating_cash_flow_ytd"], 57316185)
        self.assertEqual(fy2024["investing_cash_flow_ytd"], -45039)
        self.assertEqual(fy2024["financing_cash_flow_ytd"], -7935832)
        self.assertEqual(fy2024["net_cash_change_ytd"], 49335314)
        self.assertEqual(fy2024["cash_ending_reported_ytd"], 143002784)
        self.assertEqual(fy2024["cashflow_source_reconciliation"]["source_visual_review"],
                         "source_pdf_pages_visually_checked")

        h1_2025 = self.rows["2025-Q2"]
        self.assertEqual(h1_2025["operating_cash_flow_ytd"], 23353876)
        self.assertEqual(h1_2025["investing_cash_flow_ytd"], -29653)
        self.assertEqual(h1_2025["financing_cash_flow_ytd"], -3968172)
        self.assertEqual(h1_2025["net_cash_change_ytd"], 19356051)
        self.assertIn("Q2_2026", h1_2025["cashflow_audit_revision"]["selected_source_url"])

    def test_vpb_h1_2026_ocr_total_mismatch_is_withheld_not_plugged(self):
        row = self.rows["2026-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(row["operating_cash_flow_ytd"], 42064417)
        self.assertEqual(row["investing_cash_flow_ytd"], -1149285)
        self.assertEqual(row["financing_cash_flow_ytd"], -3965367)
        self.assertEqual(row["operating_cash_flow_ytd"] +
                         row["investing_cash_flow_ytd"] +
                         row["financing_cash_flow_ytd"], 36949765)
        candidate = row["financial_line_items_rejected_values"]["net_cash_change_ytd"]["value"]
        self.assertEqual(candidate, 6949765)
        self.assertEqual(rec["ytd_flow_components_residual"], 30000000)
        self.assertGreater(rec["ytd_flow_components_relative_difference_percent"], 0.01)
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT")
        self.assertIsNone(row["net_cash_change_ytd"])
        self.assertIsNone(row["net_cash_change"])
        self.assertIsNone(row["cash_ending_reported_ytd"])
        self.assertIsNone(row["cash_ending"])
        self.assertTrue(row["cashflow_audit_revision"]["source_visual_review"]
                        == "ocr_text_reconciled_visual_review_pending")
        self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])

    def test_vpb_q3_2026_ytd_reconciles_but_quarter_opening_waits_for_h1_2026_review(self):
        row = self.rows["2026-Q3"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(row["operating_cash_flow_ytd"], 46180388)
        self.assertEqual(row["investing_cash_flow_ytd"], -11841627)
        self.assertEqual(row["financing_cash_flow_ytd"], -3965367)
        self.assertEqual(row["net_cash_change_ytd"], 30373394)
        self.assertEqual(row["cash_beginning_reported_ytd"], 196097219)
        self.assertEqual(row["cash_ending_reported_ytd"], 226470613)
        self.assertEqual(rec["ytd_cash_bridge_residual"], 0)
        self.assertEqual(row["operating_cash_flow"], 4115971)
        self.assertEqual(row["investing_cash_flow"], -10692342)
        self.assertEqual(row["financing_cash_flow"], 0)
        self.assertEqual(row["net_cash_change"], -6576371)
        self.assertIsNone(row["cash_beginning"])
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_PRIOR_Q2_2026_CASH_BASIS_PENDING")
        self.assertIn("sum of source-backed", row["net_cash_change_calculation"])


class STBCashFlowNormalizationTests(unittest.TestCase):
    """Regression tests for STB source totals, YTD-quarter math and the 0.01% tolerance."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot=json.loads(
            (ROOT / "data" / "financials-STB.json").read_text(encoding="utf-8")
        )
        cls.rows={row["period"]:row for row in cls.snapshot["items"]}
        cls.flow_fields=("operating_cash_flow","investing_cash_flow","financing_cash_flow","net_cash_change")
        cls.index_url="https://finance.vietstock.vn/STB/tai-tai-lieu.htm?doctype=1"

    def test_stb_all_ten_periods_reconcile_with_fx_and_relative_tolerance(self):
        expected={
            "2024-Q1","2024-Q2","2024-Q3","2024-Q4",
            "2025-Q1","2025-Q2","2025-Q3","2025-Q4",
            "2026-Q1","2026-Q2",
        }
        self.assertEqual(set(self.rows),expected)
        core=(
            "operating_cash_flow","investing_cash_flow","financing_cash_flow","net_cash_change",
            "operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd",
            "net_cash_change_ytd","cash_beginning","cash_ending",
            "cash_beginning_reported_ytd","cash_ending_reported_ytd",
            "foreign_exchange_effect","foreign_exchange_effect_ytd","cashflow_period_basis",
        )
        for period,row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["unit"],"triệu VND")
                self.assertEqual(row["source_index_url"],self.index_url)
                self.assertEqual(row["cashflow_period_basis"],"year_to_date")
                rec=row["cashflow_source_reconciliation"]
                self.assertEqual(rec["source_index_url"],self.index_url)
                self.assertEqual(rec["relative_tolerance_percent"],0.01)
                self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])
                self.assertTrue(rec["separate_fx_line_reported"])
                self.assertTrue(rec["source_url"].startswith("https://"))
                self.assertTrue(rec["source_archive_file"].startswith("reports/raw/STB/"))
                for field in core:
                    self.assertIn(field,row["financial_line_items_extracted_fields"])
                    self.assertNotIn(field,row.get("financial_line_items_rejected_fields",[]))
                    if field!="cashflow_period_basis":
                        self.assertIsInstance(row.get(field),(int,float))
                        self.assertNotIsInstance(row.get(field),bool)

                self.assertEqual(
                    row["cash_ending_reported_ytd"]-row["cash_beginning_reported_ytd"]-
                    row["net_cash_change_ytd"]-row["foreign_exchange_effect_ytd"],
                    rec["ytd_cash_bridge_residual"],
                )
                self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"],0.01)
                self.assertEqual(
                    row["cash_ending"]-row["cash_beginning"]-
                    row["net_cash_change"]-row["foreign_exchange_effect"],
                    rec["quarter_cash_bridge_residual"],
                )
                self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"],0.01)

                # The one out-of-tolerance mismatch is retained as review, not treated as pass.
                if period=="2026-Q2":
                    self.assertEqual(
                        row["operating_cash_flow_ytd"]+
                        row["investing_cash_flow_ytd"]+
                        row["financing_cash_flow_ytd"],
                        -42997005,
                    )
                    self.assertEqual(row["net_cash_change_ytd"],-43097005)
                    self.assertEqual(rec["ytd_flow_components_residual"],100000)
                    self.assertAlmostEqual(rec["ytd_flow_components_relative_difference_percent"],0.2320346855,places=8)
                    self.assertGreater(rec["ytd_flow_components_relative_difference_percent"],0.01)
                    self.assertEqual(rec["status"],"NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT")
                    self.assertEqual(rec["quarter_flow_components_residual"],100000)
                    self.assertGreater(rec["quarter_flow_components_relative_difference_percent"],0.01)
                else:
                    self.assertEqual(
                        row["operating_cash_flow_ytd"]+
                        row["investing_cash_flow_ytd"]+
                        row["financing_cash_flow_ytd"],
                        row["net_cash_change_ytd"],
                    )
                    self.assertEqual(
                        row["operating_cash_flow"]+
                        row["investing_cash_flow"]+
                        row["financing_cash_flow"],
                        row["net_cash_change"],
                    )
                    self.assertEqual(rec["ytd_flow_components_residual"],0)
                    self.assertEqual(rec["quarter_flow_components_residual"],0)
                    self.assertLessEqual(rec["ytd_flow_components_relative_difference_percent"],0.01)
                    self.assertLessEqual(rec["quarter_flow_components_relative_difference_percent"],0.01)

                year,qstr=period.split("-Q");q=int(qstr)
                if q==1:
                    for flow in self.flow_fields:
                        self.assertEqual(row[flow],row[flow+"_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],row["foreign_exchange_effect_ytd"])
                else:
                    prior=self.rows[f"{year}-Q{q-1}"]
                    for flow in self.flow_fields:
                        self.assertEqual(row[flow],row[flow+"_ytd"]-prior[flow+"_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"]-prior["foreign_exchange_effect_ytd"])
                    self.assertEqual(row["cash_beginning"],prior["cash_ending"])

    def test_stb_h1_2024_later_comparative_reclassification_is_over_001_percent(self):
        row=self.rows["2024-Q2"]
        rec=row["cashflow_source_reconciliation"]
        audit=row["cashflow_audit_revision"]
        self.assertIn("Q2_2025",audit["selected_source_url"])
        diffs=audit["previous_source_comparison"]
        self.assertEqual(row["operating_cash_flow_ytd"],27113464)
        self.assertEqual(row["investing_cash_flow_ytd"],-418378)
        self.assertEqual(row["financing_cash_flow_ytd"],-2267691)
        self.assertEqual(row["net_cash_change_ytd"],24427395)
        self.assertGreater(diffs["operating_cash_flow_ytd"]["relative_difference_percent"],0.01)
        self.assertGreater(diffs["investing_cash_flow_ytd"]["relative_difference_percent"],0.01)
        self.assertEqual(rec["status"],"NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")

    def test_stb_q3_2024_fx_source_revision_is_traced_and_cash_bridge_residual_within_tolerance(self):
        row=self.rows["2024-Q3"]
        rec=row["cashflow_source_reconciliation"]
        audit=row["cashflow_audit_revision"]
        self.assertIn("Q3_2025",audit["selected_source_url"])
        self.assertEqual(row["foreign_exchange_effect_ytd"],-8227)
        self.assertEqual(audit["previous_source_comparison"]["foreign_exchange_effect_ytd"]["previous_value"],-6227)
        self.assertEqual(rec["ytd_cash_bridge_residual"],2000)
        self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"],0.01)
        self.assertEqual(rec["quarter_cash_bridge_residual"],2000)
        self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"],0.01)
        self.assertEqual(rec["status"],"NEEDS_MANUAL_REVIEW_SOURCE_FX_RECLASS_GT_0_01_PERCENT")

    def test_stb_fy2024_comparative_differences_under_tolerance_are_accepted_without_plug(self):
        row=self.rows["2024-Q4"]
        rec=row["cashflow_source_reconciliation"]
        audit=row["cashflow_audit_revision"]
        self.assertIn("Q4_2025",audit["selected_source_url"])
        self.assertEqual(row["operating_cash_flow_ytd"],38365249)
        self.assertEqual(row["investing_cash_flow_ytd"],-1007900)
        self.assertEqual(row["financing_cash_flow_ytd"],-1459275)
        self.assertEqual(row["net_cash_change_ytd"],35898074)
        self.assertLessEqual(audit["previous_source_comparison"]["operating_cash_flow_ytd"]["relative_difference_percent"],0.01)
        self.assertLessEqual(audit["previous_source_comparison"]["financing_cash_flow_ytd"]["relative_difference_percent"],0.01)
        self.assertEqual(rec["ytd_cash_bridge_residual"],0)
        self.assertEqual(rec["quarter_cash_bridge_residual"],-2000)
        self.assertLessEqual(rec["quarter_cash_bridge_relative_difference_percent"],0.01)

    def test_stb_q3_2025_fx_ocr_correction_is_source_traced(self):
        row=self.rows["2025-Q3"]
        correction=row["cashflow_audit_revision"]["prior_non_null_values_corrected"]["foreign_exchange_effect_ytd"]
        self.assertEqual(row["foreign_exchange_effect_ytd"],166291)
        self.assertEqual(correction["previous_value"],198218)
        self.assertEqual(correction["new_value"],166291)
        self.assertEqual(row["net_cash_change_ytd"],31075195)
        self.assertEqual(row["cash_ending_reported_ytd"],137734541)
        self.assertEqual(row["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"],0)
        self.assertEqual(row["cashflow_source_reconciliation"]["source_visual_review"],"source_pdf_pages_visually_checked")

    def test_stb_q2_2026_source_flow_mismatch_above_001_percent_is_not_silently_passed(self):
        row=self.rows["2026-Q2"]
        rec=row["cashflow_source_reconciliation"]
        self.assertEqual(row["net_cash_change_ytd"],-43097005)
        self.assertEqual(rec["ytd_flow_components_residual"],100000)
        self.assertGreater(rec["ytd_flow_components_relative_difference_percent"],0.01)
        self.assertEqual(rec["status"],"NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT")
        self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])
        self.assertEqual(rec["ytd_cash_bridge_residual"],0)
        self.assertEqual(rec["quarter_cash_bridge_residual"],0)




class CTGCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for the source-reconciled CTG cash-flow series."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-CTG.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_ctg_all_ten_periods_reconcile_and_quarter_equals_ytd_delta(self):
        core = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
            "cashflow_period_basis",
        )
        periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), periods)
        self.assertEqual(len(self.rows), 10)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["operating_cash_flow_ytd"] +
                                 row["investing_cash_flow_ytd"] +
                                 row["financing_cash_flow_ytd"],
                                 row["net_cash_change_ytd"])
                self.assertEqual(row["operating_cash_flow"] +
                                 row["investing_cash_flow"] +
                                 row["financing_cash_flow"],
                                 row["net_cash_change"])
                self.assertEqual(row["cash_ending_reported_ytd"] -
                                 row["cash_beginning_reported_ytd"] -
                                 row["net_cash_change_ytd"] -
                                 row["foreign_exchange_effect_ytd"], 0)
                self.assertEqual(cash_bridge_delta(row), 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"], 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["quarter_cash_bridge_residual"], 0)
                review = row["cashflow_audit_revision"].get("source_basis_review") or {}
                self.assertEqual(row["cashflow_source_reconciliation"]["status"],
                                 review.get("status", row["cashflow_source_reconciliation"]["status"]))
                self.assertTrue(all(field in row["financial_line_items_extracted_fields"]
                                    for field in core))
                self.assertTrue(all(field not in row.get("financial_line_items_rejected_fields", [])
                                    for field in core))
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["source_index_url"],
                    "https://finance.vietstock.vn/CTG/tai-tai-lieu.htm?doctype=1",
                )

                year, quarter_s = period.split("-Q")
                quarter = int(quarter_s)
                if quarter == 1:
                    for field in ("operating_cash_flow", "investing_cash_flow",
                                  "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[field], row[field + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"])
                    prior_year = self.rows.get(f"{int(year)-1}-Q4")
                    if prior_year:
                        self.assertEqual(row["cash_beginning"], prior_year["cash_ending"])
                else:
                    prior = self.rows[f"{year}-Q{quarter-1}"]
                    for field in ("operating_cash_flow", "investing_cash_flow",
                                  "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[field],
                                         row[field + "_ytd"] - prior[field + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"] -
                                     prior["foreign_exchange_effect_ytd"])
                    self.assertEqual(row["cash_beginning"], prior["cash_ending"])

    def test_ctg_later_comparatives_and_source_exceptions_are_traced(self):
        expectations = {
            "2024-Q2": (84384453, -427675, 1537, 83958315,
                        "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT"),
            "2024-Q3": (100518480, -606368, 1537, 99913649,
                        "NEEDS_MANUAL_REVIEW_SOURCE_NET_ROW_DIFF_GT_0_01_PERCENT"),
            "2024-Q4": (102188686, -1329023, 1537, 100861200,
                        "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT"),
            "2025-Q2": (18255640, -581917, 0, 17673723,
                        "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT"),
            "2025-Q3": (85022836, -1154686, 0, 83868150,
                        "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT"),
        }
        for period, expected in expectations.items():
            with self.subTest(period=period):
                row = self.rows[period]
                self.assertEqual(tuple(row[k] for k in (
                    "operating_cash_flow_ytd", "investing_cash_flow_ytd",
                    "financing_cash_flow_ytd", "net_cash_change_ytd",
                )), expected[:4])
                self.assertEqual(row["cashflow_source_reconciliation"]["status"], expected[4])
                self.assertTrue(row["cashflow_audit_revision"]["selected_source_url"].startswith(
                    "https://static2.vietstock.vn/data/HOSE/"))
                self.assertTrue(row["cashflow_source_reconciliation"]["source_basis_review"]["reason"])
                self.assertIsNotNone(row["cashflow_audit_revision"]["previous_source_basis"])

    def test_ctg_q1_2026_cash_ending_uses_direct_pdf_visual_correction(self):
        row = self.rows["2026-Q1"]
        self.assertEqual(row["cash_ending_reported_ytd"], 578995009)
        self.assertEqual(row["cash_ending"], 578995009)
        correction = row["cashflow_source_reconciliation"]["source_ocr_correction"]
        self.assertEqual(correction["old"], 578095009)
        self.assertEqual(correction["new"], 578995009)
        self.assertEqual(correction["page"], 11)
        self.assertEqual(correction["unit"], "triệu VND")
        self.assertEqual(row["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"], 0)
        self.assertEqual(cash_bridge_delta(row), 0)
        self.assertTrue(within_relative_tolerance(578995009, 578995009))




class BIDCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for BID consolidated cash-flow normalization."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-BID.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_bid_all_ten_periods_reconcile_with_selected_ytd_basis(self):
        periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        flows = ("operating_cash_flow", "investing_cash_flow",
                 "financing_cash_flow", "net_cash_change")
        core = (*flows, *(field + "_ytd" for field in flows),
                "cash_beginning", "cash_ending", "cash_beginning_reported_ytd",
                "cash_ending_reported_ytd", "foreign_exchange_effect",
                "foreign_exchange_effect_ytd", "cashflow_period_basis")
        self.assertEqual(set(self.rows), periods)
        self.assertEqual(len(self.rows), 10)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertTrue(all(field in row["financial_line_items_extracted_fields"]
                                    for field in core))
                self.assertTrue(all(field not in row.get("financial_line_items_rejected_fields", [])
                                    for field in core))
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/BID/tai-tai-lieu.htm?doctype=1")
                self.assertEqual(row["foreign_exchange_effect"], None)
                self.assertEqual(row["foreign_exchange_effect_ytd"], None)
                self.assertEqual(row["cashflow_source_reconciliation"]["fx_line_present"], False)
                self.assertEqual(row["operating_cash_flow"] +
                                 row["investing_cash_flow"] +
                                 row["financing_cash_flow"], row["net_cash_change"])
                self.assertEqual(row["operating_cash_flow_ytd"] +
                                 row["investing_cash_flow_ytd"] +
                                 row["financing_cash_flow_ytd"], row["net_cash_change_ytd"])
                self.assertEqual(row["cash_ending_reported_ytd"] -
                                 row["cash_beginning_reported_ytd"] -
                                 row["net_cash_change_ytd"], 0)
                self.assertEqual(cash_bridge_delta(row), 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"], 0)
                self.assertEqual(row["cashflow_source_reconciliation"]["quarter_cash_bridge_residual"], 0)

                year, quarter_s = period.split("-Q")
                quarter = int(quarter_s)
                if quarter == 1:
                    for field in flows:
                        self.assertEqual(row[field], row[field + "_ytd"])
                else:
                    previous = self.rows[f"{year}-Q{quarter-1}"]
                    for field in flows:
                        self.assertEqual(row[field], row[field + "_ytd"] -
                                         previous[field + "_ytd"])
                    self.assertEqual(row["cash_beginning"], previous["cash_ending"])

    def test_bid_tolerance_is_relative_and_source_numbers_are_not_plugged(self):
        # Original-vs-later H1/2024 differences are below or equal to 0.01%.
        h12024 = self.rows["2024-Q2"]
        comparison = h12024["cashflow_audit_revision"]["previous_source_basis"]["relative_changes"]
        self.assertLessEqual(comparison["operating_cash_flow_ytd"]["relative_difference_percent"], 0.01)
        self.assertLessEqual(comparison["net_cash_change_ytd"]["relative_difference_percent"], 0.01)
        self.assertEqual(h12024["cashflow_source_reconciliation"]["status"],
                         "PASS_WITHIN_0_01_PERCENT_COMPARATIVE_DIFFERENCE_ACCEPTED")
        # The FY2024 source basis and H1/2025 CFI reclassification exceed tolerance and remain flagged.
        q42024 = self.rows["2024-Q4"]
        self.assertEqual(q42024["cashflow_source_reconciliation"]["status"],
                         "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(q42024["cashflow_audit_revision"]["previous_source_basis"]["ytd"], {
            "operating_cash_flow_ytd": 101080084,
            "investing_cash_flow_ytd": -1127413,
            "financing_cash_flow_ytd": -94460,
            "net_cash_change_ytd": 99858211,
        })
        h12025 = self.rows["2025-Q2"]
        self.assertEqual(h12025["cashflow_source_reconciliation"]["status"],
                         "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(h12025["cashflow_audit_revision"]["previous_source_basis"]["ytd"], {
            "operating_cash_flow_ytd": 90471834,
            "investing_cash_flow_ytd": -869550,
            "financing_cash_flow_ytd": 13196654,
            "net_cash_change_ytd": 102798938,
        })
        # The Q1/2026 opening differs from FY2025 close by 18,308 million VND,
        # which is less than 0.01%; source-reported balances remain unchanged.
        q12026 = self.rows["2026-Q1"]
        self.assertEqual(q12026["cash_beginning"], 530277690)
        self.assertEqual(self.rows["2025-Q4"]["cash_ending"], 530295998)
        self.assertEqual(q12026["cashflow_source_reconciliation"]
                         ["adjacent_quarter_cash_continuity_residual"], -18308)
        self.assertTrue(within_relative_tolerance(530277690, 530295998))
        self.assertEqual(q12026["cashflow_source_reconciliation"]["status"],
                         "PASS_WITHIN_0_01_PERCENT_CROSS_YEAR_OPENING_DIFFERENCE_ACCEPTED")

    def test_bid_last_period_uses_final_cfo_line_not_operating_subtotal(self):
        # The Q4/2025 CFO amount is the final net CFO line, not the subtotal before
        # movements in operating assets and liabilities.
        q42025 = self.rows["2025-Q4"]
        self.assertEqual(q42025["operating_cash_flow_ytd"], 192956384)
        self.assertEqual(q42025["investing_cash_flow_ytd"], -1638693)
        self.assertEqual(q42025["financing_cash_flow_ytd"], 14253843)
        self.assertEqual(q42025["net_cash_change_ytd"], 205571534)
        self.assertEqual(q42025["cash_ending_reported_ytd"], 530295998)
        self.assertEqual(q42025["cashflow_source_reconciliation"]["ytd_flow_sum_residual"], 0)
        # H1/2026 CFF OCR candidate has been corrected from 1,616,208 to 16,162,208
        # based on the printed total being required by the source's flow/net rows.
        h12026 = self.rows["2026-Q2"]
        self.assertEqual(h12026["financing_cash_flow_ytd"], 16162208)
        self.assertEqual(h12026["net_cash_change_ytd"], -8127461)
        self.assertEqual(h12026["cash_ending_reported_ytd"], 522150229)




class VIXCashFlowScopeGuardTests(unittest.TestCase):
    """Prevent VIX standalone/unconfirmed reports from entering consolidated cash-flow charts."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-VIX.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_vix_cashflow_fields_are_withheld_until_consolidation_scope_is_confirmed(self):
        fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
            "capital_expenditure", "capital_expenditure_ytd",
            "dividends_paid", "dividends_paid_ytd", "cashflow_period_basis",
        )
        self.assertEqual(len(self.rows), 11)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertTrue(all(row.get(field) is None for field in fields))
                self.assertFalse(row["cashflow_source_reconciliation"]["selected_for_consolidated_series"])
                self.assertTrue(row["cashflow_audit_revision"]["withheld_from_consolidated_cashflow"])
                self.assertEqual(
                    row["source_index_url"],
                    "https://finance.vietstock.vn/VIX/tai-tai-lieu.htm?doctype=1",
                )
                for field in fields:
                    if field != "cashflow_period_basis":
                        self.assertNotIn(field, row.get("financial_line_items_extracted_fields", []))
                        self.assertIn(field, row.get("financial_line_items_rejected_fields", []))

    def test_vix_previous_candidates_are_preserved_for_scope_review(self):
        explicitly_standalone = ("2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
                                 "2025-Q1", "2025-Q2", "2025-Q3")
        for period in explicitly_standalone:
            with self.subTest(period=period):
                row = self.rows[period]
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["status"],
                    "TERMINAL_MANUAL_REVIEW_SCOPE_NOT_CONSOLIDATED",
                )
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["source_scope_status"],
                    "confirmed_standalone",
                )
        for period in ("2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3"):
            with self.subTest(period=period):
                row = self.rows[period]
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["status"],
                    "TERMINAL_MANUAL_REVIEW_SCOPE_UNCONFIRMED",
                )
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["source_scope_status"],
                    "consolidation_scope_unconfirmed",
                )
        q12024 = self.rows["2024-Q1"]
        prior = q12024["cashflow_audit_revision"]["original_cashflow_candidates"]
        self.assertTrue(prior)
        self.assertTrue(any(
            isinstance(v, (int, float))
            for v in prior.values()
        ))

if __name__ == "__main__":
    unittest.main()
