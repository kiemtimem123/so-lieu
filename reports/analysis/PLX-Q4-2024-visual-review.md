# PLX Q4/2024 — full B01/B02/B03 visual review (interim report)

## Source and evidence
- VietstockFinance document ID: **490581**.
- Consolidated Q4/2024 interim report: `reports/raw/PLX/auto-plx-20261021/b80662485ac3e19f.pdf`.
- Official catalog: `https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1`.
- Original pages visually reviewed at 300 DPI: B01 pages 2–4, B02 page 5, B03 pages 6–7.
- Render workflow run **42077417114**, artifact **13438762714**, artifact name `vietstock-source-review-PLX-2024-Q4-FULL-STATEMENTS`.

## B01 — PASS
At 31-Dec-2024 in the interim Q4 report:
- Current assets: **60,085,476,980,256 VND**.
- Non-current assets: **21,322,766,035,906 VND**.
- Total assets: **81,408,243,016,162 VND**.
- Current liabilities: **51,289,874,919,789 VND**.
- Long-term liabilities: **816,109,301,553 VND**.
- Total liabilities: **52,105,984,221,342 VND**.
- Equity: **29,302,258,794,820 VND**.
- Liabilities + equity = total assets exactly.

Cash components:
- Cash: **5,329,069,053,043 VND**.
- Cash equivalents: **9,733,066,779,703 VND**.
- Total cash/equivalents: **15,062,135,832,746 VND**, matching B03 closing exactly.

## B02 — PASS within the Q4 interim report

### Q4 standalone current-year column
- Gross revenue: **71,065,724,665,296 VND**.
- Revenue deductions: **27,952,804,937 VND**.
- Net revenue: **71,037,771,860,359 VND**.
- Cost of goods sold: **66,433,806,493,603 VND**.
- Gross profit: **4,603,965,366,756 VND**.
- Financial income: **294,570,788,425 VND**.
- Financial expense: **251,199,772,354 VND**.
- Interest expense: **61,253,568,311 VND**.
- Share of profit of associates: **125,496,361,413 VND**.
- Selling expenses: **3,893,905,168,623 VND**.
- Administrative expenses: **281,813,829,201 VND**.
- Operating profit: **597,113,746,416 VND**.
- Other income: **211,345,031,140 VND**.
- Other expenses: **48,276,467,894 VND**.
- Other result: **163,068,563,246 VND**.
- Profit before tax: **760,182,309,662 VND**.
- Current income tax: **157,142,773,836 VND**.
- Deferred income tax: **(9,040,994,846 VND)**.
- Total income tax: **148,101,778,990 VND**.
- Profit after tax: **612,080,530,672 VND**.
- Parent-attributable profit: **545,471,386,870 VND**.
- NCI profit: **66,609,143,802 VND**.
- EPS: **317 VND/share**.

### FY2024 cumulative column in the Q4 interim report
- Gross revenue: **284,134,399,781,561 VND**.
- Revenue deductions: **106,621,928,874 VND**.
- Net revenue: **284,027,777,852,687 VND**.
- Cost of goods sold: **266,712,297,374,939 VND**.
- Gross profit: **17,315,480,477,748 VND**.
- Financial income: **1,635,301,023,198 VND**.
- Financial expense: **1,192,970,667,813 VND**.
- Interest expense: **568,872,297,088 VND**.
- Share of profit of associates: **510,981,571,441 VND**.
- Selling expenses: **13,530,920,803,110 VND**.
- Administrative expenses: **1,036,924,999,773 VND**.
- Operating profit: **3,700,946,601,691 VND**.
- Other income: **340,575,036,030 VND**.
- Other expenses: **81,371,321,340 VND**.
- Other result: **259,203,714,690 VND**.
- Profit before tax: **3,960,150,316,381 VND**.
- Current income tax: **796,864,384,940 VND**.
- Deferred income tax: **67,228,268 VND**.
- Total income tax: **796,931,613,208 VND**.
- Profit after tax: **3,163,218,703,173 VND**.
- Parent-attributable profit: **2,890,002,145,491 VND**.
- NCI profit: **273,216,557,682 VND**.
- Reported FY EPS: **1,829 VND/share**.

The original image corrected three OCR errors:
1. FY revenue deductions are **106,621,928,874 VND**, not 106,462,192,882 VND.
2. Q4 parent PAT is **545,471,386,870 VND**, not 254 million VND.
3. FY deferred tax is **67,228,268 VND**.

All Q4 and FY B02 internal equations pass with residual **0 VND**, including revenue less deductions, gross profit, operating profit, other result, PBT, tax/PAT, and parent/NCI attribution. EPS is not an additive financial statement line and is not included in period-difference tests.

## B03 — PASS
Original FY/YTD B03:
- CFO: **1,995,120,309,795 VND**.
- CFI: **2,872,147,303,085 VND**.
- CFF: **(3,815,580,079,005 VND)**.
- Net cash movement: **1,051,687,533,875 VND**.
- Beginning cash/equivalents: **14,048,245,083,619 VND**.
- FX effect: **(37,796,784,748 VND)**.
- Ending cash/equivalents: **15,062,135,832,746 VND**.
- CAPEX: **(1,986,157,576,601 VND)**.
- Dividends paid: **(1,905,060,785,720 VND)**.

FY/YTD component sum and cash bridge both have residual **0 VND**.

### Q4 standalone B03
Derived solely as original FY/YTD B03 less original Q3 9M/YTD B03:
- CFO: **877,861,959,523 VND**.
- CFI: **(2,372,352,866,804 VND)**.
- CFF: **4,263,109,924,443 VND**.
- Net cash movement: **2,768,619,017,162 VND**.
- FX effect: **0 VND**.
- Opening cash: **12,293,516,815,584 VND** (Q3 close).
- Closing cash: **15,062,135,832,746 VND**.
- CAPEX: **(831,258,020,554 VND)**.
- Dividends paid: **(640,383,375 VND)**.

Q4 standalone component sum and cash bridge both have residual **0 VND**. All FY-minus-9M-minus-Q4 component differences are zero.

## Q3 9M cross-check from Q4
For B02, the Q4 interim FY/YTD column less Q4 standalone current-quarter values reproduces the Q3 report's 9M/YTD values exactly for gross revenue, deductions, net revenue, COGS, gross profit, financial income/expense, interest expense, associates, selling/admin expense, operating profit, PBT, current/deferred/total tax, PAT, Parent PAT and NCI PAT.

One classification exception remains:
- FY/YTD other income less Q4 other income = **129,230,004,890 VND**, while Q3 9M reported **129,861,000,680 VND**.
- FY/YTD other expenses less Q4 other expenses = **33,094,853,446 VND**, while Q3 9M reported **33,725,849,236 VND**.
- Both differ by **(630,995,790 VND)**; net other result is unchanged and exactly reconciles to **96,135,151,444 VND**.

This is kept as an offsetting classification exception, not plugged.

## Q3 2024 B02 cross-period exception remains PENDING
Q4 confirms the Q3 9M/YTD column as the carried cumulative basis. It does **not** resolve the separate mismatch between Q3 current-quarter B02 values and Q1 + Q2 + Q3 standalone values; several lines still differ by more than 0.01%. The Q3 report pages reviewed did not disclose a reason. Preserve all Q1/Q2/Q3 reported current-quarter values and Q3 9M values without backsolving or overwrite. Continue review against the separately audited FY2024 VietstockFinance report; do not mark Q3 fully complete yet.

## Interim versus audited year-end
This Q4 interim report reports 31-Dec-2024 cash/equivalents of **15,062,135,832,746 VND**. The separately issued audited FY2024 report reports **14,933,068,792,315 VND**. Preserve both original document bases. The latter is the audited basis used for Q1/2025 opening and must not overwrite the Q4 interim source record.

## Closeout
- B01: **PASS**.
- B02: **PASS within report**.
- B03 FY/YTD and Q4 standalone: **PASS**.
- Full original PDF visual review: **COMPLETE**.
- Main arithmetic residuals: **0 VND**.
- Q3 B02 quarter-versus-YTD exception: **PENDING**, not plugged.
- FY audited versus Q4 interim cash difference: preserved as separate reporting bases.
