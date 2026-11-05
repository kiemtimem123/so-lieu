# PLX Q2/2024 — full visual review and OCR column corrections

## Source and evidence
- VietstockFinance document ID: **472667**.
- Consolidated report: `reports/raw/PLX/auto-plx-20261021/1cf87f21b5f884ad.pdf`.
- Official catalog: `https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1`.
- Visual render: 300 DPI, workflow run **42056381946**, artifact **13428873110**.
- Reviewed original PDF pages **2–7**: B01 pages 2–4, B02 page 5, B03 pages 6–7.

## B01 — PASS
At 30-Jun-2024:
- Current assets: **53,399,295,404,565 VND**.
- Non-current assets: **20,567,620,941,725 VND**.
- Total assets: **73,966,916,346,290 VND**.
- Current liabilities: **44,671,996,018,226 VND**.
- Long-term liabilities: **847,435,003,681 VND**.
- Total liabilities: **45,519,431,021,907 VND**.
- Equity: **28,447,485,324,383 VND**.
- Liabilities + equity = total assets exactly.

Cash and cash equivalents:
- Cash: **7,190,589,876,149 VND**.
- Cash equivalents: **8,371,623,162,849 VND**.
- Total: **15,562,213,038,998 VND**, matching B03 closing.

## B02 — PASS after original-image column correction
The PDF has four report columns: Q2 current year, Q2 prior year, H1 current year and H1 prior year. The OCR sidecar had shifted/mixed two current-year cells with the comparison columns. Visual values below are the current-year columns only.

Q2 standalone current-year:
- Gross revenue: **73,862,082,497,694 VND**.
- Revenue deductions: **25,217,547,762 VND**.
- Net revenue: **73,836,864,949,932 VND**.
- Cost of goods sold: **69,215,526,536,697 VND**.
- Gross profit: **4,621,338,413,235 VND**.
- Financial income: **430,195,812,674 VND**.
- Financial expense: **373,446,172,415 VND**.
- Interest expense: **177,325,750,833 VND**.
- Share of profit of associates: **165,725,475,694 VND**.
- Selling expense: **3,209,177,866,936 VND**.
- Administrative expense: **253,117,688,877 VND**.
- Operating profit: **1,381,517,973,375 VND**.
- Other income: **133,995,905,435 VND**.
- Other expense: **12,646,545,064 VND**.
- Other result: **121,349,360,371 VND**.
- Profit before tax: **1,502,867,333,746 VND**.
- Current tax: **239,262,468,957 VND**.
- Deferred tax: **(10,936,865,189 VND)**.
- Total tax: **228,325,603,768 VND**.
- Profit after tax: **1,274,541,729,978 VND**.
- Parent-attributable profit: **1,199,496,609,088 VND**.
- NCI profit: **75,045,120,890 VND**.
- EPS: **859 VND/share**.

H1/2024 cumulative current-year column:
- Gross revenue: **148,993,971,682,853 VND**.
- Revenue deductions: **50,909,348,693 VND**.
- Net revenue: **148,943,062,334,160 VND**.
- Cost of goods sold: **139,652,285,585,797 VND**.
- Gross profit: **9,290,776,748,363 VND**.
- Financial income: **880,153,984,973 VND**.
- Financial expense: **748,378,648,033 VND**.
- Interest expense: **371,249,868,090 VND**.
- Share of profit of associates: **276,500,326,004 VND**.
- Selling expense: **6,407,186,385,715 VND**.
- Administrative expense: **491,218,083,262 VND**.
- Operating profit: **2,800,647,942,330 VND**.
- Other income: **162,264,451,641 VND**.
- Other expense: **18,909,334,141 VND**.
- Other result: **143,355,117,500 VND**.
- Profit before tax: **2,944,003,059,830 VND**.
- Current tax: **550,591,731,628 VND**.
- Deferred tax: **(13,963,258,577 VND)**.
- Total tax: **536,628,473,051 VND**.
- Profit after tax: **2,407,374,586,779 VND**.
- Parent-attributable profit: **2,272,470,661,711 VND**.
- NCI profit: **134,903,925,068 VND**.
- EPS: **1,621 VND/share**.

The crucial OCR corrections were:
1. Q2 current-year financial income is **430,195,812,674 VND**, not the prior-year comparative **431,952,637,224 VND**.
2. H1 current-year share of profit of associates is **276,500,326,004 VND**, not the prior-year comparative **343,267,139,786 VND**.
3. Q2 current-year NCI profit is **75,045,120,890 VND**; parent + NCI = total PAT exactly.

With the correct current-year columns, revenue, gross profit, operating profit, other result, PBT, tax/PAT and Parent/NCI all reconcile exactly. The prior-year comparison columns remain unimported.

## B03 — PASS
The original Q2 report presents H1/YTD cumulative flows. Visual source values:
- CFO: **(1,584,075,317,608 VND)**.
- CFI: **7,033,082,881,539 VND**.
- CFF: **(3,972,014,193,393 VND)**.
- Net cash movement: **1,476,993,370,538 VND**.
- Opening cash/equivalents: **14,048,245,083,619 VND**.
- FX effect: **36,974,584,841 VND**.
- Closing cash/equivalents: **15,562,213,038,998 VND**.
- CAPEX: **(884,893,299,636 VND)**.
- Dividends paid: **(1,904,420,402,345 VND)**.

H1 flow sum and cash bridge residuals are 0 VND.

## Q2 standalone derivation
Q2 standalone is calculated as H1/YTD less the original Q1/2024 YTD report, on the same consolidated basis:
- CFO: **(185,410,216,861 VND)**.
- CFI: **(538,946,240,983 VND)**.
- CFF: **(813,834,130,954 VND)**.
- Net cash movement: **(1,538,190,588,798 VND)**.
- FX effect: **(6,386,239,463 VND)**.
- Opening cash: **17,106,789,867,259 VND** (Q1 close).
- Closing cash: **15,562,213,038,998 VND**.
- CAPEX: **(601,744,907,807 VND)**.
- Dividends paid: **(1,904,420,402,345 VND)**.

Q2 standalone flow sum and cash bridge residuals are 0 VND. H1 minus Q1 minus Q2 component differences are zero for CFO, CFI, CFF, net cash, FX, CAPEX and dividends. No plug is used.

## Closeout
- B01: **PASS**.
- B02: **PASS with corrected source-column mapping**.
- B03 H1/YTD: **PASS**.
- Q2 standalone cashflow: **PASS**.
- Full visual review: **COMPLETE**.
- All principal arithmetic bridges: **0 VND**.
- All source raw values remain in VND metadata; dashboard display values are in million VND.
- Negative cashflows and dividends remain negative; no values are balanced by inference.