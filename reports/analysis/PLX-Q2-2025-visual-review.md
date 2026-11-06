# PLX Q2/2025 — B01/B02/B03 visual review

## Source and visual evidence
- VietstockFinance document ID: **514768**.
- Consolidated Q2/2025 report: `reports/raw/PLX/auto-plx-20261021/90195e13c974fbad.pdf`.
- Official catalogue: `https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1`.
- Original PDF pages **2–7** directly reviewed at **300 DPI**: B01 pages 2–4, B02 page 5, B03 pages 6–7.
- Render run **42147883316**, artifact **13471345462**.

## B01 — PASS
At 30-Jun-2025, raw VND:
- Current assets **66,274,987,488,379**; non-current assets **21,135,983,567,100**; total assets **87,410,971,055,479**.
- Current liabilities **58,473,208,235,977**; long-term liabilities **759,564,936,223**; total liabilities **59,232,773,172,200**.
- Equity **28,178,197,883,279**.
- Cash **6,546,709,785,535**; cash equivalents **4,218,375,025,514**; total **10,765,084,811,049**.
- Total assets = liabilities + equity exactly; cash components also sum exactly.

## B02 — PASS within each report column
Q2 current-year column:
- Gross revenue **77,083,481,942,676**; deductions **29,106,368,392**; net revenue **77,054,375,574,284**.
- COGS **71,919,641,393,348**; gross profit **5,134,734,180,936**.
- Financial income **441,174,201,136**; financial expense **327,505,743,680**; interest expense **180,781,974,118**.
- Associates **150,267,587,738**; selling **3,461,920,159,645**; admin **307,988,580,517**.
- Operating profit **1,628,761,485,968**.
- Other income **23,897,415,151**; other expenses **14,682,992,103**; other result **9,214,423,048**.
- PBT **1,637,975,909,016**; current tax **323,685,620,958**; deferred tax **(54,028,355,821)**; total tax **269,657,265,137**.
- PAT **1,368,318,643,879**; parent PAT **1,283,730,540,279**; NCI PAT **84,588,103,600**; EPS **899 VND/share**.

H1/YTD current-year column:
- Gross revenue **144,973,653,282,323**; deductions **58,247,220,383**; net revenue **144,915,406,061,940**.
- COGS **136,068,769,466,227**; gross profit **8,846,636,595,713**.
- Financial income **862,936,723,429**; financial expense **621,108,336,246**; interest expense **346,353,679,124**.
- Associates **264,558,244,089**; selling **6,815,143,463,708**; admin **571,596,250,681**.
- Operating profit **1,966,283,512,596**.
- Other income **53,349,791,916**; other expenses **23,273,743,937**; other result **30,076,047,979**.
- PBT **1,996,359,560,575**; current tax **425,402,770,092**; deferred tax **(8,130,653,935)**; total tax **417,272,116,157**.
- PAT **1,579,087,444,418**; parent PAT **1,417,145,350,199**; NCI PAT **161,942,094,219**; EPS **926 VND/share**.

Q2 and H1 income-statement internal equations all have residual **0 VND**. Parent PAT + NCI PAT = consolidated PAT in both columns.

### Q1 + Q2 versus H1 cross-period check
All main B02 rows reconcile exactly, except for an equal offsetting difference:
- H1 other income minus Q1 other income minus Q2 other income: **(711,102,062 VND)**.
- H1 other expenses minus Q1 other expenses minus Q2 other expenses: **(711,102,062 VND)**.
- Other result difference: **0 VND**.
No explanation for the equal classification difference was found in the reviewed notes. Preserve the published Q1, Q2 and H1 lines; mark this classification item **PENDING**. Do not redistribute or plug it.

## B03 — PASS
Original H1/YTD cashflow, raw VND:
- CFO **(442,992,517,070)**.
- CFI **(5,598,916,341,260)**.
- CFF **1,855,066,395,925**.
- Net cash movement **(4,186,842,462,405)**.
- Opening cash/equivalents **14,933,068,792,315**.
- FX effect **18,858,481,139**.
- Closing cash/equivalents **10,765,084,811,049**.
- CAPEX **(549,225,062,363)**; dividends paid **(1,514,375,702,417)**.

H1 cashflow component sum and cash bridge residuals are both **0 VND**.

### Q2 standalone cashflow
Q2 standalone is H1/YTD B03 less Q1/YTD B03 from the original Q1 consolidated report:
- CFO **2,106,791,853,375**.
- CFI **(1,021,432,844,145)**.
- CFF **(792,003,743,906)**.
- Net cash movement **293,355,265,324**.
- FX effect **24,995,968,933**.
- Opening cash **10,446,733,576,792** (Q1 close).
- Closing cash **10,765,084,811,049**.
- CAPEX **(358,908,217,763)**.
- Dividends paid **(1,514,365,622,917)**.

Q2 standalone flow sum, cash bridge, and H1-minus-Q1-minus-Q2 component residuals are all **0 VND**. Negative cash flows remain negative; no plug is used.

## B04 / NCI equity bridge — PENDING
The reviewed Q2/2025 report includes B01, B02 and B03 but does not present a separate B04 statement of changes in equity. Notes reviewed contain the NCI accounting policy but no transaction-by-transaction bridge.
- Beginning NCI equity at 1-Jan-2025: **3,285,111,765,231 VND**.
- Ending NCI equity at 30-Jun-2025: **3,160,555,849,966 VND**.
- Observed NCI equity change: **(124,555,915,265 VND)**.
- H1 NCI PAT: **161,942,094,219 VND**.
- Implied non-PAT equity movement would be **(286,498,009,484 VND)**, but the report does not identify the underlying transactions. This is a calculated difference only, not an explanation.
Keep B04/NCI movement **PENDING**. Do not treat it as NCI PAT or plug the difference.

## Closeout
- B01: **PASS**.
- B02 current and H1 columns: **PASS internally**.
- B03 H1 and Q2 standalone: **PASS, all bridges residual 0 VND**.
- B02 other-income/other-expense classification difference: **PENDING**.
- B04/NCI transaction bridge: **PENDING, no separate B04/transaction schedule in the reviewed source**.
- Core data can proceed with these two exceptions explicitly recorded; do not overwrite source columns or infer balancing values.