# PLX Q3/2024 — B01/B02/B03 visual review and open B02 cross-period exception

## Source and visual evidence
- VietstockFinance document ID: **483929**.
- Consolidated Q3/2024 report: `reports/raw/PLX/auto-plx-20261021/01400b120484d2c7.pdf`.
- Official document catalog: `https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1`.
- Rendered at **300 DPI**: workflow run **42057655509**, artifact **13430312361**.
- Direct image review: B01 PDF pages 2–4, B02 page 5, B03 pages 6–7.

## B01 — PASS
As at 30-Sep-2024:
- Current assets: **49,620,976,389,763 VND**.
- Non-current assets: **20,568,127,461,605 VND**.
- Total assets: **70,189,103,851,368 VND**.
- Current liabilities: **40,691,667,265,528 VND**.
- Long-term liabilities: **822,402,724,335 VND**.
- Total liabilities: **41,514,069,989,863 VND**.
- Equity: **28,675,033,861,505 VND**.
- Total liabilities + equity = total assets exactly.

Cash and cash equivalents:
- Cash: **6,751,167,341,335 VND**.
- Cash equivalents: **5,542,349,474,249 VND**.
- Total: **12,293,516,815,584 VND**.

## B02 — within-report arithmetic PASS; cross-period exception PENDING

### Q3 standalone current-year column
- Gross revenue: **64,352,149,009,035 VND**.
- Revenue deductions: **27,759,775,244 VND**.
- Net revenue: **64,324,389,233,791 VND**.
- Cost of goods sold: **60,887,953,877,442 VND**.
- Gross profit: **3,436,435,356,349 VND**.
- Financial income: **495,756,246,975 VND**.
- Financial expense: **231,690,804,893 VND**.
- Interest expense: **174,618,679,639 VND**.
- Share of profit of associates: **108,984,884,024 VND**.
- Selling expenses: **3,318,400,967,579 VND**.
- Administrative expenses: **268,478,694,668 VND**.
- Operating profit: **222,606,020,208 VND**.
- Other income: **34,140,384,799 VND**.
- Other expenses: **15,534,724,395 VND**.
- Other result: **18,605,660,404 VND**.
- Profit before tax: **241,211,680,612 VND**.
- Current income tax: **85,772,393,306 VND**.
- Deferred income tax: **24,954,092,788 VND**.
- Total income tax: **110,726,486,094 VND**.
- Profit after tax: **130,485,194,518 VND**.
- Parent-attributable profit: **65,874,458,258 VND**.
- NCI profit: **64,610,736,260 VND**.
- EPS: **51 VND/share**.

Revenue less deductions, cost of goods sold/gross profit, operating profit, other result, PBT/tax/PAT and parent/NCI all reconcile exactly within the Q3 column.

### Nine-month cumulative current-year column
- Gross revenue: **213,068,675,116,265 VND**.
- Revenue deductions: **78,669,123,937 VND**.
- Net revenue: **212,990,005,992,328 VND**.
- Cost of goods sold: **200,278,490,881,336 VND**.
- Gross profit: **12,711,515,110,992 VND**.
- Financial income: **1,340,730,234,773 VND**.
- Financial expense: **941,770,895,459 VND**.
- Interest expense: **507,618,728,777 VND**.
- Share of profit of associates: **385,485,210,028 VND**.
- Selling expenses: **9,637,015,634,487 VND**.
- Administrative expenses: **755,111,170,572 VND**.
- Operating profit: **3,103,832,855,275 VND**.
- Other income: **129,861,000,680 VND**.
- Other expenses: **33,725,849,236 VND**.
- Other result: **96,135,151,444 VND**.
- Profit before tax: **3,199,968,006,719 VND**.
- Current tax: **639,721,611,104 VND**.
- Deferred tax: **9,108,223,114 VND**.
- Total tax: **648,829,834,218 VND**.
- Profit after tax: **2,551,138,172,501 VND**.
- Parent-attributable profit: **2,344,530,758,621 VND**.
- NCI profit: **206,607,413,880 VND**.
- EPS: **1,660 VND/share**.

The 9M values also reconcile internally.

### Cross-period discrepancy
The Q3 current-quarter column and 9M cumulative column do not reconcile to the previously saved Q1 and Q2 reports on several B02 rows. The residual is calculated as:

`9M/YTD as reported - Q1 standalone - Q2 standalone - Q3 standalone`

Selected residuals:
- Gross revenue / net revenue: **-277,445,575,623 VND** (**0.1302%** of 9M reported).
- Cost of goods sold: **-261,748,581,903 VND** (**0.1307%**).
- Gross profit: **-15,696,993,720 VND** (**0.1235%**).
- Financial income: **-35,179,997,175 VND** (**2.6239%**).
- Financial expense: **-38,298,557,467 VND** (**4.0667%**).
- Selling expenses: **-88,571,718,807 VND** (**0.9191%**).
- Administrative expenses: **-4,585,607,358 VND** (**0.6073%**).
- Operating profit: **+80,578,892,737 VND** (**2.5961%**).
- PBT: **+14,753,266,277 VND** (**0.4610%**).
- PAT: **+13,278,391,204 VND** (**0.5205%**).
- Parent PAT: **+6,185,638,652 VND** (**0.2638%**).
- NCI PAT: **+7,092,752,552 VND** (**3.4330%**).

Revenue deductions and share of profit of associates do reconcile exactly. These discrepancies exceed the project's 0.01% tolerance.

The original Q3 report's available notes were searched for explicit restatement, retrospective adjustment or reclassification language. No explanation for these B02 differences was found. The source images clearly show both current-quarter and YTD columns as transcribed above; neither column is replaced or backsolved.

**Status: `PENDING_EXCEPTION_OVER_0_01_PERCENT`.** Preserve Q1, Q2 and Q3 report values separately, do not plug, and do not mark Q3 complete. The next official-source check is Q4/2024 (and the audited FY2024 basis if accessible) to establish whether a later report reconciles or explains the Q3/YTD discrepancy.

## B03 — PASS
Original 9M/YTD B03 values:
- CFO: **1,117,258,350,272 VND**.
- CFI: **5,244,500,169,889 VND**.
- CFF: **(8,078,690,003,448 VND)**.
- Net cash movement: **(1,716,931,483,287 VND)**.
- Beginning cash/equivalents: **14,048,245,083,619 VND**.
- FX effect: **(37,796,784,748 VND)**.
- Closing cash/equivalents: **12,293,516,815,584 VND**.
- CAPEX: **(1,154,899,556,047 VND)**.
- Dividends paid: **(1,904,420,402,345 VND)**.

The 9M flow sum and cash bridge both reconcile exactly.

### Q3 standalone B03
Derived from the original Q3 9M/YTD report less the original Q2 H1/YTD report, both consolidated:
- CFO: **2,701,333,667,880 VND**.
- CFI: **(1,788,582,711,650 VND)**.
- CFF: **(4,106,675,810,055 VND)**.
- Net cash movement: **(3,193,924,853,825 VND)**.
- FX effect: **(74,771,369,589 VND)**.
- Opening cash: **15,562,213,038,998 VND** (Q2 close).
- Closing cash: **12,293,516,815,584 VND**.
- CAPEX: **(270,006,256,411 VND)**.
- Dividends paid: **0 VND**.

The Q3 standalone flow sum, opening-to-closing cash bridge, and YTD-minus-H1 component differences all have residual **0 VND**.

## Closeout state
- B01 visual and arithmetic: **PASS**.
- B02 within-report arithmetic and visual transcription: **PASS**.
- B02 cross-period 9M bridge: **PENDING**, over 0.01%.
- B03 9M/YTD and Q3 standalone: **PASS**.
- Full B01/B02/B03 image review: **DONE**.
- Source columns preserved separately; no balancing plug or unsupported correction.
- Next action: review official Q4/2024 report and compare its annual current-year values to Q3 9M and Q1/Q2/Q3 standalone before closing the exception.
