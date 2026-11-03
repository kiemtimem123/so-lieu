# IDC Q2/2026 — visual PDF review

- VietstockFinance document ID: **556340**
- Scope: consolidated
- ZIP: `reports/raw/IDC/auto-idc-20261021/5e5637e71fa303a7.zip`
- English PDF member: `2_idc_2026_7_31_a5004ca_en_financialstatementshn_q2_2026_s.pdf`
- Source URL: https://static2.vietstock.vn/data/HNX/2026/BCTC/VN/QUY%202/IDC_Baocaotaichinh_Q2_2026_Hopnhat.zip?ver=fec9e0e5
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41695506922
- Artifact: `vietstock-source-review-IDC-2026-Q2`, ID `13261640367`, SHA-256 `cc511d5804b930f5df2b3be6e08fa6a74df55581d368e4a7fa89090fce8f2241`.
- Rendered PDF pages 8–14 at 180 DPI. B01 8–11, B02 12, B03 13–14.

## B01 — balance sheet as at 30 June 2026 (VND)

| Item | Value |
|---|---:|
| Current assets | 16,424,882,607,866 |
| Cash and cash equivalents | 608,684,579,632 |
| Short-term investments | 6,612,747,709,157 |
| Current receivables | 1,398,487,922,279 |
| Inventory | 7,737,431,153,217 |
| Other current assets | 67,531,243,581 |
| Non-current assets | 7,121,143,339,714 |
| Fixed assets | 2,828,137,956,093 |
| Total assets (row 280) | 23,546,025,947,580 |
| Current liabilities | 5,609,121,115,090 |
| Non-current liabilities | 9,106,756,094,816 |
| Total liabilities (row 300) | 14,715,877,209,906 |
| Equity (row 400) | 8,830,148,737,674 |
| Total liabilities and equity (row 440) | 23,546,025,947,580 |

B01 composition totals and row 280 = row 300 + row 400 have 0 VND residuals.

## B02 — Q2/2026 standalone column (VND)

The first numeric column is **the second quarter of 2026**, the third is H1/2026 YTD. Snapshot top-level quarter fields use the first column. H1 is retained separately in `income_statement_source_ytd_raw_vnd`.

| Item | Q2/2026 |
|---|---:|
| Gross revenue | 2,270,556,204,685 |
| Deductions | (66,825,128) |
| Net revenue | 2,270,489,379,557 |
| Cost of goods sold | (1,421,483,331,885) |
| Gross profit | 849,006,047,672 |
| Finance income | 144,735,815,482 |
| Finance expenses | (56,657,259,572) |
| Interest expense | (56,420,402,688) |
| Selling expenses | (22,117,041,607) |
| General and administrative expenses | (67,646,607,403) |
| Share of profit in associates | 419,004,202 |
| Operating profit | 847,739,958,774 |
| Other income | 706,442,579 |
| Other expenses | (15,511,032,827) |
| Other profit/(loss) | (14,804,590,248) |
| Profit before tax | 832,935,368,526 |
| Current tax expense | (179,411,251,901) |
| Deferred tax income | 9,809,689,654 |
| Net profit after tax | 663,333,806,279 |
| Parent-attributable net profit | 609,810,412,292 |
| Non-controlling interests | 53,523,393,987 |
| Basic / diluted EPS | 1,461 / 1,461 |

All B02 revenue, gross profit, operating profit, other profit, PBT, tax/PAT and parent/NCI bridges have 0 VND residuals. H1/2026 YTD values remain preserved separately.

## B03 — cash flow (VND)

### H1/2026 current-period YTD as reported

| Item | Value |
|---|---:|
| CFO | (5,019,037,910) |
| CFI | 412,225,133,057 |
| CFF | (352,471,108,238) |
| Net increase in cash | 54,734,986,909 |
| Opening cash (reported YTD) | 553,943,475,131 |
| FX effect | 6,117,592 |
| Closing cash | 608,684,579,632 |
| Capex line 21 | (158,418,483,835) |
| Dividends paid | (74,115,054,425) |

The H1 flow bridge and H1 cash bridge both reconcile exactly (0 VND). The adjacent H1/2025 column is explicitly labelled **As restated – Note 41** and remains separate; it is not used as the current-year calculation basis.

### Q2/2026 standalone derived from H1 minus Q1/2026

| Item | Q2 standalone |
|---|---:|
| CFO | (202,543,174,911) |
| CFI | 480,833,384,534 |
| CFF | (471,228,735,423) |
| Net change in cash | (192,938,525,800) |
| FX effect | 2,812,837 |
| Opening cash (Q1 reported close) | 800,729,495,703 |
| Closing cash (Q2 report) | 608,684,579,632 |
| Capex line 21 delta | 113,451,875,677 |
| Dividends paid delta | (37,483,555,225) |

The Q2 standalone flow-component bridge is exact (0 VND). The cash bridge residual is **-890,796,892 VND**, equivalent to **0.1463%** of Q2 closing cash, above the allowed **0.01%** tolerance.

### Cross-period opening-cash exception — unresolved

- Q1/2026 report B03 closing cash: **800,729,495,703 VND**.
- Q2/2026 report H1 B03 opening cash: **553,943,475,131 VND**.
- Q2/2026 B01 comparative at 31 December 2025 is marked **As restated – Note 41** and also shows **553,943,475,131 VND**, which is **890,796,892 VND** above original Q4/2025 closing cash **553,052,678,239 VND**.
- The H1/2026 YTD cash bridge itself reconciles exactly. When Q2 standalone is calculated as H1 YTD less the originally reported Q1/2026 cashflows, the quarter flow components reconcile but the Q1-close-to-Q2-close cash bridge leaves **-890,796,892 VND** residual (**0.1463%**), above 0.01%.
- Keep all reported source values and derived quarter flows unchanged; do not insert a balancing plug or assume the prior period is restated without a source statement confirming it. Mark the Q2 standalone cash bridge as pending cross-period basis review.

## Status

**B01/B02 visual review PASS. B03 H1/2026 YTD PASS. Q2 standalone cashflow: manual review exception above 0.01%.** Data commit: `1f1449355dd200ccba8b77fa5e91024980078362`. The report is visually reviewed; the cash-basis exception remains open and must be resolved or explicitly carried as a source-basis exception before final IDC closeout.


## Note 41 — direct visual check of the opening-cash restatement

A second rendering pass inspected PDF pages 60–67 at 180 DPI. PDF page **66** (printed page **61**) contains Note 41, “Reclassification of corresponding data in accordance with Circular 99”.

The note explicitly shows for 31 December 2025:
- Cash equivalents previously stated: **474,491,428,405 VND**
- Note 41 adjustment: **+890,796,892 VND**
- Cash equivalents as restated: **475,382,225,297 VND**
- Cash (unchanged): **78,561,249,834 VND**
- Total cash and cash equivalents therefore changes from **553,052,678,239 VND** to **553,943,475,131 VND**.

This is the exact amount and basis behind the H1/2026 B03 opening-cash difference. It explains the origin of the exception. It does **not** make the Q2 standalone B03 cash bridge pass: after deriving Q2 by H1/2026 YTD minus Q1/2026 as-published values, the Q2-only cash bridge still has a **-890,796,892 VND** residual (**0.1463%**), above 0.01%. Do not force this into CFO/CFI/CFF, do not change Q1 values, and do not use a balancing plug. Keep this as a documented opening-balance restatement exception until a same-basis Q1/2026 statement is available or the reporting basis is formally reconciled.

Note 41 visual evidence:
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41697391168
- Artifact ID: `13262111894`, name `vietstock-source-review-IDC-2026-Q2`, pages 60–67 at 180 DPI.
- Page 66 image SHA-256: `72a16c5383e506eafd84a10e41c2e9f604fac5b261869f5832371e80b8276d4e`.
