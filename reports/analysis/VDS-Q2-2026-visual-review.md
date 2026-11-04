# VDS Q2/2026 HN — direct visual audit and NCI movement follow-up

## 1. Scope and source

- Ticker: **VDS**.
- Report: consolidated interim financial statements for the six months ended 30 June 2026.
- VietstockFinance document ID: **555653**.
- Official document index: `https://finance.vietstock.vn/VDS/tai-tai-lieu.htm?doctype=1`.
- Source ZIP: `reports/raw/VDS/auto-vds-20261021/6ca61e80d55ffaac.zip`.
- Selected ZIP member: `VDS_Baocaotaichinh_Q2_2026_Hopnhat.pdf` (not the separate explanatory PDF `VDS_KQKD_Q2_2026.pdf`).
- Source archive SHA-256: `6ca61e80d55ffaac15c5524f96c927e7e57618c56f1b2cf09d0582109624fc1c`.
- Selected PDF SHA-256: `cf4351deb1e3c184ba11ff18f8c81ce15cc41e37070830f666dd48b33a7e471d`; 50 pages.
- Original PDF rendered at **300 DPI**. Main visual evidence: workflow runs **41882650570** and **41882681714**, artifacts **13348739177** and **13350071771**.
- Pages reviewed: B01 PDF pages 6–8 (printed 1–3); B02 11–13 (printed 6–8); B03 14–16 (printed 9–11); customer trust cashflow continuation 16–17 (printed 11–12); B04 page 18 (printed 13); further notes 19–30.

## 2. B01 — balance sheet PASS

Raw VND values read from the original pages:

| Item | 30-Jun-2026 | Residual |
|---|---:|---:|
| Current assets | 6,637,898,183,061 | |
| Non-current assets | 1,268,691,204,391 | |
| **Total assets** | **7,906,589,387,452** | **0** |
| Current liabilities | 4,888,996,386,336 | |
| Long-term liabilities | 3,117,886,013 | |
| **Total liabilities** | **4,892,114,272,349** | **0** |
| Equity | 3,014,475,115,103 | |
| **Liabilities + equity** | **7,906,589,387,452** | **0 vs assets** |

Selected source rows: cash and cash equivalents **801,617,758,652**; FVTPL **1,061,476,078,606**; HTM **20,000,000,000**; loans **4,289,666,502,091**; AFS **434,797,278,000**; receivables **36,737,345,980**; fixed assets **49,396,644,981**; retained earnings **363,368,457,472**.

## 3. B02 — income statement PASS

All values below are raw VND; Q2 standalone and H1/YTD columns are kept separate.

| Item | Q2/2026 standalone | H1/2026 YTD |
|---|---:|---:|
| Operating revenue | 262,152,978,583 | 458,846,424,238 |
| Operating expenses | 157,186,798,783 | 341,668,738,203 |
| Financial income | 5,473,235,995 | 15,457,780,956 |
| Financial expenses | 21,800,613,791 | 34,527,225,824 |
| Admin expenses | 45,931,870,444 | 91,436,924,760 |
| Selling expenses | blank | blank |
| Profit before tax | 42,712,405,506 | 6,677,335,807 |
| Income tax | 9,613,460,295 | 3,069,191,042 |
| **Profit after tax** | **33,098,945,211** | **3,608,144,765** |
| Attributable to parent | 36,516,641,493 | 8,131,939,292 |
| Attributable to NCI | (3,417,696,282) | (4,523,794,527) |
| EPS (VND/share) | **134** | **30** |

Checks:
- Revenue components on B02 page 11 add to reported row 20 exactly (residual 0).
- Operating expense components on B02 pages 11–12 add to row 40 exactly (residual 0).
- Q2 PBT less tax equals Q2 PAT exactly; parent PAT plus NCI PAT equals total PAT exactly.
- H1 PBT less tax equals H1 PAT exactly; H1 parent plus NCI equals H1 PAT exactly.
- B02 page 12 row 61 selling expense is blank; row 62 admin expense is **45,931,870,444 VND**. Earlier snapshot mistakenly copied admin expenses into selling expenses.
- B02 page 12 row 50 financial income is **5,473,235,995 VND**; prior snapshot incorrectly contained 0.
- B02 page 13 Q2 EPS is **134**, not the prior snapshot value 501.

## 4. B03 — company cashflows PASS

Raw VND, consolidated H1/YTD source basis:

| Item | H1/2026 YTD |
|---|---:|
| Operating cash flow | (2,620,903,680) |
| Investing cash flow | (90,786,936,920) |
| Financing cash flow | (101,950,000,000) |
| **Net cash movement** | **(195,357,840,600)** |
| Beginning cash and equivalents | 996,975,599,252 |
| Ending cash and equivalents | 801,617,758,652 |

All company cashflow checks have residual 0:
- CFO + CFI + CFF = reported net cash movement.
- Beginning cash + net movement = ending cash.
- Q2 standalone is calculated as H1/YTD less Q1/YTD on the same consolidated basis:
  - CFO **(251,044,721,598)**.
  - CFI **179,751,455,631**.
  - CFF **14,750,000,000**.
  - Net movement **(56,543,265,967)**.
  - Q2 standalone flows sum and cash bridge both have residual 0.
- Fixed-asset purchase line 61 H1/YTD is **(1,058,807,300 VND)**; Q1/2026 line 61 is **(1,035,060,800 VND)**, so Q2 standalone is **(23,746,500 VND)**.
- Dividend line 76 and FX lines 102/104 are blank; retain as **null**, not zero.

## 5. Customer / brokerage trust cashflows — PASS, kept separate

The separate section starts at PDF page 16 and continues on page 17. It is not part of the company's CFO/CFI/CFF or company cash equivalents.

Raw VND:
- Securities brokerage cash received **6,939,185,270,531**.
- Cash paid for securities purchases **(6,940,445,813,753)**.
- Customer deposit receipts **42,399,030,419,735**.
- Margin deposits at VSD (line 7.1) **6,297,304,983**.
- Customer settlement payments **(43,259,884,228,117)**.
- Issuer receipts **538,250,662,753**.
- Issuer payments **(537,546,805,140)**.
- Reported net movement **(855,113,189,008)**.
- Opening customer cash **1,748,126,020,118**.
- Closing customer cash **893,012,831,110**.

The trust-flow components, including the separately listed VSD margin line 7.1, reconcile to the reported net movement exactly; opening customer cash plus net movement equals closing customer cash exactly. Do not merge these amounts with the company's own cashflows.

## 6. B04 — arithmetic PASS; NCI transaction bridge PENDING

B04 equity rollforward:
- Opening total equity **3,099,129,510,066 VND**.
- Current-year increases **148,157,849,887 VND**.
- Current-year decreases **232,812,244,850 VND**.
- Closing total equity **3,014,475,115,103 VND**, matching B01 equity exactly.
- NCI opening **67,544,853,295 VND**; current-year decrease **11,038,190,794 VND**; closing NCI **56,506,662,501 VND**. Arithmetic residual 0.

The B04 main statement does not give the transaction detail behind the NCI decline. Compare the NCI line with B02 only as separately reported statements; do not create a balancing plug. The ownership note below provides a possible explanation for part of the Q1 movement, but does not yet supply the legal transaction value/bridge.

## 7. Ownership note cross-check — RVIF percentage changes between Q4/2025 and Q1/2026

Direct visual review of B05 pages:
- Q4/2025 HN: PDF page 21 / printed page 16 — VDAM **150bn/58%**; RVIF **70bn/85%** (prior direct visual audit).
- Q1/2026 HN: PDF page 21 / printed page 16 — VDAM **150bn/58%**; RVIF **70bn/95%**. Direct render: workflow run **41915850023**, artifact **13364946839**.
- Q2/2026 HN: PDF page 21 / printed page 16 for VDAM and page 22 / printed page 17 for RVIF — VDAM **150bn/58%**; RVIF **70bn/95%**. Direct render: workflow run **41915196166**, artifact **13363383855**.

What is established:
- VDAM stayed at **150bn capital / 58% VDS ownership** from Q4/2025 through Q2/2026.
- RVIF's reported ownership rose from **85% at 31-Dec-2025** to **95% at 31-Mar-2026**, and remained **95% at 30-Jun-2026**. RVIF fund capital remains **70bn VND**.
- Thus a 10-percentage-point ownership change at RVIF occurred after the 2025 year-end reporting date and by 31-Mar-2026. The notes identify a latest fund-license amendment date of 10-May-2024; that date is not sufficient evidence of the exact ownership transaction date.

## 8. Relating the ownership change to B04 NCI movements — hypothesis, not a closed reconciliation

B04 direct values:
- Q1/2026 NCI: opening **67,544,853,295**; decrease **7,825,738,340**; closing **59,719,114,955 VND**.
- Q2/2026 B04 H1 cumulative NCI decrease **11,038,190,794 VND**, closing **56,506,662,501 VND**.
- Q2 incremental B04 decrease after Q1: **3,212,452,454 VND**.

B02:
- Q1/2026 original NCI PAT **(964,596,560 VND)**.
- Q2/2026 standalone NCI PAT **(3,417,696,282 VND)**.
- H1/2026 YTD NCI PAT **(4,523,794,527 VND)**.

Observations:
- Q1 B04 NCI decrease less Q1 original B02 NCI PAT = **6,861,141,780 VND** of additional NCI decrease.
- Q2 incremental B04 NCI decrease differs from Q2 standalone NCI PAT by **+205,243,828 VND**.
- H1 B04 NCI decrease less H1 B02 NCI PAT = **6,514,396,267 VND**.

The RVIF change from 85% to 95% is directionally consistent with a transfer of part of RVIF's net assets from NCI to the controlling shareholder; it is a plausible explanation for a portion of the Q1 B04 reduction. However, the reviewed B05 does not specify the purchase/transfer instrument, purchase consideration, transaction date or carrying-value adjustment. Do not equate 10% of the stated 70bn fund capital with the B04 adjustment, and do not claim this fully reconciles the 6.861bn/6.514bn differences. Keep the NCI transaction bridge **PENDING** until a transaction disclosure or reconciliation schedule is found.

## 9. Separate B02 Q1/H1 attribution issue for 2026 — PENDING

Q1/2026 original B02 and Q2/2026 H1/YTD less Q2 standalone have the same total PAT but differ in parent/NCI allocation:
- Q1 original: parent **(28,526,203,886)**; NCI **(964,596,560)**; total **(29,490,800,446)**.
- Q1 implied by H1 less Q2: parent **(28,384,702,201)**; NCI **(1,106,098,245)**; total **(29,490,800,446)**.
- Allocation difference: **141,501,685 VND** (parent higher and NCI lower in the Q1 original than the implied split); total PAT residual 0.

Preserve original Q1 and H1/YTD source columns; no backsolve, no plug, no overwrite. This 2026 allocation difference is distinct from the 2025 Q1/H1 difference of 1,117,693,283 VND.

## 10. Data corrections made after visual audit

The Q2/2026 snapshot was updated at million-VND precision from the PDF images:
- B01 assets, liabilities, equity and sub-totals.
- B02 quarterly PAT, parent-attributable PAT, NCI PAT, tax, revenue/expense rows and EPS.
- EPS corrected from 501 to **134**.
- Financial income corrected from 0 to **5,473.235995 million VND**.
- Selling expense changed from 45,932 to **null** because B02 row 61 is blank; admin expense set to **45,931.870444 million VND**.
- Dividend line 76 retained as **null**; FX lines blank retained as **null**.
- B03 company cashflow fields set to exact values; customer trust cashflows stored in a separate audit object.

No raw-source values were altered. No balancing plug was inserted. Snapshot file: `data/financials-VDS.json`; data commit **2f7cb0216fb9b356c1c54e4d51bd0cd3a045a18f**.
