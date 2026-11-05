# PLX Q2/2026 — full B01/B02/B03 visual review

## Source and evidence
- VietstockFinance document ID: **556113**.
- Original consolidated report: `reports/raw/PLX/auto-plx-20261021/925339daf7038fe2.pdf`.
- Official catalog: `https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1`.
- PDF pages visually inspected at **300 DPI**: B01 pages 2–4, B02 page 5, B03 pages 6–7, Note 1 cash composition page 20.
- Successful render: workflow run **42052798406**, artifact **13426693096**, artifact name `vietstock-source-review-PLX-2026-Q2-B03-CASHFLOW`.

## B01 — PASS
Values at 30-Jun-2026:
- Total current assets: **61,285,423,671,831 VND**.
- Non-current assets: **26,590,890,734,017 VND**.
- Total assets: **87,876,314,405,848 VND**.
- Current liabilities: **57,743,007,260,113 VND**.
- Long-term liabilities: **979,722,714,289 VND**.
- Total liabilities: **58,722,729,974,402 VND**.
- Equity: **29,153,584,431,446 VND**.
- Liabilities + equity = assets exactly.

Cash and equivalents at 30-Jun-2026:
- Cash on hand: **43,229,842,772 VND**.
- Demand bank deposits: **4,649,314,967,866 VND**.
- Cash in transit: **251,434,050,875 VND**.
- Cash total: **4,943,978,861,513 VND**.
- Cash equivalents: **1,379,978,340,544 VND**.
- Total cash and equivalents: **6,323,957,202,057 VND**.

## B02 — PASS
Q2/2026 standalone column, all raw VND:
- Gross sales revenue: **136,253,115,852,196**.
- Revenue deductions: **34,982,126,852**.
- Net revenue: **136,218,133,725,344**.
- Cost of goods sold: **128,526,418,908,129**.
- Gross profit: **7,691,714,817,215**.
- Financial income: **443,350,028,596**.
- Financial expense: **293,982,236,930**.
- Interest expense: **231,004,860,336**.
- Selling expenses: **4,033,774,993,287**.
- Administrative expenses: **416,415,124,252**.
- Share of profit of associates: **153,737,337,273**.
- Operating profit: **3,335,629,828,615**.
- Other income: **53,765,938,127**.
- Other expenses: **25,243,490,710**.
- Other result: **28,522,447,417**.
- Profit before tax: **3,364,152,276,032**.
- Current income tax: **347,307,997,529**.
- Deferred income tax: **(27,878,345,505)**.
- Total income tax: **319,429,652,024**.
- Profit after tax: **3,044,722,624,008**.
- Parent-attributable profit: **2,808,812,523,261**.
- NCI profit: **235,910,100,747**.
- EPS: **2,329 VND/share**.

H1/2026 cumulative values kept separately:
- Net revenue: **234,916,069,825,473 VND**.
- Cost of goods sold: **223,523,610,553,860 VND**.
- Gross profit: **11,392,459,271,613 VND**.
- Financial income: **805,598,607,189 VND**.
- Financial expenses: **891,322,856,341 VND**.
- Interest expense: **421,457,177,555 VND**.
- Selling expenses: **8,025,989,984,593 VND**.
- Administrative expenses: **743,334,494,655 VND**.
- Share of profit of associates: **307,334,494,655 VND**.
- Profit before tax: **2,868,337,224,036 VND**.
- Current tax: **536,705,911,180 VND**.
- Deferred tax: **(50,614,185,245 VND)**.
- Total tax: **486,091,725,935 VND**.
- Profit after tax: **2,382,245,498,101 VND**.
- Parent-attributable profit: **2,045,838,842,073 VND**.
- NCI profit: **336,406,656,028 VND**.
- EPS: **1,676 VND/share**.

Revenue, cost of sales, gross profit, operating profit, PBT, tax, PAT and Parent/NCI arithmetic all reconcile to the source.

## B03 — PASS
Original B03 reports H1/YTD cumulative amounts:
- CFO: **1,224,204,547,047 VND**.
- CFI: **5,536,623,100,159 VND**.
- CFF: **(8,019,953,358,007 VND)**.
- Net cash movement: **(1,259,125,710,801 VND)**.
- Opening cash/equivalents: **7,588,239,730,231 VND**.
- FX effect: **(5,156,817,373 VND)**.
- Closing cash/equivalents: **6,323,957,202,057 VND**.
- CAPEX: **(949,550,459,737 VND)**.
- Dividends paid: **(217,052,009 VND)**.

H1 flow sum:
CFO + CFI + CFF = net cash movement, residual **0 VND**.

H1 cash bridge:
Opening cash + net movement + FX = closing cash, residual **0 VND**.

## Q2 standalone extraction
The original PDF presents H1/YTD cashflow. Q2 standalone is derived only by subtracting Q1/2026 YTD values from H1/2026 YTD, using the same consolidated report basis:
- CFO: **(8,151,521,210,218 VND)**.
- CFI: **4,771,932,657,800 VND**.
- CFF: **(330,860,581,285 VND)**.
- Net movement: **(3,710,449,133,703 VND)**.
- FX effect: **0 VND**.
- Opening cash: **10,034,406,335,760 VND** (Q1 closing).
- Closing cash: **6,323,957,202,057 VND**.
- CAPEX: **(591,073,777,428 VND)**.
- Dividends paid: **(112,351,369 VND)**.

Q2 standalone flow sum and opening-to-closing cash bridge both have residual **0 VND**. All H1 minus Q1 minus Q2 component differences are exactly zero. No balancing plug is used and negative cash flows retain their negative sign.

## Opening cash basis
The Q1/2026 report explicitly labels the opening balance “Số đầu năm (phân loại lại)”. The reported opening **7,588,239,730,231 VND** matches Q1 B03, Q1 Note 1 and Q2 H1 opening; preserve the original Q4/2025 close separately. This is a reclassified comparative basis, not an internal Q2 cashflow break.

## Closeout
- B01: **PASS**.
- B02: **PASS**.
- B03 H1/YTD: **PASS**.
- Q2 standalone cashflow derived from same-source Q1/YTD: **PASS**.
- Note 1 cash composition: **PASS**.
- Full direct visual review: **COMPLETE**.
- All principal arithmetic residuals: **0 VND**.
- No source values inferred from an accounting balance plug or overwritten.