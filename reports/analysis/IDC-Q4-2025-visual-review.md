# IDC Q4/2025 — visual PDF review

- VietstockFinance document ID: **529902**
- Scope: consolidated
- Archive: `reports/raw/IDC/auto-idc-20261021/5ff8f3ce069a369e.zip`
- English PDF member: `1_idc_2026_1_29_0d3041b_en_financialstatementshn_q4_2025hn_s.pdf`
- Direct source archive: https://static2.vietstock.vn/data/HNX/2025/BCTC/VN/QUY%204/IDC_Baocaotaichinh_Q4_2025_Hopnhat.zip
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41693037890
- Artifact: `vietstock-source-review-IDC-2025-Q4`, ID `13257699370`, SHA-256 `231a4774ff398d0509dbc6630474f13a5ce9ab301c129ea877cb822d2b6915b8`, retention 14 days.
- Rendered PDF pages: 8–14 at 180 DPI. Metadata: `reports/raw/IDC/auto-idc-20261021/render-metadata-2025-Q4.json`.

## B01 — balance sheet (VND)

| Item | Value |
|---|---:|
| Current assets | 9,856,822,003,191 |
| Short-term investments (row 120) | 6,807,014,517,859 |
| Cash and cash equivalents | 553,052,678,239 |
| Non-current assets | 13,344,668,676,332 |
| Total assets (row 270) | 23,201,490,679,523 |
| Current liabilities (row 310) | 5,620,500,395,796 |
| Non-current liabilities (row 330) | 9,317,959,391,971 |
| Total liabilities (row 300) | 14,938,459,787,767 |
| Equity (row 400) | 8,263,030,891,756 |
| Total liabilities and equity (row 440) | 23,201,490,679,523 |

B01 asset composition, liabilities composition and assets = liabilities + equity all have 0 VND residual. The old parser candidate for short-term investments (909,607 million VND) was false; visual row 120 confirms 6,807,014,517,859 VND.

## B02 — Q4-only income statement (VND)

| Item | Value |
|---|---:|
| Revenue from sale of goods and services | 2,160,206,044,440 |
| Deductions | (67,932,722) |
| Net revenue | 2,160,138,111,718 |
| Cost of goods sold | (1,453,163,128,638) |
| Gross profit | 706,974,983,080 |
| Finance income | 108,952,409,062 |
| Finance expenses | (42,472,227,098) |
| Interest expense — as printed | (43,891,490,863) |
| Share of profit in associates | 180,518,355 |
| Selling expenses | (18,592,495,992) |
| General and administrative expenses | (92,138,853,752) |
| Operating profit | 662,904,333,655 |
| Other income | 10,212,684,319 |
| Other expenses | (13,897,429,941) |
| Other profit | (3,684,745,622) |
| Profit before tax | 659,219,588,033 |
| Current tax expense | (142,577,559,905) |
| Deferred tax income | 23,353,093,110 |
| Net profit after tax | 539,995,121,238 |
| Parent-attributable net profit | 449,103,567,116 |
| Non-controlling interests | 90,891,554,122 |
| Basic / diluted EPS | 1,183 / 1,183 |

Gross profit, operating profit, other profit, PBT, tax/PAT and parent/NCI bridges are exact.

### Source-reported interest-expense exception

The rendered PDF page 12 clearly prints interest expense **43,891,490,863 VND**, but the parent line for total finance expenses is only **42,472,227,098 VND**. The subline exceeds the parent by **1,419,263,765 VND**. This is recorded as an inconsistency in the published statement. Keep the visibly reported subline with a warning, do not change total finance expense or profit, and do not use the subline as an aggregate bridge input.

## B03 — cash flow (VND)

### FY2025 as reported

| Item | Value |
|---|---:|
| CFO | 3,913,940,809,873 |
| CFI | (7,009,893,958,684) |
| CFF | 1,460,905,190,082 |
| Net change in cash | (1,635,047,958,729) |
| Opening cash | 2,188,037,806,317 |
| FX effect | 62,830,651 |
| Closing cash | 553,052,678,239 |
| Capex | (3,103,468,210,215) |
| Dividends paid | (1,300,232,590,297) |

**Correction:** the old OCR took **91,523,594 VND** from the FY2024 comparative column. Page 14 directly confirms FY2025 FX is **62,830,651 VND**. With the corrected value, the FY2025 cash bridge residual is zero.

### Q4 standalone — same original reporting basis

Q4 standalone = FY2025 YTD minus 9M/2025 YTD from the original IDC Q3/2025 report.

| Item | Q4 standalone |
|---|---:|
| CFO | 970,200,007,993 |
| CFI | (2,329,374,796,016) |
| CFF | 1,120,543,443,747 |
| Net change in cash | (238,631,344,276) |
| FX effect | (2,537,404) |
| Opening cash | 791,686,559,919 |
| Closing cash | 553,052,678,239 |
| Capex | (1,300,428,928,495) |
| Dividends paid | (654,131,953,577) |

FY2025 flow and cash bridges, Q4 flow and cash bridges, and Q4 opening cash vs Q3 closing cash all reconcile with 0 VND residual. Exact raw values were calculated before rounding snapshot values to million VND.

## Status

**B01/B02/B03 visual review: PASS**, with one disclosed B02 source inconsistency for interest expense. Cashflow FX OCR correction is applied and both YTD and standalone cash bridges now reconcile exactly. Do not repeat Q4 core extraction. Next period: **IDC Q1/2026**.
