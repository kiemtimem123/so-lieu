# IDC Q1/2026 — kiểm tra trực quan PDF

- Nguồn: VietstockFinance IDC, BCTC hợp nhất Q1/2026.
- PDF: `reports/raw/IDC/auto-idc-20261021/229a1ff9af9d3e1b.pdf`
- URL: https://static2.vietstock.vn/data/HNX/2026/BCTC/VN/QUY%201/IDC_Baocaotaichinh_Q1_2026_Hopnhat.pdf
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41694161229
- Artifact: `vietstock-source-review-IDC-2026-Q1`, ID `13258496176`, digest `16f7b72e32ada60f564b478a7119f96cbc79b3eb64cf324c3aa5a2893901516d`.
- Rendered PDF pages 8–14 at 180 DPI. B01 8–11; B02 12; B03 13–14.

## B01 — balance sheet (VND)

| Item | Value |
|---|---:|
| Current assets | 10,087,525,251,101 |
| Cash and cash equivalents | 800,729,495,703 |
| Short-term investments | 6,841,660,868,866 |
| Short-term receivables | 1,039,082,103,804 |
| Inventories | 1,336,544,952,533 |
| Other current assets | 69,507,830,195 |
| Non-current assets | 13,451,977,379,319 |
| Fixed assets | 2,875,737,262,368 |
| Total assets (row 280) | 23,539,502,630,420 |
| Current liabilities | 5,593,032,195,552 |
| Long-term liabilities | 9,096,732,263,053 |
| Total liabilities (row 300) | 14,689,764,458,605 |
| Equity (row 400) | 8,849,738,171,815 |
| Total liabilities and equity (row 440) | 23,539,502,630,420 |

All B01 component totals and balance equation residuals are 0 VND.

## B02 — Q1/2026 standalone (VND)

| Item | Value |
|---|---:|
| Gross revenue | 1,485,625,112,674 |
| Deductions | (100,472,253) |
| Net revenue | 1,485,524,640,421 |
| Cost of goods sold | (1,096,785,999,513) |
| Gross profit | 388,738,640,908 |
| Finance income | 131,515,653,570 |
| Finance expenses | (58,967,381,247) |
| Interest expense | (58,741,206,811) |
| Share of profit in associates | 407,741,448 |
| Selling expenses | (18,525,479,401) |
| Administrative expenses | (53,853,448,503) |
| Operating profit | 389,315,726,775 |
| Other income | 32,552,495,178 |
| Other expenses | (1,571,094,975) |
| Other profit | 30,981,400,203 |
| Profit before tax | 420,297,126,978 |
| Current tax expense | (83,687,912,608) |
| Deferred tax income | 1,297,966,689 |
| Net profit after tax | 337,907,181,059 |
| Parent-attributable net profit | 270,595,917,639 |
| Non-controlling interests | 67,311,263,420 |
| Basic / diluted EPS | 713 / 713 |

**Important EPS correction:** the first column on B02 is Q1/2026, EPS 713. EPS 902 belongs to the Q1/2025 comparative column and was removed from the Q1/2026 record. Old parser false candidates for selling expenses (217) and operating profit (981) were cleared; visually confirmed values are retained.

All gross-profit, operating-profit, other-profit, PBT, tax/PAT and parent/NCI bridges have 0 VND residual.

## B03 — Q1/2026 cash flow (VND)

Q1/2026 is both the quarter and YTD period.

| Item | Value |
|---|---:|
| CFO | 197,524,137,001 |
| CFI | (68,608,251,477) |
| CFF | 118,757,627,185 |
| Net increase in cash | 247,673,512,709 |
| Opening cash | 553,052,678,239 |
| FX effect | 3,304,755 |
| Closing cash | 800,729,495,703 |
| Capex | (271,870,359,512) |
| Dividends paid | (36,631,499,200) |

Flow bridge and cash bridge residuals are 0 VND; opening cash equals Q4/2025 closing cash.

## Status

**B01/B02/B03 visually reviewed and PASS.** Data commit: `cb98a0bfc9127c3e78eafa23466ec08fcd57f1fe`. No OCR rerun. Next period: **IDC Q2/2026**.
