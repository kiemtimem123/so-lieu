"""Regression tests for the FX-aware cash-flow bridge in validate-bank-reconciliation.py."""
import json
from decimal import Decimal, ROUND_HALF_UP
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
                # Raw source amounts are independently rounded to million VND.
                # Residuals at or below the user-approved 0.01% tolerance are accepted;
                # preserve the source values and never add a balancing plug.
                self.assertTrue(within_relative_tolerance(
                    row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] +
                    row["financing_cash_flow_ytd"], row["net_cash_change_ytd"]))
                self.assertLessEqual(abs(cash_bridge_delta(row)) /
                                     max(abs(row["cash_ending"]), 1) * 100, 0.01)
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
                        self.assertTrue(within_relative_tolerance(row[field], value),
                                        f"{period} {field}: {row[field]} vs {value} exceeds 0.01%")

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



class SSICashFlowNormalizationTests(unittest.TestCase):
    """Source-backed SSI consolidated cash flows using relative tolerance <= 0.01%."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-SSI.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_ssi_all_ten_periods_use_statement_totals_and_relative_tolerance(self):
        periods = (
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        )
        flows = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd",
        )
        cash_fields = (
            "cash_beginning", "cash_ending", "cash_beginning_reported_ytd",
            "cash_ending_reported_ytd",
        )
        visible_fields = flows + cash_fields + (
            "capital_expenditure", "capital_expenditure_ytd",
            "dividends_paid", "dividends_paid_ytd",
        )
        self.assertEqual(set(self.rows), set(periods))
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/SSI/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(row["source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertTrue(row["source_archive_file"].startswith("reports/raw/SSI/"))
                self.assertEqual(row["cashflow_audit_revision"]["selected_source_index_url"],
                                 "https://finance.vietstock.vn/SSI/tai-tai-lieu.htm?doctype=1")
                self.assertEqual(row["cashflow_source_reconciliation"]["tolerance_percent"], 0.01)
                self.assertTrue(row["cashflow_source_reconciliation"]["no_balancing_plug"])
                self.assertEqual(row["cashflow_source_reconciliation"]["source_visual_review"],
                                 "OCR text transcribed; direct PDF image review pending for all pages in this pass")
                self.assertEqual(row.get("foreign_exchange_effect"), None)
                self.assertEqual(row.get("foreign_exchange_effect_ytd"), None)
                self.assertIn("cash_component_detail_adjustment_line_102_vnd",
                              row["cashflow_source_reconciliation"])
                self.assertIn("cash_component_detail_adjustment_line_104_vnd",
                              row["cashflow_source_reconciliation"])
                for field in visible_fields:
                    self.assertIsInstance(row.get(field), (int, float), field)
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, row.get("financial_line_items_extracted_fields", []), field)
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []), field)

                sum_ytd = sum(row[f] for f in (
                    "operating_cash_flow_ytd", "investing_cash_flow_ytd", "financing_cash_flow_ytd"
                ))
                sum_q = sum(row[f] for f in (
                    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow"
                ))
                self.assertTrue(within_relative_tolerance(sum_ytd, row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(sum_q, row["net_cash_change"]))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending_reported_ytd"],
                    row["cash_beginning_reported_ytd"] + row["net_cash_change_ytd"]
                ))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending"],
                    row["cash_beginning"] + row["net_cash_change"]
                ))
                check = row["cashflow_source_reconciliation"]
                self.assertAlmostEqual(check["ytd_flow_sum_relative_difference_percent"],
                                       relative_difference_percent(sum_ytd, row["net_cash_change_ytd"]))
                self.assertAlmostEqual(check["quarter_flow_sum_relative_difference_percent"],
                                       relative_difference_percent(sum_q, row["net_cash_change"]))
                self.assertTrue(check["ytd_flow_components_within_tolerance"])
                self.assertTrue(check["quarter_flow_components_within_tolerance"])
                self.assertTrue(check["ytd_cash_bridge_within_tolerance"])
                self.assertTrue(check["quarter_cash_bridge_within_tolerance"])
                self.assertLessEqual(check["ytd_flow_sum_relative_difference_percent"], 0.01)
                self.assertLessEqual(check["quarter_flow_sum_relative_difference_percent"], 0.01)
                self.assertLessEqual(check["ytd_cash_bridge_relative_difference_percent"], 0.01)
                self.assertLessEqual(check["quarter_cash_bridge_relative_difference_percent"], 0.01)
                self.assertIn(check["status"], (
                    "PASS_ARITHMETIC_RECONCILED",
                    "ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT",
                ))

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for qfield, yfield in (
                        ("operating_cash_flow", "operating_cash_flow_ytd"),
                        ("investing_cash_flow", "investing_cash_flow_ytd"),
                        ("financing_cash_flow", "financing_cash_flow_ytd"),
                        ("net_cash_change", "net_cash_change_ytd"),
                        ("capital_expenditure", "capital_expenditure_ytd"),
                        ("dividends_paid", "dividends_paid_ytd"),
                    ):
                        self.assertEqual(row[qfield], row[yfield])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for qfield, yfield in (
                        ("operating_cash_flow", "operating_cash_flow_ytd"),
                        ("investing_cash_flow", "investing_cash_flow_ytd"),
                        ("financing_cash_flow", "financing_cash_flow_ytd"),
                        ("net_cash_change", "net_cash_change_ytd"),
                        ("capital_expenditure", "capital_expenditure_ytd"),
                        ("dividends_paid", "dividends_paid_ytd"),
                    ):
                        self.assertEqual(row[qfield], row[yfield] - prior[yfield])
                    self.assertEqual(row["cash_beginning"], prior["cash_ending"])

    def test_ssi_later_comparative_cash_flow_totals_match_original_source_basis(self):
        rows = self.rows
        # FY2024 comparative in Q4/2025 is the selected source basis.
        self.assertEqual(rows["2024-Q4"]["operating_cash_flow_ytd"], -4264319)
        self.assertEqual(rows["2024-Q4"]["investing_cash_flow_ytd"], 801533)
        self.assertEqual(rows["2024-Q4"]["financing_cash_flow_ytd"], 3207880)
        self.assertEqual(rows["2024-Q4"]["net_cash_change_ytd"], -254905)
        self.assertIn("Q4_2025", rows["2024-Q4"]["cashflow_audit_revision"]["selected_source_url"])

        # Q1/2025 comparative in Q1/2026.
        self.assertEqual(rows["2025-Q1"]["operating_cash_flow_ytd"], -9373976)
        self.assertEqual(rows["2025-Q1"]["net_cash_change_ytd"], -121959)
        self.assertIn("Q1_2026", rows["2025-Q1"]["cashflow_audit_revision"]["selected_source_url"])

        # H1/2025 comparative in Q2/2026.
        self.assertEqual(rows["2025-Q2"]["operating_cash_flow_ytd"], -12920530)
        self.assertEqual(rows["2025-Q2"]["investing_cash_flow_ytd"], -443459)
        self.assertEqual(rows["2025-Q2"]["financing_cash_flow_ytd"], 15873914)
        self.assertEqual(rows["2025-Q2"]["net_cash_change_ytd"], 2509925)
        self.assertIn("Q2_2026", rows["2025-Q2"]["cashflow_audit_revision"]["selected_source_url"])

    def test_ssi_2026_q2_cash_end_and_source_rounding_stay_within_tolerance(self):
        q2 = self.rows["2026-Q2"]
        self.assertEqual(q2["cash_beginning_reported_ytd"], 3646493)
        self.assertEqual(q2["cash_ending_reported_ytd"], 531522)
        self.assertEqual(q2["net_cash_change_ytd"], -3114971)
        self.assertEqual(q2["cashflow_source_reconciliation"]["ytd_cash_bridge_residual"], 0)
        # Rounding differences in component totals remain metadata; they are not plugged.
        self.assertEqual(q2["cashflow_source_reconciliation"]["quarter_flow_sum_residual"], -1)
        self.assertLessEqual(q2["cashflow_source_reconciliation"]["quarter_flow_sum_relative_difference_percent"], 0.01)



class VDSCashFlowNormalizationTests(unittest.TestCase):
    """Regression for VDS consolidated cash-flow source mapping and 0.01% policy."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-VDS.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_vds_all_ten_periods_reconcile_with_relative_tolerance(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        flow_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd",
        )
        balance_fields = (
            "cash_beginning", "cash_ending", "cash_beginning_reported_ytd",
            "cash_ending_reported_ytd",
        )
        exposed_fields = flow_fields + balance_fields + (
            "capital_expenditure", "capital_expenditure_ytd",
            "dividends_paid", "dividends_paid_ytd",
        )
        self.assertEqual(set(self.rows), expected_periods)

        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(
                    row["source_index_url"],
                    "https://finance.vietstock.vn/VDS/tai-tai-lieu.htm?doctype=1",
                )
                self.assertTrue(row["source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertTrue(row["source_archive_file"].startswith("reports/raw/VDS/"))
                self.assertEqual(row["cashflow_source_reconciliation"]["tolerance_percent"], 0.01)
                self.assertTrue(row["cashflow_source_reconciliation"]["no_balancing_plug"])
                self.assertEqual(row.get("foreign_exchange_effect"), None)
                self.assertEqual(row.get("foreign_exchange_effect_ytd"), None)
                self.assertEqual(
                    row["cashflow_source_reconciliation"]["source_visual_review"],
                    "OCR text transcribed; direct PDF image review pending",
                )
                for field in exposed_fields:
                    self.assertIsInstance(row.get(field), (int, float), field)
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, row.get("financial_line_items_extracted_fields", []), field)
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []), field)

                ytd_sum = sum(row[f] for f in (
                    "operating_cash_flow_ytd", "investing_cash_flow_ytd", "financing_cash_flow_ytd"
                ))
                quarter_sum = sum(row[f] for f in (
                    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow"
                ))
                self.assertTrue(within_relative_tolerance(ytd_sum, row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(quarter_sum, row["net_cash_change"]))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending_reported_ytd"],
                    row["cash_beginning_reported_ytd"] + row["net_cash_change_ytd"]
                ))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending"], row["cash_beginning"] + row["net_cash_change"]
                ))
                check = row["cashflow_source_reconciliation"]
                for field in (
                    "ytd_flow_sum_relative_difference_percent",
                    "quarter_flow_sum_relative_difference_percent",
                    "ytd_cash_bridge_relative_difference_percent",
                    "quarter_cash_bridge_relative_difference_percent",
                ):
                    self.assertLessEqual(check[field], 0.01)
                self.assertTrue(check["ytd_flow_components_within_tolerance"])
                self.assertTrue(check["quarter_flow_components_within_tolerance"])
                self.assertTrue(check["ytd_cash_bridge_within_tolerance"])
                self.assertTrue(check["quarter_cash_bridge_within_tolerance"])
                self.assertIn(check["status"], (
                    "PASS_ARITHMETIC_RECONCILED",
                    "ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT",
                    "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT",
                ))

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for qfield, yfield in (
                        ("operating_cash_flow", "operating_cash_flow_ytd"),
                        ("investing_cash_flow", "investing_cash_flow_ytd"),
                        ("financing_cash_flow", "financing_cash_flow_ytd"),
                        ("net_cash_change", "net_cash_change_ytd"),
                        ("capital_expenditure", "capital_expenditure_ytd"),
                        ("dividends_paid", "dividends_paid_ytd"),
                    ):
                        self.assertEqual(row[qfield], row[yfield])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for qfield, yfield in (
                        ("operating_cash_flow", "operating_cash_flow_ytd"),
                        ("investing_cash_flow", "investing_cash_flow_ytd"),
                        ("financing_cash_flow", "financing_cash_flow_ytd"),
                        ("net_cash_change", "net_cash_change_ytd"),
                        ("capital_expenditure", "capital_expenditure_ytd"),
                        ("dividends_paid", "dividends_paid_ytd"),
                    ):
                        self.assertEqual(row[qfield], row[yfield] - prior[yfield])
                    self.assertEqual(row["cash_beginning"], prior["cash_ending"])

    def test_vds_h1_2024_material_comparative_reclassification_is_flagged(self):
        q2 = self.rows["2024-Q2"]
        selected = q2["cashflow_audit_revision"]["source_basis_history"]
        self.assertEqual(selected["original_cfi_ytd_vnd"], -22707469615)
        self.assertEqual(selected["selected_cfi_ytd_vnd"], -9707469615)
        self.assertEqual(selected["original_cff_ytd_vnd"], 372500000000)
        self.assertEqual(selected["selected_cff_ytd_vnd"], 359500000000)
        self.assertEqual(selected["net_cash_change_unchanged_vnd"], -201926546392)
        self.assertAlmostEqual(selected["source_difference_cfi_relative_percent"], 57.2499, places=4)
        self.assertAlmostEqual(selected["source_difference_cff_relative_percent"], 3.4899, places=4)
        self.assertEqual(q2["cashflow_source_reconciliation"]["status"],
                         "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertTrue(q2["cashflow_source_reconciliation"]["no_balancing_plug"])
        q3 = self.rows["2024-Q3"]
        self.assertEqual(q3["cashflow_source_reconciliation"]["status"],
                         "NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT")
        self.assertEqual(q3["cashflow_audit_revision"]["source_basis_history"]["source_basis_consistency"],
                         "connected_h1_2024_reclassification")

    def test_vds_uses_later_comparative_source_basis_where_checked(self):
        q12024 = self.rows["2024-Q1"]
        self.assertIn("Q1_2025", q12024["cashflow_audit_revision"]["selected_source_url"])
        q42024 = self.rows["2024-Q4"]
        self.assertIn("Q4_2025", q42024["cashflow_audit_revision"]["selected_source_url"])
        q12025 = self.rows["2025-Q1"]
        self.assertIn("Q1_2026", q12025["cashflow_audit_revision"]["selected_source_url"])
        h12025 = self.rows["2025-Q2"]
        self.assertIn("Q2_2026", h12025["cashflow_audit_revision"]["selected_source_url"])

    def test_vds_2026_q2_rounding_residual_is_retained_without_plug(self):
        row = self.rows["2026-Q2"]
        self.assertEqual(row["cashflow_source_reconciliation"]["quarter_flow_sum_residual"], -1)
        self.assertEqual(row["net_cash_change_ytd"], -195358)
        self.assertEqual(row["cash_beginning_reported_ytd"], 996976)
        self.assertEqual(row["cash_ending_reported_ytd"], 801618)
        self.assertLessEqual(
            row["cashflow_source_reconciliation"]["quarter_flow_sum_relative_difference_percent"],
            0.01,
        )



class KDHCashFlowNormalizationTests(unittest.TestCase):
    """Regression for KDH consolidated cash-flow normalization and 0.01% rule."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-KDH.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_kdh_ten_periods_use_source_ytd_and_relative_tolerance(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        flow_fields = (
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "net_cash_change",
            "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd",
        )
        cash_fields = (
            "cash_beginning", "cash_ending",
            "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
        )
        exposed_fields = flow_fields + cash_fields + (
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
        )
        self.assertEqual(set(self.rows), expected_periods)
        self.assertEqual(len(self.rows), 10)

        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                audit = row["cashflow_audit_revision"]
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/KDH/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(audit["selected_source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertEqual(audit["source_reporting_unit"], "Ngàn VND")
                self.assertEqual(rec["tolerance_percent"], 0.01)
                self.assertTrue(rec["no_balancing_plug"])
                for field in exposed_fields:
                    if field.startswith("foreign_exchange"):
                        self.assertIsNone(row[field])
                    else:
                        self.assertIsInstance(row.get(field), (int, float), field)
                        self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, row.get("financial_line_items_extracted_fields", []))
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))

                ytd_sum = sum(row[f] for f in (
                    "operating_cash_flow_ytd", "investing_cash_flow_ytd",
                    "financing_cash_flow_ytd",
                ))
                quarter_sum = sum(row[f] for f in (
                    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
                ))
                self.assertTrue(within_relative_tolerance(ytd_sum, row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(quarter_sum, row["net_cash_change"]))
                self.assertAlmostEqual(
                    rec["ytd_flow_sum_relative_difference_percent"],
                    relative_difference_percent(ytd_sum, row["net_cash_change_ytd"]),
                )
                self.assertAlmostEqual(
                    rec["quarter_flow_sum_relative_difference_percent"],
                    relative_difference_percent(quarter_sum, row["net_cash_change"]),
                )
                self.assertLessEqual(rec["ytd_flow_sum_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_sum_relative_difference_percent"], 0.01)

                ytd_expected_close = (row["cash_beginning_reported_ytd"] +
                                      row["net_cash_change_ytd"])
                quarter_expected_close = row["cash_beginning"] + row["net_cash_change"]
                if rec["ytd_cash_bridge_relative_difference_percent"] <= 0.01:
                    self.assertTrue(within_relative_tolerance(
                        row["cash_ending_reported_ytd"], ytd_expected_close))
                    self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])
                else:
                    self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))
                    self.assertFalse(rec["ytd_cash_bridge_within_tolerance"])
                if rec["quarter_cash_bridge_relative_difference_percent"] <= 0.01:
                    self.assertTrue(within_relative_tolerance(row["cash_ending"], quarter_expected_close))
                    self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])
                else:
                    self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))
                    self.assertFalse(rec["quarter_cash_bridge_within_tolerance"])

                year, quarter = period.split("-Q")
                q = int(quarter)
                if q == 1:
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"] - prior[flow + "_ytd"])

    def test_kdh_later_comparatives_and_material_reclassifications_are_traced(self):
        q2_2024 = self.rows["2024-Q2"]
        self.assertIn("KDH_Baocaotaichinh_Q2_2025", q2_2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            q2_2024["cashflow_audit_revision"]["previous_source_comparison"]["investing"]["relative_difference_percent"],
            0.01,
        )
        self.assertLessEqual(
            q2_2024["cashflow_source_reconciliation"]["ytd_cash_bridge_relative_difference_percent"],
            0.01,
        )
        self.assertTrue(q2_2024["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))

        q4_2024 = self.rows["2024-Q4"]
        self.assertIn("KDH_Baocaotaichinh_Q4_2025", q4_2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            q4_2024["cashflow_audit_revision"]["previous_source_comparison"]["operating"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(q4_2024["cashflow_source_reconciliation"]["no_balancing_plug"])

        q2_2025 = self.rows["2025-Q2"]
        self.assertIn("KDH_Baocaotaichinh_Q2_2026", q2_2025["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            q2_2025["cashflow_audit_revision"]["previous_source_comparison"]["net"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(q2_2025["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))

    def test_kdh_2026_q1_cross_statement_cash_conflict_is_preserved(self):
        row = self.rows["2026-Q1"]
        rec = row["cashflow_source_reconciliation"]
        audit = row["cashflow_audit_revision"]
        self.assertEqual(audit["source_values_raw_thousand_vnd"]["close"], 3643808683)
        self.assertEqual(audit["balance_sheet_cash_ending_raw_thousand_vnd"], 3613808683)
        self.assertEqual(rec["cash_flow_statement_vs_balance_sheet_ending_cash_residual"], 30000)
        self.assertGreater(
            rec["cash_flow_statement_vs_balance_sheet_ending_cash_relative_difference_percent"],
            0.01,
        )
        self.assertEqual(rec["ytd_cash_bridge_residual"], 30000)
        self.assertGreater(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
        self.assertTrue(rec["no_balancing_plug"])

        q2 = self.rows["2026-Q2"]
        q2rec = q2["cashflow_source_reconciliation"]
        self.assertEqual(q2rec["quarter_cash_bridge_residual"], -30001)
        self.assertGreater(q2rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertLessEqual(q2rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
        self.assertTrue(q2rec["no_balancing_plug"])



class NVLCashFlowNormalizationTests(unittest.TestCase):
    """Regression for NVL cash-flow series, source revisions and 0.01% tolerance."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-NVL.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}

    def test_nvl_ten_periods_use_source_ytd_and_correct_vnd_scaling(self):
        expected = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), expected)
        self.assertEqual(len(self.rows), 10)
        core_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
        )
        for period, row in self.rows.items():
            with self.subTest(period=period):
                audit = row["cashflow_audit_revision"]
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/NVL/tai-tai-lieu.htm?doctype=1")
                self.assertEqual(audit["source_reporting_unit"], "VND")
                self.assertEqual(audit["stored_unit"], "triệu VND")
                self.assertIn("source_values_raw_vnd", audit)
                self.assertEqual(rec["tolerance_percent"], 0.01)
                self.assertTrue(rec["no_balancing_plug"])
                for field in core_fields:
                    self.assertIn(field, row.get("financial_line_items_extracted_fields", []))
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))
                    self.assertIsInstance(row.get(field), (int, float), field)
                    self.assertNotIsInstance(row.get(field), bool)

                raw = audit["source_values_raw_vnd"]
                self.assertEqual(raw["cfo"] + raw["cfi"] + raw["cff"], raw["net"])
                self.assertEqual(raw["close"] - raw["open"] - raw["net"] - raw["fx"], 0)
                for stored_key, raw_key in (
                    ("operating_cash_flow_ytd", "cfo"),
                    ("investing_cash_flow_ytd", "cfi"),
                    ("financing_cash_flow_ytd", "cff"),
                    ("net_cash_change_ytd", "net"),
                    ("cash_beginning_reported_ytd", "open"),
                    ("cash_ending_reported_ytd", "close"),
                    ("foreign_exchange_effect_ytd", "fx"),
                ):
                    self.assertLessEqual(abs(row[stored_key] * 1_000_000 - raw[raw_key]), 500_000)

                ytd_sum = sum(row[f] for f in (
                    "operating_cash_flow_ytd", "investing_cash_flow_ytd",
                    "financing_cash_flow_ytd",
                ))
                quarter_sum = sum(row[f] for f in (
                    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
                ))
                self.assertTrue(within_relative_tolerance(ytd_sum, row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(quarter_sum, row["net_cash_change"]))
                self.assertLessEqual(rec["ytd_flow_sum_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_sum_relative_difference_percent"], 0.01)

                ytd_expected = (row["cash_beginning_reported_ytd"] +
                                row["net_cash_change_ytd"] +
                                row["foreign_exchange_effect_ytd"])
                quarter_expected = (row["cash_beginning"] + row["net_cash_change"] +
                                    row["foreign_exchange_effect"])
                if rec["ytd_cash_bridge_relative_difference_percent"] <= 0.01:
                    self.assertTrue(within_relative_tolerance(row["cash_ending_reported_ytd"], ytd_expected))
                    self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])
                else:
                    self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))
                if rec["quarter_cash_bridge_relative_difference_percent"] <= 0.01:
                    self.assertTrue(within_relative_tolerance(row["cash_ending"], quarter_expected))
                    self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])
                else:
                    self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))

                year, qtext = period.split("-Q")
                q = int(qtext)
                if q == 1:
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"], row["foreign_exchange_effect_ytd"])
                else:
                    prior = self.rows[f"{year}-Q{q-1}"]
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"] - prior[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"] -
                                     prior["foreign_exchange_effect_ytd"])

    def test_nvl_later_comparatives_and_source_reclassifications_are_traced(self):
        q2_2024 = self.rows["2024-Q2"]
        self.assertIn("NVL_Baocaotaichinh_Q2_2025", q2_2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            q2_2024["cashflow_audit_revision"]["previous_source_comparison"]["cfo"]["relative_difference_percent"],
            0.01,
        )
        self.assertGreater(
            q2_2024["cashflow_audit_revision"]["previous_source_comparison"]["net"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(q2_2024["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))

        q4_2024 = self.rows["2024-Q4"]
        self.assertIn("NVL_Baocaotaichinh_Q4_2025", q4_2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            q4_2024["cashflow_audit_revision"]["previous_source_comparison"]["cfo"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(q4_2024["cashflow_source_reconciliation"]["no_balancing_plug"])

        q2_2025 = self.rows["2025-Q2"]
        self.assertIn("NVL_Baocaotaichinh_Q2_2026", q2_2025["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            q2_2025["cashflow_audit_revision"]["previous_source_comparison"]["net"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(q2_2025["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))
        self.assertTrue(self.rows["2025-Q3"]["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))

    def test_nvl_later_restated_fy2025_cash_basis_is_preserved(self):
        fy25 = self.rows["2025-Q4"]
        rec = fy25["cashflow_source_reconciliation"]
        self.assertEqual(fy25["cash_ending_reported_ytd"], 4_395_321)
        self.assertEqual(fy25["cashflow_audit_revision"]["later_report_represented_fy2025_cash_close_raw_vnd"],
                         4_208_770_020_478)
        self.assertGreater(rec["later_report_fy2025_cash_basis_relative_difference_percent"], 0.01)
        self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))

    def test_nvl_2026_q1_q2_source_cash_basis_conflict_remains_unplugged(self):
        q1 = self.rows["2026-Q1"]
        q1rec = q1["cashflow_source_reconciliation"]
        self.assertEqual(q1["cash_ending_reported_ytd"], 4_518_329)
        self.assertEqual(q1rec["q4_2025_close_to_q1_2026_opening_residual_raw_vnd"], 2_261_673_373)
        self.assertGreater(q1rec["q4_2025_close_to_q1_2026_opening_relative_difference_percent"], 0.01)

        q2 = self.rows["2026-Q2"]
        q2rec = q2["cashflow_source_reconciliation"]
        self.assertEqual(q2["cash_beginning_reported_ytd"], 4_208_770)
        self.assertEqual(q2rec["q1_to_q2_reported_ytd_opening_residual_raw_vnd"], -188_812_622_733)
        self.assertGreater(q2rec["q1_to_q2_reported_ytd_opening_relative_difference_percent"], 0.01)
        self.assertLessEqual(q2rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
        self.assertGreater(q2rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertEqual(q2rec["quarter_cash_bridge_residual"], -188_812)
        self.assertTrue(q2rec["no_balancing_plug"])



class HHVCashFlowNormalizationTests(unittest.TestCase):
    """Regression for HHV source cash-flow totals, comparative revisions and 0.01% tolerance."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-HHV.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.core_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "net_cash_change", "operating_cash_flow_ytd", "investing_cash_flow_ytd",
            "financing_cash_flow_ytd", "net_cash_change_ytd", "cash_beginning",
            "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd",
        )

    def test_hhv_all_ten_periods_reconcile_and_keep_core_fields_visible(self):
        expected_periods = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1",
            "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), expected_periods)
        self.assertEqual(len(self.rows), 10)

        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                audit = row["cashflow_audit_revision"]
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["source_index_url"],
                                 "https://finance.vietstock.vn/HHV/tai-tai-lieu.htm?doctype=1")
                self.assertEqual(rec["tolerance_percent"], 0.01)
                self.assertTrue(rec["no_balancing_plug"])
                self.assertEqual(audit["source_reporting_unit"], "VND")
                self.assertEqual(audit["stored_unit"], "triệu VND")
                self.assertEqual(audit["scale_rule"],
                                 "Source VND / 1,000,000; snapshot rounded to nearest triệu VND; exact raw source integers retained in this metadata.")
                self.assertEqual(audit["source_visual_review"],
                                 "ocr_sidecar_reconciled_pdf_image_viewer_unavailable")
                raw = audit["source_values_raw_vnd"]
                for key in ("cfo", "cfi", "cff", "net", "open", "fx", "close"):
                    self.assertIsInstance(raw[key], int)
                self.assertEqual(raw["cfo"] + raw["cfi"] + raw["cff"] - raw["net"],
                                 rec["ytd_source_flow_sum_residual_vnd"])
                self.assertEqual(raw["close"] - raw["open"] - raw["net"] - raw["fx"],
                                 rec["ytd_source_cash_bridge_residual_vnd"])
                self.assertTrue(within_relative_tolerance(
                    raw["cfo"] + raw["cfi"] + raw["cff"], raw["net"]))
                self.assertTrue(within_relative_tolerance(
                    raw["close"], raw["open"] + raw["net"] + raw["fx"]))

                for field in self.core_fields:
                    self.assertIsInstance(row.get(field), (int, float), field)
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, row.get("financial_line_items_extracted_fields", []))
                    self.assertNotIn(field, row.get("financial_line_items_rejected_fields", []))

                ytd_sum = row["operating_cash_flow_ytd"] + row["investing_cash_flow_ytd"] + row["financing_cash_flow_ytd"]
                quarter_sum = row["operating_cash_flow"] + row["investing_cash_flow"] + row["financing_cash_flow"]
                self.assertTrue(within_relative_tolerance(ytd_sum, row["net_cash_change_ytd"]))
                self.assertTrue(within_relative_tolerance(quarter_sum, row["net_cash_change"]))
                self.assertTrue(within_relative_tolerance(
                    row["cash_ending_reported_ytd"],
                    row["cash_beginning_reported_ytd"] + row["net_cash_change_ytd"] +
                    row["foreign_exchange_effect_ytd"]))
                self.assertLessEqual(rec["ytd_flow_sum_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["quarter_flow_sum_relative_difference_percent"], 0.01)
                self.assertLessEqual(rec["ytd_cash_bridge_relative_difference_percent"], 0.01)
                self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])
                self.assertTrue(rec["quarter_flow_components_within_tolerance"])

                if rec["quarter_cash_bridge_relative_difference_percent"] <= 0.01:
                    self.assertTrue(within_relative_tolerance(
                        row["cash_ending"],
                        row["cash_beginning"] + row["net_cash_change"] + row["foreign_exchange_effect"]))
                    self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])
                else:
                    self.assertEqual(period, "2026-Q2")
                    self.assertFalse(rec["quarter_cash_bridge_within_tolerance"])
                    self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))

                year, qtext = period.split("-Q")
                q = int(qtext)
                if q == 1:
                    for flow in ("operating_cash_flow", "investing_cash_flow",
                                 "financing_cash_flow", "net_cash_change"):
                        self.assertEqual(row[flow], row[flow + "_ytd"])
                    self.assertEqual(row["foreign_exchange_effect"],
                                     row["foreign_exchange_effect_ytd"])
                    self.assertEqual(row["cash_beginning"], row["cash_beginning_reported_ytd"])
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

    def test_hhv_later_comparatives_and_source_reclassification_are_traced(self):
        h1_2024 = self.rows["2024-Q2"]
        self.assertIn("HHV_Baocaotaichinh_Q2_2025", h1_2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            h1_2024["cashflow_audit_revision"]["previous_source_comparison"]["cfo"]["relative_difference_percent"],
            0.01,
        )
        self.assertGreater(
            h1_2024["cashflow_audit_revision"]["previous_source_comparison"]["cfi"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(h1_2024["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))

        q3_2024 = self.rows["2024-Q3"]
        self.assertEqual(q3_2024["cashflow_audit_revision"]["source_values_raw_vnd"]["net"], 71870752272)
        self.assertIn("later_comparative_comparison", q3_2024["cashflow_audit_revision"])
        self.assertGreater(
            q3_2024["cashflow_audit_revision"]["later_comparative_arithmetic"]["source_flow_sum_relative_difference_percent"],
            0.01,
        )
        self.assertEqual(
            q3_2024["cashflow_audit_revision"]["later_comparative_arithmetic"]["source_flow_sum_residual_vnd"],
            -10_010_000,
        )
        self.assertTrue(q3_2024["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))
        # Keep the original 9M/2024 series because the later OCR comparator's flow sum
        # differs from its stated net by more than the agreed relative tolerance.
        self.assertEqual(q3_2024["investing_cash_flow_ytd"], -507350)

        fy2024 = self.rows["2024-Q4"]
        self.assertIn("HHV_Baocaotaichinh_Q4_2025", fy2024["cashflow_audit_revision"]["selected_source_url"])
        self.assertEqual(fy2024["cashflow_audit_revision"]["previous_source_comparison"]["net"]["previous_source_raw_vnd"], 44238771058)
        self.assertGreater(
            fy2024["cashflow_audit_revision"]["previous_source_comparison"]["net"]["relative_difference_percent"],
            0.01,
        )
        self.assertTrue(fy2024["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))
        self.assertTrue(fy2024["cashflow_source_reconciliation"]["ytd_flow_components_within_tolerance"])

        h1_2025 = self.rows["2025-Q2"]
        self.assertIn("HHV_Baocaotaichinh_Q2_2026", h1_2025["cashflow_audit_revision"]["selected_source_url"])
        self.assertGreater(
            h1_2025["cashflow_audit_revision"]["previous_source_comparison"]["cfo"]["relative_difference_percent"],
            0.01,
        )
        self.assertGreater(
            h1_2025["cashflow_audit_revision"]["previous_source_comparison"]["cfi"]["relative_difference_percent"],
            0.01,
        )
        self.assertLessEqual(
            h1_2025["cashflow_audit_revision"]["previous_source_comparison"]["net"]["relative_difference_percent"],
            0.01,
        )
        self.assertLessEqual(
            h1_2025["cashflow_source_reconciliation"]["ytd_flow_sum_relative_difference_percent"],
            0.01,
        )
        self.assertTrue(h1_2025["cashflow_source_reconciliation"]["status"].startswith("NEEDS_MANUAL_REVIEW"))

    def test_hhv_2026_q2_cross_period_cash_basis_conflict_is_preserved_without_plug(self):
        fy2025 = self.rows["2025-Q4"]
        q1 = self.rows["2026-Q1"]
        h1 = self.rows["2026-Q2"]
        rec = h1["cashflow_source_reconciliation"]
        audit = h1["cashflow_audit_revision"]
        self.assertEqual(audit["source_values_raw_vnd"]["open"], 571723614675)
        self.assertEqual(audit["source_values_raw_vnd"]["close"], 493796286208)
        self.assertEqual(audit["source_values_raw_vnd"]["net"], -77927328467)
        self.assertEqual(rec["cross_period_cash_basis"]["fy2025_close_to_q2_ytd_opening_residual_raw_vnd"],
                         571723614675 - 586763461560)
        self.assertGreater(rec["cross_period_cash_basis"]["fy2025_close_to_q2_ytd_opening_relative_difference_percent"], 0.01)
        self.assertEqual(rec["cross_period_cash_basis"]["q1_to_q2_standalone_bridge_residual_raw_vnd"], -15039808794)
        self.assertGreater(rec["quarter_cash_bridge_relative_difference_percent"], 0.01)
        self.assertTrue(rec["no_balancing_plug"])
        self.assertTrue(rec["status"].startswith("NEEDS_MANUAL_REVIEW"))
        self.assertTrue(within_relative_tolerance(
            q1["cash_beginning_reported_ytd"], fy2025["cash_ending_reported_ytd"]))

class PLXCashFlowNormalizationTests(unittest.TestCase):
    """Regression coverage for PLX cash flow, YTD bridges, field visibility and cross-year exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "data" / "financials-PLX.json").read_text(encoding="utf-8")
        )
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.index_url = "https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1"
        cls.flow_fields = (
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "net_cash_change",
        )
        cls.ytd_fields = tuple(field + "_ytd" for field in cls.flow_fields)
        cls.fx_fields = ("foreign_exchange_effect", "foreign_exchange_effect_ytd")

    @staticmethod
    def _relative_percent(left, right):
        return abs(left - right) / max(abs(left), abs(right), 1) * 100

    @classmethod
    def _within_tolerance(cls, left, right):
        return cls._relative_percent(left, right) <= 0.01

    def test_plx_has_expected_periods_and_approved_vietstock_sources(self):
        expected = {
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2",
        }
        self.assertEqual(set(self.rows), expected)
        self.assertEqual(len(self.rows), 10)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["symbol"], "PLX")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], self.index_url)
                self.assertIn("PLX_Baocaotaichinh_", row["source_url"])
                self.assertTrue(row["source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertTrue(row["source_archive_file"].startswith("reports/raw/PLX/"))
                self.assertEqual(row["cashflow_source_reconciliation"]["source_url"], row["source_url"])
                self.assertEqual(row["cashflow_source_reconciliation"]["relative_tolerance_percent"], 0.01)
                self.assertTrue(row["cashflow_source_reconciliation"]["selected_values_not_adjusted_for_tolerance"])
                self.assertTrue(row["cashflow_source_reconciliation"]["no_balancing_plug"])

    def test_plx_nine_periods_pass_flows_and_cash_bridges_within_001_percent(self):
        complete_periods = sorted(period for period, row in self.rows.items()
                                  if all(isinstance(row.get(field), (int, float)) and not isinstance(row.get(field), bool)
                                         for field in self.flow_fields + self.ytd_fields + self.fx_fields
                                         + ("cash_beginning", "cash_ending")))
        self.assertEqual(len(complete_periods), 9)
        for period in complete_periods:
            with self.subTest(period=period):
                row = self.rows[period]
                year, quarter_text = period.split("-Q")
                quarter = int(quarter_text)
                quarterly_sum = sum(row[field] for field in self.flow_fields[:3])
                ytd_sum = sum(row[field] for field in self.ytd_fields[:3])
                self.assertTrue(self._within_tolerance(quarterly_sum, row["net_cash_change"]))
                self.assertTrue(self._within_tolerance(ytd_sum, row["net_cash_change_ytd"]))
                self.assertTrue(self._within_tolerance(
                    row["cash_beginning"] + row["net_cash_change"] + row["foreign_exchange_effect"],
                    row["cash_ending"],
                ))
                year_open = self.rows[f"{year}-Q1"]["cash_beginning"]
                self.assertTrue(self._within_tolerance(
                    year_open + row["net_cash_change_ytd"] + row["foreign_exchange_effect_ytd"],
                    row["cash_ending"],
                ))
                if quarter == 1:
                    for field in self.flow_fields:
                        self.assertTrue(self._within_tolerance(row[field], row[field + "_ytd"]))
                    self.assertTrue(self._within_tolerance(
                        row["foreign_exchange_effect"], row["foreign_exchange_effect_ytd"]))
                else:
                    prior = self.rows[f"{year}-Q{quarter - 1}"]
                    for field in self.flow_fields:
                        self.assertTrue(self._within_tolerance(
                            row[field], row[field + "_ytd"] - prior[field + "_ytd"]))
                    self.assertTrue(self._within_tolerance(
                        row["foreign_exchange_effect"],
                        row["foreign_exchange_effect_ytd"] - prior["foreign_exchange_effect_ytd"],
                    ))
                    self.assertTrue(self._within_tolerance(row["cash_beginning"], prior["cash_ending"]))

                rec = row["cashflow_source_reconciliation"]
                self.assertTrue(rec["quarter_flow_components_within_tolerance"])
                self.assertTrue(rec["ytd_flow_components_within_tolerance"])
                self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])
                self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])
                self.assertEqual(rec["visual_review"], "ocr_text_reconciled_visual_review_pending")

    def test_plx_source_matched_cashflow_fields_are_allowlisted_and_not_false_rejected(self):
        flow_keys = self.flow_fields + self.ytd_fields + self.fx_fields
        balance_keys = ("cash_beginning", "cash_ending")
        for period, row in self.rows.items():
            with self.subTest(period=period):
                extracted = set(row.get("financial_line_items_extracted_fields", []))
                rejected = set(row.get("financial_line_items_rejected_fields", []))
                if period == "2026-Q2":
                    for field in flow_keys:
                        self.assertIsNone(row.get(field))
                        self.assertNotIn(field, extracted)
                    # Opening comes from Q1 close; closing is supported by the Q2 balance sheet.
                    for field in balance_keys:
                        self.assertIsInstance(row.get(field), (int, float))
                        self.assertIn(field, extracted)
                        self.assertNotIn(field, rejected)
                    continue
                for field in flow_keys + balance_keys:
                    self.assertIsInstance(row.get(field), (int, float))
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, extracted)
                    self.assertNotIn(field, rejected)

    def test_plx_year_boundary_cash_basis_discrepancies_are_preserved_without_plugs(self):
        cases = (
            ("2024-Q4", "2025-Q1", 15062136, 14933069, -129067),
            ("2025-Q4", "2026-Q1", 10803154, 7588240, -3214914),
        )
        for previous_period, current_period, previous_close, current_open, expected_residual in cases:
            with self.subTest(previous_period=previous_period, current_period=current_period):
                previous = self.rows[previous_period]
                current = self.rows[current_period]
                self.assertEqual(previous["cash_ending"], previous_close)
                self.assertEqual(current["cash_beginning"], current_open)
                self.assertEqual(current_open - previous_close, expected_residual)
                self.assertGreater(self._relative_percent(previous_close, current_open), 0.01)
                rec = current["cashflow_source_reconciliation"]["cross_period_cash_basis"]
                self.assertEqual(rec["previous_period"], previous_period)
                self.assertEqual(rec["residual_million_vnd"], expected_residual)
                self.assertGreater(rec["relative_difference_percent"], 0.01)
                self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_CROSS_YEAR_CASH_BASIS")
                self.assertTrue(rec["no_balancing_plug"])

    def test_plx_q2_2026_cashflow_remains_blank_when_archived_ocr_is_unreadable(self):
        row = self.rows["2026-Q2"]
        rec = row["cashflow_source_reconciliation"]
        self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_CASHFLOW_OCR_INCOMPLETE")
        self.assertEqual(rec["visual_review"], "ocr_text_unreadable_visual_review_pending")
        for field in self.flow_fields + self.ytd_fields + self.fx_fields:
            self.assertIsNone(row.get(field))
        self.assertEqual(row["cash_beginning"], 10034406)
        self.assertEqual(row["cash_ending"], 6323957)
        self.assertIn("OCR table on PDF pages 6-7", rec["note"])

class IDCCashFlowNormalizationTests(unittest.TestCase):
    """IDC cash-flow source precedence, quarter/YTD math and cash-basis exception tests."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "data" / "financials-IDC.json").read_text(encoding="utf-8"))
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.expected_periods = {"2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"}
        cls.flow_fields = ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_change")
        cls.ytd_fields = tuple(field + "_ytd" for field in cls.flow_fields)

    @staticmethod
    def _relative_percent(left, right):
        return abs(left - right) / max(abs(left), abs(right), 1) * 100

    @classmethod
    def _within_tolerance(cls, left, right):
        return cls._relative_percent(left, right) <= 0.01

    def test_idc_expected_periods_source_and_units(self):
        self.assertEqual(set(self.rows), self.expected_periods)
        self.assertEqual(len(self.snapshot["items"]), 10)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["symbol"], "IDC")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], "https://finance.vietstock.vn/IDC/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(row["source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertTrue(row["source_archive_file"].startswith("reports/raw/IDC/"))
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(rec["original_period_source_url"], row["source_url"])
                self.assertEqual(rec["relative_tolerance_percent"], 0.01)
                self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])
                self.assertTrue(rec["no_balancing_plug"])
                self.assertIn("static2.vietstock.vn", rec["selected_cashflow_source_url"])
                self.assertTrue(rec["selected_cashflow_source_archive_file"].startswith("reports/raw/IDC/"))

    def test_idc_quarter_and_ytd_components_sum_to_net_change(self):
        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                q_sum = sum(row[k] for k in self.flow_fields[:3])
                ytd_sum = sum(row[k] for k in self.ytd_fields[:3])
                self.assertTrue(self._within_tolerance(q_sum, row["net_cash_change"]))
                self.assertTrue(self._within_tolerance(ytd_sum, row["net_cash_change_ytd"]))
                self.assertTrue(rec["quarter_flow_components_within_tolerance"])
                self.assertTrue(rec["ytd_flow_components_within_tolerance"])
                raw = rec["selected_values_raw_vnd"]
                self.assertEqual(raw["quarter"]["cfo"] + raw["quarter"]["cfi"] + raw["quarter"]["cff"], raw["quarter"]["net_cash_change"])
                self.assertEqual(raw["ytd"]["cfo"] + raw["ytd"]["cfi"] + raw["ytd"]["cff"], raw["ytd"]["net_cash_change"])

    def test_idc_ytd_cash_bridge_and_quarter_cash_bridge(self):
        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                raw = rec["selected_values_raw_vnd"]
                ytd = raw["ytd"]
                ytd_expected = ytd["cash_beginning"] + ytd["net_cash_change"] + ytd["fx"]
                ytd_residual = ytd["cash_ending"] - ytd_expected
                self.assertEqual(ytd_residual, rec["calculations"]["ytd_cash_bridge_residual_raw_vnd"])
                self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])
                q = raw["quarter"]
                q_expected = q["cash_beginning"] + q["net_cash_change"] + q["fx"]
                q_residual = q["cash_ending"] - q_expected
                self.assertEqual(q_residual, rec["calculations"]["quarter_cash_bridge_residual_raw_vnd"])
                if period == "2026-Q2":
                    self.assertGreater(self._relative_percent(q["cash_ending"], q_expected), 0.01)
                    self.assertFalse(rec["quarter_cash_bridge_within_tolerance"])
                    self.assertEqual(rec["status"], "NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_AND_VISUAL_PENDING")
                else:
                    self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])

    def test_idc_quarter_flows_equal_ytd_deltas_and_intra_year_cash_continuity(self):
        for period, row in self.rows.items():
            year, quarter_text = period.split("-Q")
            quarter = int(quarter_text)
            prior = self.rows.get(f"{year}-Q{quarter-1}") if quarter > 1 else None
            with self.subTest(period=period):
                raw = row["cashflow_source_reconciliation"]["selected_values_raw_vnd"]
                qraw, yraw = raw["quarter"], raw["ytd"]
                if prior:
                    praw = prior["cashflow_source_reconciliation"]["selected_values_raw_vnd"]["ytd"]
                    for field in ("cfo", "cfi", "cff", "net_cash_change", "fx"):
                        self.assertEqual(qraw[field], yraw[field] - praw[field])
                    self.assertEqual(qraw["cash_beginning"], praw["cash_ending"])
                    self.assertEqual(row["cash_beginning"], prior["cash_ending"])
                else:
                    for field in ("cfo", "cfi", "cff", "net_cash_change", "fx"):
                        self.assertEqual(qraw[field], yraw[field])

    def test_idc_ytd_opening_is_separate_and_2026_q2_exception_preserved(self):
        row = self.rows["2026-Q2"]
        rec = row["cashflow_source_reconciliation"]
        cross = rec["cross_period_cash_basis"]
        self.assertEqual(row["cash_beginning"], 800729)
        self.assertEqual(row["cash_beginning_reported_ytd"], 553943)
        self.assertEqual(row["cash_ending"], 608685)
        # Balance-sheet cash at 30/06/2026 is a separate source row from the
        # unresolved cash-flow closing balance; preserve both without forcing
        # them to match while the source bridge remains under manual review.
        self.assertEqual(row["cash_and_equivalents"], 553943)
        self.assertEqual(cross["prior_year_end_cash_raw_vnd"], 553052678239)
        self.assertEqual(cross["source_reported_ytd_open_raw_vnd"], 553943475131)
        self.assertEqual(cross["residual_raw_vnd"], 890796892)
        self.assertGreater(cross["relative_difference_percent"], 0.01)
        self.assertTrue(cross["no_balancing_plug"])

    def test_idc_h1_source_revision_history_is_preserved(self):
        h124 = self.rows["2024-Q2"]["cashflow_source_reconciliation"]["source_revision"]
        self.assertEqual(h124["prior_source"], "2024-Q2 original report")
        self.assertEqual(h124["selected_minus_prior_ytd_values_raw_vnd"]["cfo"], 27887768541)
        self.assertEqual(h124["selected_minus_prior_ytd_values_raw_vnd"]["cfi"], -27887762007)
        h125 = self.rows["2025-Q2"]["cashflow_source_reconciliation"]["source_revision"]
        self.assertEqual(h125["selected_minus_prior_ytd_values_raw_vnd"]["cfo"], -525837250014)
        self.assertEqual(h125["selected_minus_prior_ytd_values_raw_vnd"]["cfi"], 525837250014)
        self.assertEqual(h125["selected_minus_prior_ytd_values_raw_vnd"]["net"], 0)
        self.assertEqual(h125["selected_minus_prior_ytd_values_raw_vnd"]["cff"], 0)
        self.assertIn("As restated", self.rows["2025-Q2"]["cashflow_source_reconciliation"]["selected_cashflow_source_basis"])

    def test_idc_cashflow_fields_are_allowlisted_and_not_false_rejected(self):
        fields = self.flow_fields + self.ytd_fields + ("foreign_exchange_effect", "foreign_exchange_effect_ytd", "cash_beginning", "cash_ending", "cash_beginning_reported_ytd", "cash_ending_reported_ytd")
        for period, row in self.rows.items():
            with self.subTest(period=period):
                extracted = set(row.get("financial_line_items_extracted_fields", []))
                rejected = set(row.get("financial_line_items_rejected_fields", []))
                for field in fields:
                    self.assertIsInstance(row.get(field), (int, float))
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, extracted)
                    self.assertNotIn(field, rejected)

class KBCCashFlowNormalizationTests(unittest.TestCase):
    """KBC cash-flow source precedence, quarter/YTD reconciliation and exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "data" / "financials-KBC.json").read_text(encoding="utf-8"))
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.expected_periods = {"2024-Q1","2024-Q2","2024-Q3","2024-Q4","2025-Q1","2025-Q2","2025-Q3","2025-Q4","2026-Q1","2026-Q2","2026-Q3"}
        cls.flows = ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_change")
        cls.ytd = tuple(field + "_ytd" for field in cls.flows)

    @staticmethod
    def _relative_percent(left, right):
        return abs(left - right) / max(abs(left), abs(right), 1) * 100

    @classmethod
    def _within_tolerance(cls, left, right):
        return cls._relative_percent(left, right) <= 0.01

    def test_kbc_period_schema_sources_and_units(self):
        self.assertEqual(set(self.rows), self.expected_periods)
        self.assertEqual(len(self.snapshot["items"]), 11)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["symbol"], "KBC")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], "https://finance.vietstock.vn/KBC/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(row["source_url"].startswith("https://static2.vietstock.vn/"))
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(rec["relative_tolerance_percent"], 0.01)
                self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])
                self.assertTrue(rec["no_balancing_plug"])
                self.assertFalse(rec["separate_fx_line_reported"])
                self.assertTrue(rec["selected_cashflow_source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertTrue(rec["selected_cashflow_source_archive_file"].startswith("reports/raw/KBC/"))

    def test_kbc_all_periods_raw_flow_sums_and_bridges(self):
        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                raw = rec["selected_values_raw_vnd"]
                q, ytd = raw["quarter"], raw["ytd"]
                self.assertEqual(q["cfo"] + q["cfi"] + q["cff"], q["net_cash_change"])
                self.assertEqual(ytd["cfo"] + ytd["cfi"] + ytd["cff"], ytd["net_cash_change"])
                q_residual = q["cash_ending"] - q["cash_beginning"] - q["net_cash_change"]
                y_residual = ytd["cash_ending"] - ytd["cash_beginning"] - ytd["net_cash_change"]
                self.assertEqual(q_residual, rec["calculations"]["quarter_cash_bridge_residual_raw_vnd"])
                self.assertEqual(y_residual, rec["calculations"]["ytd_cash_bridge_residual_raw_vnd"])
                self.assertTrue(self._within_tolerance(q["cash_ending"], q["cash_beginning"] + q["net_cash_change"]))
                self.assertTrue(self._within_tolerance(ytd["cash_ending"], ytd["cash_beginning"] + ytd["net_cash_change"]))
                self.assertTrue(rec["quarter_flow_components_within_tolerance"])
                self.assertTrue(rec["ytd_flow_components_within_tolerance"])
                self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])
                self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])

    def test_kbc_quarter_values_equal_ytd_differences_before_rounding(self):
        for period, row in self.rows.items():
            year, qtxt = period.split("-Q")
            quarter = int(qtxt)
            previous = self.rows.get(f"{year}-Q{quarter - 1}") if quarter > 1 else None
            raw = row["cashflow_source_reconciliation"]["selected_values_raw_vnd"]
            with self.subTest(period=period):
                if previous:
                    prev_ytd = previous["cashflow_source_reconciliation"]["selected_values_raw_vnd"]["ytd"]
                    for key in ("cfo","cfi","cff","net_cash_change"):
                        self.assertEqual(raw["quarter"][key], raw["ytd"][key] - prev_ytd[key])
                    self.assertEqual(raw["quarter"]["cash_beginning"], prev_ytd["cash_ending"])
                else:
                    for key in ("cfo","cfi","cff","net_cash_change"):
                        self.assertEqual(raw["quarter"][key], raw["ytd"][key])

    def test_kbc_fx_is_null_because_source_has_no_separate_fx_line(self):
        for row in self.rows.values():
            with self.subTest(period=row["period"]):
                self.assertIsNone(row.get("foreign_exchange_effect"))
                self.assertIsNone(row.get("foreign_exchange_effect_ytd"))
                self.assertFalse(row["cashflow_source_reconciliation"]["separate_fx_line_reported"])

    def test_kbc_cross_year_cash_basis_difference_is_preserved(self):
        rec = self.rows["2026-Q1"]["cashflow_source_reconciliation"]["cross_year_cash_basis"]
        self.assertEqual(rec["prior_year_end_cash_raw_vnd"], 8386548063120)
        self.assertEqual(rec["current_year_open_cash_raw_vnd"], 8368534552023)
        self.assertEqual(rec["residual_raw_vnd"], -18013511097)
        self.assertGreater(rec["relative_difference_percent"], 0.01)
        self.assertTrue(rec["no_balancing_plug"])

    def test_kbc_q3_2026_investing_total_uses_detail_sum_not_bad_ocr_candidate(self):
        rec = self.rows["2026-Q3"]["cashflow_source_reconciliation"]
        self.assertEqual(rec["investing_total_ocr_candidate_raw_vnd"], -518402271256)
        self.assertEqual(rec["investing_component_sum_raw_vnd"], -515402271256)
        self.assertEqual(rec["investing_component_sum_vs_ocr_residual_raw_vnd"], 3000000000)
        self.assertEqual(sum(rec["investing_component_lines_raw_vnd"].values()), -515402271256)
        self.assertEqual(self.rows["2026-Q3"]["investing_cash_flow_ytd"], -515402.271)

    def test_kbc_h1_2025_comparative_revision_is_preserved(self):
        rec = self.rows["2025-Q2"]["cashflow_source_reconciliation"]["source_revision"]
        self.assertEqual(rec["prior_source_values_raw_vnd"]["cfo"], -7173820953702)
        self.assertEqual(rec["prior_source_values_raw_vnd"]["cfi"], -1366913300321)
        self.assertEqual(rec["selected_minus_prior_source_values_raw_vnd"]["cfo"], -895822506913)
        self.assertEqual(rec["selected_minus_prior_source_values_raw_vnd"]["cfi"], 895672506913)
        self.assertEqual(rec["selected_minus_prior_source_values_raw_vnd"]["net"], -150000000)

    def test_kbc_source_cash_crosscheck_q3_2025_is_within_tolerance(self):
        rec = self.rows["2025-Q3"]["cashflow_source_reconciliation"]["balance_sheet_cash_crosscheck"]
        self.assertEqual(rec["balance_sheet_cash_million_vnd"], 9418878)
        self.assertEqual(rec["cashflow_statement_close_raw_vnd"], 9418578135962)
        self.assertLessEqual(rec["relative_difference_percent"], 0.01)

    def test_kbc_validated_cashflow_fields_not_false_rejected(self):
        fields = self.flows + self.ytd + ("cash_beginning","cash_ending","cash_beginning_reported_ytd","cash_ending_reported_ytd")
        for period, row in self.rows.items():
            with self.subTest(period=period):
                extracted = set(row.get("financial_line_items_extracted_fields", []))
                rejected = set(row.get("financial_line_items_rejected_fields", []))
                for field in fields:
                    self.assertIsInstance(row.get(field), (int,float))
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, extracted)
                    self.assertNotIn(field, rejected)

class GEGCashFlowNormalizationTests(unittest.TestCase):
    """GEG cash-flow source precedence, quarterly/YTD calculations and known source-basis exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "data" / "financials-GEG.json").read_text(encoding="utf-8"))
        cls.rows = {row["period"]: row for row in cls.snapshot["items"]}
        cls.expected = {"2024-Q1","2024-Q2","2024-Q3","2024-Q4","2025-Q1","2025-Q2","2025-Q3","2025-Q4","2026-Q1","2026-Q2"}
        cls.flows = ("operating_cash_flow","investing_cash_flow","financing_cash_flow","net_cash_change")
        cls.ytd = tuple(k + "_ytd" for k in cls.flows)
        cls.fx = ("foreign_exchange_effect","foreign_exchange_effect_ytd")

    @staticmethod
    def pct(a, b):
        return abs(a - b) / max(abs(a), abs(b), 1) * 100

    @classmethod
    def within(cls, a, b):
        return cls.pct(a, b) <= 0.01

    def test_geg_sources_periods_and_units(self):
        self.assertEqual(set(self.rows), self.expected)
        self.assertEqual(len(self.snapshot["items"]), 10)
        for period, row in self.rows.items():
            with self.subTest(period=period):
                self.assertEqual(row["symbol"], "GEG")
                self.assertEqual(row["unit"], "triệu VND")
                self.assertEqual(row["source_index_url"], "https://finance.vietstock.vn/GEG/tai-tai-lieu.htm?doctype=1")
                self.assertTrue(row["source_url"].startswith("https://static2.vietstock.vn/"))
                rec = row["cashflow_source_reconciliation"]
                self.assertEqual(rec["relative_tolerance_percent"], 0.01)
                self.assertTrue(rec["selected_values_not_adjusted_for_tolerance"])
                self.assertTrue(rec["no_balancing_plug"])
                self.assertTrue(rec["separate_fx_line_reported"])
                self.assertTrue(rec["selected_cashflow_source_url"].startswith("https://static2.vietstock.vn/"))
                self.assertTrue(rec["selected_cashflow_source_archive_file"].startswith("reports/raw/GEG/"))

    def test_geg_raw_quarter_and_ytd_flow_sums_are_exact(self):
        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                q, y = rec["selected_values_raw_vnd"]["quarter"], rec["selected_values_raw_vnd"]["ytd"]
                self.assertEqual(q["cfo"] + q["cfi"] + q["cff"], q["net_cash_change"])
                self.assertEqual(y["cfo"] + y["cfi"] + y["cff"], y["net_cash_change"])
                self.assertTrue(rec["quarter_flow_components_within_tolerance"])
                self.assertTrue(rec["ytd_flow_components_within_tolerance"])

    def test_geg_ytd_cash_bridges_and_quarter_exceptions(self):
        expected_exceptions = {"2026-Q2"}
        for period, row in self.rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                q, y = rec["selected_values_raw_vnd"]["quarter"], rec["selected_values_raw_vnd"]["ytd"]
                q_expected = q["cash_beginning"] + q["net_cash_change"] + q["fx"]
                y_expected = y["cash_beginning"] + y["net_cash_change"] + y["fx"]
                self.assertTrue(self.within(y["cash_ending"], y_expected))
                self.assertTrue(rec["ytd_cash_bridge_within_tolerance"])
                if period in expected_exceptions:
                    self.assertGreater(self.pct(q["cash_ending"], q_expected), 0.01)
                    self.assertFalse(rec["quarter_cash_bridge_within_tolerance"])
                else:
                    self.assertTrue(self.within(q["cash_ending"], q_expected))
                    self.assertTrue(rec["quarter_cash_bridge_within_tolerance"])

    def test_geg_standalone_quarter_equals_ytd_difference_before_rounding(self):
        for period, row in self.rows.items():
            year, qtxt = period.split("-Q")
            qnum = int(qtxt)
            prev = self.rows.get(f"{year}-Q{qnum-1}") if qnum > 1 else None
            raw = row["cashflow_source_reconciliation"]["selected_values_raw_vnd"]
            with self.subTest(period=period):
                if prev:
                    prev_ytd = prev["cashflow_source_reconciliation"]["selected_values_raw_vnd"]["ytd"]
                    for key in ("cfo","cfi","cff","net_cash_change","fx"):
                        self.assertEqual(raw["quarter"][key], raw["ytd"][key] - prev_ytd[key])
                    self.assertEqual(raw["quarter"]["cash_beginning"], prev_ytd["cash_ending"])
                else:
                    for key in ("cfo","cfi","cff","net_cash_change","fx"):
                        self.assertEqual(raw["quarter"][key], raw["ytd"][key])

    def test_geg_original_h1_2025_source_and_later_comparative_are_traceable(self):
        q2 = self.rows["2025-Q2"]["cashflow_source_reconciliation"]
        self.assertEqual(q2["selected_cashflow_source_period"], "H1/2025 original consolidated BCTC Q2/2025")
        self.assertTrue(q2["selected_cashflow_source_url"].endswith("GEG_Baocaotaichinh_Q2_2025_Hopnhat.pdf"))
        ytd = q2["selected_values_raw_vnd"]["ytd"]
        self.assertEqual(ytd["cfo"], 555421075993)
        self.assertEqual(ytd["cfi"], 476067298075)
        self.assertEqual(ytd["cff"], -721712954268)
        self.assertEqual(ytd["net_cash_change"], 309775419800)
        self.assertEqual(ytd["fx"], 56223158)
        self.assertEqual(ytd["cash_beginning"], 163717707072)
        self.assertEqual(ytd["cash_ending"], 473549350030)
        alternative = q2["source_revision"]["later_comparative_alternative"]
        self.assertEqual(alternative["source_period"], "H1/2025 later comparative in Q2/2026")
        self.assertEqual(alternative["raw_values_vnd"]["net_cash_change"], 310111805190)
        self.assertEqual(alternative["differences_vs_selected_original_raw_vnd"]["net_cash_change"], 336385390)
        self.assertEqual(q2["calculations"]["quarter_cash_bridge_residual_raw_vnd"], 0)
        self.assertEqual(self.rows["2025-Q3"]["cashflow_source_reconciliation"]["calculations"]["quarter_cash_bridge_residual_raw_vnd"], 0)
        self.assertEqual(self.rows["2026-Q2"]["cashflow_source_reconciliation"]["calculations"]["quarter_cash_bridge_residual_raw_vnd"], -11422219803)
        self.assertEqual(self.rows["2026-Q2"]["cashflow_source_reconciliation"]["cross_period_cash_basis"]["residual_raw_vnd"], -30914348704)

    def test_geg_q2_q3_2025_source_pages_visually_verified_and_quarter_bridges_pass(self):
        q2 = self.rows["2025-Q2"]
        q2_rec = q2["cashflow_source_reconciliation"]
        self.assertEqual(q2_rec["visual_review"], "direct_image_verified_printed_pages_4_5")
        self.assertEqual(q2_rec["status"], "PASS_WITHIN_TOLERANCE_SOURCE_ROWS_VISUALLY_VERIFIED")
        self.assertTrue(q2_rec["quarter_cash_bridge_within_tolerance"])
        self.assertTrue(q2_rec["ytd_cash_bridge_within_tolerance"])
        self.assertEqual(q2_rec["selected_values_raw_vnd"]["quarter"]["cash_beginning"], 175400032558)
        self.assertEqual(q2_rec["selected_values_raw_vnd"]["quarter"]["cash_ending"], 473549350030)

        q3 = self.rows["2025-Q3"]
        q3_rec = q3["cashflow_source_reconciliation"]
        self.assertEqual(q3_rec["visual_review"], "direct_image_verified_printed_pages_4_5")
        self.assertEqual(q3_rec["status"], "PASS_WITHIN_TOLERANCE_SOURCE_ROWS_VISUALLY_VERIFIED")
        self.assertTrue(q3_rec["quarter_cash_bridge_within_tolerance"])
        self.assertTrue(q3_rec["ytd_cash_bridge_within_tolerance"])
        self.assertEqual(q3_rec["selected_values_raw_vnd"]["quarter"]["cash_beginning"], 473549350030)
        self.assertEqual(q3_rec["selected_values_raw_vnd"]["quarter"]["cash_ending"], 406053297053)

    def test_geg_q1_2025_comparative_and_q1_2026_source_pages_visually_verified(self):
        for period in ("2025-Q1", "2026-Q1"):
            with self.subTest(period=period):
                rec = self.rows[period]["cashflow_source_reconciliation"]
                self.assertEqual(rec["visual_review"], "direct_image_verified_printed_pages_4_5")
                self.assertEqual(rec["visual_review_completed_at"], "2026-10-30")
                self.assertEqual(rec["status"], "PASS_WITHIN_TOLERANCE_SOURCE_ROWS_VISUALLY_VERIFIED")

    def test_geg_numeric_cashflow_fields_are_allowlisted(self):
        fields = self.flows + self.ytd + self.fx + ("cash_beginning","cash_ending","cash_beginning_reported_ytd","cash_ending_reported_ytd")
        for period, row in self.rows.items():
            with self.subTest(period=period):
                ex, rejected = set(row.get("financial_line_items_extracted_fields") or []), set(row.get("financial_line_items_rejected_fields") or [])
                for field in fields:
                    self.assertIsInstance(row.get(field), (int,float))
                    self.assertNotIsInstance(row.get(field), bool)
                    self.assertIn(field, ex)
                    self.assertNotIn(field, rejected)

    def test_geg_q4_2025_cashflow_rows_visually_verified(self):
        row = self.rows["2025-Q4"]
        rec = row["cashflow_source_reconciliation"]
        ytd = rec["selected_values_raw_vnd"]["ytd"]
        self.assertEqual(rec["visual_review"], "direct_image_verified_printed_pages_4_5")
        self.assertEqual(rec["visual_review_completed_at"], "2026-10-30")
        self.assertEqual(ytd["cfo"], 932884327033)
        self.assertEqual(ytd["cfi"], 1921143888)
        self.assertEqual(ytd["cff"], -1012240268026)
        self.assertEqual(ytd["net_cash_change"], -77434797105)
        self.assertEqual(ytd["cash_beginning"], 163717707072)
        self.assertEqual(ytd["fx"], 81753281)
        self.assertEqual(ytd["cash_ending"], 86364663248)
        self.assertEqual(rec["status"], "PASS_WITHIN_TOLERANCE_SOURCE_ROWS_VISUALLY_VERIFIED")

class GEGSourceAuditEnrichmentPreservationTests(unittest.TestCase):
    """Generic enrichment must not hide source-audited GEG cash-flow fields."""

    @classmethod
    def setUpClass(cls):
        cls.enricher = runpy.run_path(
            str(ROOT / "scripts" / "enrich-financial-categories.py"),
            run_name="cashflow_enricher_for_test",
        )
        cls.restore = staticmethod(cls.enricher["restore_source_audited_cashflow_fields"])

    def test_geg_audited_cashflow_fields_survive_generic_enrichment(self):
        snapshot = json.loads((ROOT / "data" / "financials-GEG.json").read_text(encoding="utf-8"))
        cash_fields = (
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_change",
            "operating_cash_flow_ytd", "investing_cash_flow_ytd", "financing_cash_flow_ytd", "net_cash_change_ytd",
            "foreign_exchange_effect", "foreign_exchange_effect_ytd", "cash_beginning", "cash_ending",
            "cash_beginning_reported_ytd", "cash_ending_reported_ytd", "cashflow_period_basis",
        )
        original_raw = {
            row["period"]: json.loads(json.dumps(row["cashflow_source_reconciliation"]["selected_values_raw_vnd"]))
            for row in snapshot["items"]
        }
        for row in snapshot["items"]:
            row["cashflow_period_basis"] = "year_to_date"
            for field in cash_fields:
                if field != "cashflow_period_basis":
                    row[field] = None
            row["financial_line_items_extracted_fields"] = []
            row["financial_line_items_rejected_fields"] = list(cash_fields)
            row["financial_line_items_status"] = "auto_extracted_pending_visual_review"

        changed, quarters, field_count = self.restore(snapshot["items"], "GEG")
        self.assertTrue(changed)
        self.assertEqual(quarters, 10)
        self.assertGreater(field_count, 0)

        rows = {row["period"]: row for row in snapshot["items"]}
        self.assertEqual(set(rows), set(original_raw))

        def million(raw_vnd):
            return int((Decimal(str(raw_vnd)) / Decimal("1000000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        for period, row in rows.items():
            with self.subTest(period=period):
                rec = row["cashflow_source_reconciliation"]
                raw = original_raw[period]
                quarter, ytd = raw["quarter"], raw["ytd"]
                self.assertEqual(rec["selected_values_raw_vnd"], raw)
                self.assertEqual(row["cashflow_period_basis"], rec["display_period_basis"])
                self.assertEqual(row["operating_cash_flow"], million(quarter["cfo"]))
                self.assertEqual(row["investing_cash_flow"], million(quarter["cfi"]))
                self.assertEqual(row["financing_cash_flow"], million(quarter["cff"]))
                self.assertEqual(row["net_cash_change"], million(quarter["net_cash_change"]))
                self.assertEqual(row["foreign_exchange_effect"], million(quarter["fx"]))
                self.assertEqual(row["cash_beginning"], million(quarter["cash_beginning"]))
                self.assertEqual(row["cash_ending"], million(quarter["cash_ending"]))
                self.assertEqual(row["operating_cash_flow_ytd"], million(ytd["cfo"]))
                self.assertEqual(row["investing_cash_flow_ytd"], million(ytd["cfi"]))
                self.assertEqual(row["financing_cash_flow_ytd"], million(ytd["cff"]))
                self.assertEqual(row["net_cash_change_ytd"], million(ytd["net_cash_change"]))
                self.assertEqual(row["foreign_exchange_effect_ytd"], million(ytd["fx"]))
                self.assertEqual(row["cash_beginning_reported_ytd"], million(ytd["cash_beginning"]))
                self.assertEqual(row["cash_ending_reported_ytd"], million(ytd["cash_ending"]))
                extracted = set(row["financial_line_items_extracted_fields"])
                rejected = set(row["financial_line_items_rejected_fields"])
                for field in cash_fields:
                    self.assertIn(field, extracted)
                    self.assertNotIn(field, rejected)

        # Only the source-basis difference in Q2/2026 remains above tolerance.
        rec = rows["2026-Q2"]["cashflow_source_reconciliation"]
        self.assertFalse(rec["quarter_cash_bridge_within_tolerance"])
        self.assertEqual(rec["calculations"]["quarter_cash_bridge_residual_raw_vnd"], -11422219803)
        self.assertTrue(rec["no_balancing_plug"])
        for period in ("2025-Q2", "2025-Q3"):
            source_rec = rows[period]["cashflow_source_reconciliation"]
            self.assertTrue(source_rec["quarter_cash_bridge_within_tolerance"])
            self.assertEqual(source_rec["calculations"]["quarter_cash_bridge_residual_raw_vnd"], 0)

        self.assertEqual(rows["2025-Q4"]["financial_line_items_status"], "cashflow_source_rows_visually_verified")

class ManualCoreValueEnrichmentPreservationTests(unittest.TestCase):
    """Generic parser enrichment must not delete manually verified core values."""

    @classmethod
    def setUpClass(cls):
        cls.enricher = runpy.run_path(
            str(ROOT / "scripts" / "enrich-financial-categories.py"),
            run_name="manual_core_enricher_for_test",
        )
        cls.capture = staticmethod(cls.enricher["capture_manually_verified_core_fields"])
        cls.restore = staticmethod(cls.enricher["restore_manually_verified_core_fields"])

    def test_fpt_q4_2024_manually_verified_core_values_survive_parser_migration(self):
        snapshot = json.loads((ROOT / "data" / "financials-FPT.json").read_text(encoding="utf-8"))
        row = next(item for item in snapshot["items"] if item["period"] == "2024-Q4")
        fields = ("total_assets", "total_liabilities", "equity", "pretax_profit", "net_profit")
        expected = {field: row[field] for field in fields}
        backups = self.capture([row])
        self.assertIn("2024-Q4", backups)
        for field in fields:
            row[field] = None
        row["verification_status"] = "auto_pending_extraction"
        row["core_financial_extracted_fields"] = []
        row["core_financial_extraction_status"] = "auto_pending_extraction"
        changed, quarters, field_count = self.restore([row], "FPT", backups)
        self.assertTrue(changed)
        self.assertEqual(quarters, 1)
        self.assertEqual(field_count, 5)
        self.assertEqual({field: row[field] for field in fields}, expected)
        self.assertEqual(row["verification_status"], "verified_manual_visual_reconciliation")
        self.assertTrue(set(fields).issubset(set(row["core_financial_extracted_fields"])))
        self.assertTrue(set(fields).issubset(set(row["core_financial_extraction_manually_verified_fields"])))

    def test_fpt_q4_2024_visually_verified_income_statement_values(self):
        snapshot = json.loads((ROOT / "data" / "financials-FPT.json").read_text(encoding="utf-8"))
        row = next(item for item in snapshot["items"] if item["period"] == "2024-Q4")
        self.assertTrue(row["source_extract_review"]["manually_visual_reviewed"])
        self.assertEqual(row["source_extract_review"]["source_pages"], [8])
        self.assertEqual(row["source_extract_review"]["printed_pages"], [6])
        for field, expected in {
            "revenue":17607818,"cost_of_goods_sold":11128844,"gross_profit":6478973,
            "financial_income":576398,"financial_expense":831375,"interest_expense":134854,
            "selling_expense":1684354,"admin_expense":1735410,"operating_profit":2922047,
            "pretax_profit":2959667,"income_tax_current":536404,"income_tax_deferred":-70239,
            "income_tax":466165,"net_profit":2493502,"net_profit_attributable":2086993,
            "eps":994,"diluted_eps":994,"roa":14.29,"roe":28.03
        }.items():
            with self.subTest(field=field):
                self.assertEqual(row[field], expected)
        self.assertEqual(row["pretax_profit"]-row["net_profit"],row["income_tax"])


ENRICHER = runpy.run_path(
    str(ROOT / "scripts" / "enrich-financial-categories.py"),
    run_name="cashflow_enrichment_module",
)
capture_source_audited_cashflow_backups = ENRICHER["capture_source_audited_cashflow_backups"]
restore_source_audited_cashflow_backups = ENRICHER["restore_source_audited_cashflow_backups"]


class EnrichmentCashflowPreservationTests(unittest.TestCase):
    def test_source_audited_ytd_cashflow_survives_detail_enrichment(self):
        symbol = "VND"
        source_index = "https://finance.vietstock.vn/VND/tai-tai-lieu.htm?doctype=1"
        row = {
            "period": "2025-Q1",
            "unit": "triệu VND",
            "source_index_url": source_index,
            "source_archive_file": "reports/raw/VND/test-source.pdf",
            "cashflow_period_basis": "year_to_date",
            "operating_cash_flow": -5202620,
            "operating_cash_flow_ytd": -5202620,
            "investing_cash_flow": -3575,
            "investing_cash_flow_ytd": -3575,
            "financing_cash_flow": 5302391,
            "financing_cash_flow_ytd": 5302391,
            "net_cash_change": 96197,
            "net_cash_change_ytd": 96197,
            "cash_beginning": 881176,
            "cash_beginning_reported_ytd": 881176,
            "cash_ending": 977372,
            "cash_ending_reported_ytd": 977372,
            "foreign_exchange_effect": None,
            "foreign_exchange_effect_ytd": None,
            "financial_line_items_extracted_fields": [
                "operating_cash_flow", "operating_cash_flow_ytd",
                "investing_cash_flow", "investing_cash_flow_ytd",
                "financing_cash_flow", "financing_cash_flow_ytd",
                "net_cash_change", "net_cash_change_ytd",
                "cash_beginning", "cash_ending",
            ],
            "financial_line_items_rejected_fields": [],
            "cashflow_source_reconciliation": {
                "source_index_url": source_index,
                "comparison_tolerance_relative_percent": 0.01,
                "ytd_flow_components_sum_to_net_cash_change": True,
                "quarter_flow_components_sum_to_net_cash_change": True,
                "ytd_cash_bridge_residual": 0,
                "quarter_cash_bridge_residual": 0,
                "status": "PASS_ARITHMETIC_RECONCILED",
            },
            "cashflow_audit_revision": {"selected_basis": "validated YTD source"},
        }
        rows = [row]
        backups = capture_source_audited_cashflow_backups(rows, symbol)

        # Simulate the regression caused by generic OCR/enrichment.
        row["cashflow_period_basis"] = "quarterly_reported"
        row["operating_cash_flow_ytd"] = 123456
        row["financing_cash_flow"] = None
        row["cash_ending"] = None
        row["financial_line_items_extracted_fields"] = ["brokerage_revenue"]
        row["financial_line_items_rejected_fields"] = ["operating_cash_flow_ytd"]
        row["cashflow_source_reconciliation"] = {"status": "overwritten"}

        changed, affected, restored = restore_source_audited_cashflow_backups(rows, backups)

        self.assertTrue(changed)
        self.assertEqual(affected, 1)
        self.assertGreater(restored, 0)
        self.assertEqual(row["cashflow_period_basis"], "year_to_date")
        self.assertEqual(row["operating_cash_flow_ytd"], -5202620)
        self.assertEqual(row["financing_cash_flow"], 5302391)
        self.assertEqual(row["cash_ending"], 977372)
        self.assertEqual(row["cashflow_source_reconciliation"]["status"],
                         "PASS_ARITHMETIC_RECONCILED")
        self.assertIn("brokerage_revenue", row["financial_line_items_extracted_fields"])
        self.assertIn("operating_cash_flow_ytd", row["financial_line_items_extracted_fields"])
        self.assertNotIn("operating_cash_flow_ytd", row["financial_line_items_rejected_fields"])


    def test_ssi_and_raw_source_audit_variants_are_preserved(self):
        symbol = "KDH"
        source_index = "https://finance.vietstock.vn/KDH/tai-tai-lieu.htm?doctype=1"
        audit_variants = [
            (
                {
                    "source_index_url": source_index,
                    "tolerance_percent": 0.01,
                    "ytd_flow_components_within_tolerance": True,
                    "quarter_flow_components_within_tolerance": True,
                    "ytd_cash_bridge_within_tolerance": True,
                    "quarter_cash_bridge_within_tolerance": True,
                },
                {},
            ),
            (
                {
                    "source_index_url": source_index,
                    "tolerance_percent": 0.01,
                    "no_balancing_plug": True,
                },
                {
                    "no_balancing_plug": True,
                    "source_values_raw_thousand_vnd": {"operating": -633698923, "net": 1069523944},
                },
            ),
        ]
        for audit, revision in audit_variants:
            with self.subTest(audit=audit):
                row = {
                    "period": "2026-Q1",
                    "unit": "triệu VND",
                    "source_index_url": source_index,
                    "source_archive_file": "reports/raw/KDH/test-source.pdf",
                    "cashflow_period_basis": "year_to_date",
                    "operating_cash_flow_ytd": -633699,
                    "cash_ending_reported_ytd": 3643809,
                    "financial_line_items_extracted_fields": [
                        "operating_cash_flow_ytd", "cash_ending_reported_ytd",
                    ],
                    "financial_line_items_rejected_fields": [],
                    "cashflow_source_reconciliation": audit,
                    "cashflow_audit_revision": revision,
                }
                rows = [row]
                backups = capture_source_audited_cashflow_backups(rows, symbol)
                self.assertIn("2026-Q1", backups)
                row["cashflow_period_basis"] = "quarterly_reported"
                row["operating_cash_flow_ytd"] = None
                row["cash_ending_reported_ytd"] = None
                changed, affected, restored = restore_source_audited_cashflow_backups(rows, backups)
                self.assertTrue(changed)
                self.assertEqual(affected, 1)
                self.assertGreater(restored, 0)
                self.assertEqual(row["cashflow_period_basis"], "year_to_date")
                self.assertEqual(row["operating_cash_flow_ytd"], -633699)
                self.assertEqual(row["cash_ending_reported_ytd"], 3643809)


if __name__ == "__main__":
    unittest.main()
