# VDS Q1/2026 — trực quan xác minh B01/B02/B03

- Nguồn duy nhất: VietstockFinance document **543855**, BCTC hợp nhất Q1/2026.
- Danh mục: https://finance.vietstock.vn/VDS/tai-tai-lieu.htm?doctype=1
- PDF: https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/VDS_Baocaotaichinh_Q1_2026_Hopnhat.pdf
- Archive: `reports/raw/VDS/auto-vds-20261021/2720dd850acfbd95.pdf`.
- Đơn vị VND; B01 PDF pages 6–8 (printed pages 1–3), B02 PDF pages 11–13 (printed pages 6–8), B03 PDF pages 14–16 (printed pages 9–11). Các trang ảnh đã mở trực tiếp từ PDF gốc ngày 04/11/2026.

## B01 — PASS, residual 0 VND

- Current assets **6,417,238,249,041** + non-current assets **1,451,267,733,558** = total assets **7,868,505,982,599**.
- Current liabilities **4,831,645,599,511** + long-term liabilities **7,787,333,467** = total liabilities **4,839,432,932,978**.
- Equity **3,029,073,049,621**; liabilities + equity = total assets exactly.
- Cash and equivalents **858,161,024,619**.

## B02 — PASS, residual 0 VND

Q1 current-quarter column is also YTD:

- Operating revenue row20 **202,757,306,990**; identified components: FVTPL **-21,364,334,330**, HTM **14,427,123,290**, lending **118,422,852,421**, AFS **33,685,939,300**, brokerage **54,605,098,960**, custody **1,959,949,420**, financial advisory **414,090,909**, other operating income **606,587,020**. Row1.8 current Q1 cell is blank; **832,001,623** belongs to prior-year comparative only. Revenue component residual **0**.
- Operating expenses row40 **190,545,800,755**; row21 FVTPL **59,694,895,497**, row23 AFS reclassification loss **5,326,029,300**, row24 provisions **77,138,419,416**, row26 proprietary **917,509,818**, row27 brokerage **41,445,982,285**, row30 custody **2,143,640,576**, row31 financial advisory **3,260,790,859**, row32 other services **618,533,004**. Rows22 and29 are blank. Expense detail residual **0**.
- Financial income row50 **9,984,544,961**; financial expense row60 **12,726,612,033**, including interest **12,546,575,343**; admin expense row62 **45,505,054,316**.
- Operating result row70 **-36,035,615,153**; other income/result **545,454**; PBT **-36,035,069,699**.
- Current tax **7,851,910,907**; deferred tax benefit **-14,396,180,160**; total tax expense **-6,544,269,253**; PAT **-29,490,800,446**; parent PAT **-28,526,203,886**; NCI **-964,596,560**; EPS **-105**. PBT-tax=PAT and parent+NCI=PAT exactly.

## B03 — PASS, residual 0 VND

- CFO **248,423,817,918**; CFI **-270,538,392,551**; CFF **-116,700,000,000**; net cash change **-138,814,574,633**.
- Opening cash **996,975,599,252**; closing cash **858,161,024,619**. Flow sum and cash bridge residuals are both 0 VND.
- FX rows 102/104 are blank; retain null. Customer brokerage/trust-money cashflow section is separate and is not merged into company B03.

## Ratio and status

- ROA **-1.4755%**; ROE **-3.8498%**, using quarterly PAT / average opening-closing assets or equity × 4 × 100.
- All source values remain raw VND in provenance; normalized snapshot values are triệu VND. No balancing plug.
- Data snapshot commit: `a20cecd3fb726d6e379a925cac6abfa40e261690`.
- Status: `verified_manual_visual_reconciliation`. Q1/2026 is closed; do not re-extract or repeat visual review.

## Q2/2025 parent/NCI exception — investigation remains PENDING

- Supplemental original PDF pages 19–21 (printed pages 13–15) were inspected. Pages 19–20 are the B04 statement of changes in consolidated equity; page 21 begins the notes. They show aggregate equity movements but do not provide a quarter-specific parent/NCI attribution bridge that explains the **1,117,693,283 VND** shift.
- Preserve Q1/2025 original B02 parent/NCI values and Q2/2025 H1/YTD parent/NCI values unchanged. Q3/2025 YTD less Q3 standalone continues to reproduce the Q2 H1 allocation exactly. Do not backsolve, plug, or mark the allocation exception PASS.
- Next action: direct visual audit VDS Q2/2026 consolidated report, document ID **555653**, from the archived VietstockFinance ZIP `reports/raw/VDS/auto-vds-20261021/6ca61e80d55ffaac.zip`. Q2/2026 remains visual PENDING; do not re-run OCR or alter already source-backed fields.
