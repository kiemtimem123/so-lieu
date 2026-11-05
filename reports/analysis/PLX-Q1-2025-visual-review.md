# PLX Q1/2025 — full B01/B02/B03 visual review

## Source and render evidence
- VietstockFinance document ID: **504658**.
- Consolidated Q1/2025 PDF: `reports/raw/PLX/auto-plx-20261021/8ebe33f1a2757507.pdf`.
- Original catalog: `https://finance.vietstock.vn/PLX/tai-tai-lieu.htm?doctype=1`.
- Visual review: **300 DPI**, B01 PDF pages 2–5, B02 pages 6–7, B03 pages 8–10.
- The images came from two successful source-render workflows:
  - Run **42047432084**, artifact **13424607733**: pages 2, 9 and 10.
  - Run **42051131868**, artifact **13425833571**: pages 3–8.

## B01 — PASS
Visually reviewed B01 pages 2–5:
- Total assets: **80,035,874,441,574 VND**.
- Total liabilities: **50,515,699,095,191 VND**.
- Equity: **29,520,175,346,383 VND**.
- Liabilities + equity = total assets exactly.

B01 page 2 opening cash composition was directly confirmed:
- Opening cash: **5,329,158,367,088 VND**.
- Opening cash equivalents: **9,603,910,425,227 VND**.
- Total: **14,933,068,792,315 VND**.

## B02 — PASS
Visually reviewed B02 pages 6–7:
- Gross sales revenue: **67,890,171,339,647 VND**.
- Revenue deductions: **29,140,851,991 VND**.
- Net revenue: **67,861,030,487,656 VND**.
- Cost of goods sold: **64,149,128,072,879 VND**.
- Gross profit: **3,711,902,414,777 VND**.
- Financial income: **421,762,522,293 VND**.
- Financial expense: **293,602,592,566 VND**.
- Selling expenses: **3,353,223,304,063 VND**.
- Administrative expenses: **263,607,670,164 VND**.
- Operating profit: **337,522,026,628 VND**.
- Other income: **30,163,478,827 VND**.
- Other expenses: **9,301,853,896 VND**.
- Other profit: **20,861,624,931 VND**.
- Profit before tax: **358,383,651,559 VND**.
- Current income tax: **101,717,149,134 VND**.
- Deferred income tax: **45,897,701,886 VND**.
- Profit after tax: **210,768,800,539 VND**.
- Parent-attributable profit: **133,414,809,920 VND**.
- NCI profit: **77,353,990,619 VND**.
- Basic EPS: **86 VND/share**.

The net revenue, gross-profit, operating-profit, other-profit, PBT/tax/PAT and parent/NCI bridges agree with the original report values.

## B03 — PASS
Visually reviewed B03 pages 8–10:
- CFO: **(2,549,784,370,445) VND**.
- CFI: **(4,577,483,497,115) VND**.
- CFF: **2,647,070,139,831 VND**.
- Net cash movement: **(4,480,197,727,729) VND**.
- Opening cash/equivalents: **14,933,068,792,315 VND**.
- FX effect: **(6,137,487,794) VND**.
- Closing cash/equivalents: **10,446,733,576,792 VND**.

The cashflow component sum and cash opening-to-closing bridge pass within the project's 0.01% tolerance. No balancing plug was inserted. Cashflow values remain in VND in source metadata and in million VND in the display snapshot.

## Cross-year cash basis — resolved by audited FY2024
The earlier Q4/2024 interim report recorded closing cash/equivalents of **15,062,135,832,746 VND**. The separately archived audited FY2024 consolidated report records B01 and B03 closing cash/equivalents of **14,933,068,792,315 VND**, confirmed directly on PDF pages 6 and 14 at 300 DPI. That audited closing value matches the Q1/2025 B01 and B03 opening value exactly.

Therefore:
- Q1/2025 is reconciled to the **audited FY2024 year-end basis**.
- The original Q4/2024 interim value remains preserved in its own period record.
- No original Q4 interim value is overwritten; no plug or backsolve is used.
- The audited annual pages establish the final audited cash amount; the review does not infer a more detailed adjustment journal than the disclosed statements provide.

See `reports/analysis/PLX-Q1-2025-cash-basis-reconciliation.md` for the standalone cross-year bridge.

## Closeout
- B01: **PASS**.
- B02: **PASS**.
- B03: **PASS**.
- Full visual review of the Q1/2025 core financial statements: **COMPLETE**.
- Cross-year cash basis: **EXPLAINED BY AUDITED FY2024 YEAR-END BASIS**.
- No source values were overwritten and no balancing plug was inserted.
