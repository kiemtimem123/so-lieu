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
- Allocation difference: **141,501,685 VND** in opposite directions: Q1 original parent PAT is **141,501,685 VND lower (more negative)** than implied; Q1 original NCI PAT is **141,501,685 VND higher (less negative)** than implied. Total PAT residual 0.

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


## 11. Q1/Q2 2026 NCI movements and RVIF ownership change — classification remains PENDING

### 11.1. Direct B04 comparison

The Q1/2026 consolidated report (VietstockFinance document **543855**, B04 PDF page 18 / printed page 13) and Q2/2026 consolidated report (document **555653**, B04 PDF page 18 / printed page 13) show:

| B04 NCI line | Q1/2026 | H1/2026 cumulative | Q2 increment |
|---|---:|---:|---:|
| Opening NCI at 1-Jan-2026 | 67,544,853,295 | 67,544,853,295 | |
| Decrease in reporting period | (7,825,738,340) | (11,038,190,794) | (3,212,452,454) |
| Closing NCI | 59,719,114,955 | 56,506,662,501 | |

All three B04 movements reconcile arithmetically to the stated closing balances. Q2 increment is H1 cumulative decrease less Q1 decrease; no plug is inserted.

B02 NCI profit/(loss) allocations:
- Q1/2026 standalone: **(964,596,560 VND)**.
- Q2/2026 standalone: **(3,417,696,282 VND)**.
- H1/2026 YTD: **(4,523,794,527 VND)**.

Comparison of the B04 movement and B02 NCI PAT leaves:
- Q1: B04 NCI decrease less Q1 NCI PAT = **6,861,141,780 VND** additional NCI decrease outside the B02 NCI PAT line.
- Q2 increment: B04 decrease less Q2 NCI PAT = **(205,243,828 VND)**, meaning Q2 B04 decrease is 205,243,828 VND smaller than the Q2 NCI loss.
- H1 cumulative: B04 decrease less H1 NCI PAT = **6,514,396,267 VND**.

These are cross-statement differences, not automatic arithmetic errors. A transaction/equity bridge is still required before classifying them.

### 11.2. B05 ownership comparison — RVIF 85% to 95%

Direct visual B05 comparison:
- Q4/2025 (31-Dec-2025): RVIF fund capital **70bn VND**, VDS ownership **85%**.
- Q1/2026 (31-Mar-2026), PDF page 21 / printed page 16: RVIF fund capital **70bn VND**, VDS ownership **95%**. Q1 visual render workflow run **41915850023**, artifact **13364946839**.
- Q2/2026 (30-Jun-2026), PDF page 22 / printed page 17: RVIF fund capital **70bn VND**, VDS ownership **95%**. Q2 visual render workflow run **41915196166**, artifact **13363383855**.
- VDAM remained **150bn VND / 58%** from Q4/2025 through Q2/2026; the RVIF ownership percentage is the ownership note that changed.

Thus the reported RVIF ownership percentage increased by 10 percentage points sometime after 31-Dec-2025 and no later than 31-Mar-2026. This aligns directionally with a reduction in NCI reported in Q1/2026, but the reviewed B04/B05 pages do not disclose the acquisition/transfer agreement, consideration, exact effective date, fund NAV/carrying-value adjustment, or other complete transaction bridge.

Do not multiply the 10 percentage points by the 70bn stated fund capital and treat the 7bn arithmetic result as the amount recorded in B04. Stated fund capital is not established by these pages as the carrying value/NAV of the transferred interest. The B04 NCI reduction of 7,825,738,340 VND and the post-B02 Q1 difference of 6,861,141,780 VND are therefore not yet reconciled to the ownership change.

**Classification: PENDING — probable ownership-change lead, not a source-supported amount reconciliation.** Keep this separate from the FY2025 VDAM capital increase/NCI 21bn, which is closed PASS.

### 11.3. Separate B02 Q1/H1 2026 allocation inconsistency

Q1/2026 original B02:
- Parent PAT **(28,526,203,886 VND)**.
- NCI PAT **(964,596,560 VND)**.
- Total PAT **(29,490,800,446 VND)**.

Q1 implied by H1 YTD less Q2 standalone:
- Parent PAT **(28,384,702,201 VND)**.
- NCI PAT **(1,106,098,245 VND)**.
- Total PAT **(29,490,800,446 VND)**.

The split differs by **141,501,685 VND** in opposite directions: original Q1 parent is 141,501,685 VND more negative; original Q1 NCI is 141,501,685 VND less negative. Consolidated PAT agrees exactly.

Keep the original Q1 and H1/YTD values as separately published. Do not backsolve, insert a plug, or claim the RVIF percentage movement explains this exact 141.5m difference without a transaction schedule. This is a second, independent PENDING allocation issue, distinct from the 2025 difference of 1,117,693,283 VND.

## 12. Audit status

- B01: **PASS** — assets, liabilities, equity and subtotals reconcile exactly.
- B02: **PASS** — revenue/expense detail, tax bridge, PAT and parent/NCI bridge reconcile for both Q2 standalone and H1 YTD; corrected EPS/financial income/selling-expense mapping.
- B03: **PASS** — company cashflows and cash bridge reconcile exactly; customer trust cashflows are separately reconciled and are not mixed with company cash.
- B04: **PASS arithmetic; PENDING transaction classification** for H1 NCI decrease 11,038,190,794 VND.
- B05: **PASS as reported ownership data**; RVIF moved from 85% at FY2025 year-end to 95% by Q1/2026. The nature/value of the transaction and bridge to B04 remain pending.
- B02 Q1/H1 2026 attribution: **PENDING 141,501,685 VND**; preserve source columns.
- B02 Q1/H1 2025 attribution: separate PENDING **1,117,693,283 VND**; no overwrite.


## 13. Further note pages 31–50 — no disclosed NCI transaction bridge located

The correct Q2/2026 consolidated PDF member was rendered at 300 DPI for PDF pages **31–50**:
- VietstockFinance document **555653**; source ZIP `reports/raw/VDS/auto-vds-20261021/6ca61e80d55ffaac.zip`.
- Workflow run **41917120909**, artifact **13364129604**, rendered pages 31–50. This artifact used the exact Q2 HN PDF member `VDS_Baocaotaichinh_Q2_2026_Hopnhat.pdf`.
- A prior page-31–50 render run **41916876255**, artifact **13364847422**, is excluded: the workflow fallback pointed to the Q1/2026 PDF, so it is not Q2 evidence.

Findings from the correct Q2 pages:
1. **Note 10 — long-term other investments** (PDF page 36 / printed page 31) includes the row “Quỹ Đầu tư Thịnh vượng Rồng Việt (RVIF)”:
   - 30-Jun-2026: **47,854,800,000 VND**.
   - 1-Jan-2026: **49,497,795,000 VND**.
   - Decrease: **1,642,995,000 VND**.
   
   This is a reported carrying amount within the “other long-term investments” table. The note pages do not state that this movement is the consideration for the 10-percentage-point change in the RVIF ownership ratio; do not equate the 1.643bn decrease to the B04 NCI reduction or use it as a balancing amount.

2. **Note 21.3 — equity** (PDF page 41 / printed page 36) reports:
   - NCI at 1-Jan-2026: **67,544,853,295 VND**.
   - NCI at 30-Jun-2026: **56,506,662,501 VND**.
   - This repeats the B04 balance movement; no additional transaction breakdown is provided on the note page.
   - The same note shows total equity 3,099,129,510,066 VND opening and 3,014,475,115,103 VND closing, matching B01/B04. Retained earnings total 358,592,121,913 VND opening and 363,368,457,472 VND closing; realized/unrealized components are presented separately.

3. **Note 31 — related parties** (PDF page 49 / printed page 44) lists the counterparties and material transactions disclosed there. RVIF is not identified as a counterparty in the listed material related-party transactions. This is not a complete certificate that no ownership transfer occurred; it only describes the related-party table disclosed on that page.

4. **Note 33 — events after the reporting period** (PDF page 50 / printed page 45) states that there were no material events after the reporting date requiring adjustment or disclosure. This does not identify the RVIF ownership transaction during H1/2026.

5. **Note 30 — supplementary information for changes in equity** (PDF page 48 / printed page 43) explains other comprehensive income/equity changes related to financial-asset revaluation; it does not contain a quantified NCI ownership transaction bridge.

Conclusion after reviewing B05 and all note pages 19–50:
- RVIF's disclosed ownership ratio is **85% at FY2025 year-end** and **95% at Q1 and Q2/2026**; fund capital is 70bn VND throughout.
- B04 H1 NCI decrease is **11,038,190,794 VND**. B02 H1 NCI loss is **4,523,794,527 VND**. The residual is **6,514,396,267 VND** and remains unexplained.
- Note 10 RVIF investment carrying amount decreases by **1,642,995,000 VND**, but the note does not tie this to the 10-percentage-point change or B04.
- No contract, transaction date, consideration, NAV/carrying-value bridge, or quantified acquisition/transfer schedule was identified in the reviewed B05/Notes 19–50.
- **NCI transaction explanation remains PENDING.** Retain the RVIF ownership change and Note 10 movement as two independent source-supported clues; do not infer the amount, date, instrument or counterparty from them.


## 14. Note 10 RVIF carrying value — additional clue, not transaction consideration

The same Note 10 table, “Đầu tư dài hạn khác”, was directly reviewed in the Q1/2026 and Q2/2026 consolidated reports:

| Period-end | Reported RVIF investment amount | Change from previous point |
|---|---:|---:|
| 31-Dec-2025 (opening balance shown in Q1/Q2) | 49,497,795,000 VND | |
| 31-Mar-2026 (Q1 Note 10) | 49,198,275,000 VND | (299,520,000) VND |
| 30-Jun-2026 (Q2 Note 10) | 47,854,800,000 VND | (1,343,475,000) VND |

Source pages:
- Q1/2026: PDF page **36** / printed page **31**, original PDF `reports/raw/VDS/auto-vds-20261021/2720dd850acfbd95.pdf`; 300-DPI render run **41917726858**, artifact **13365821105**.
- Q2/2026: PDF page **36** / printed page **31**, original selected HN PDF inside `reports/raw/VDS/auto-vds-20261021/6ca61e80d55ffaac.zip`; 300-DPI render run **41917120909**, artifact **13364129604**.

The amount is presented within “other long-term investments” as “Quỹ Đầu tư Thịnh vượng Rồng Việt (RVIF)”. The Q2 table also contains other investments that were no longer present at period end, so this table is a carrying-value schedule and not a statement of the fund's full NAV or a transaction agreement.

Interpretation limit:
- The reported RVIF investment amount declines by **299,520,000 VND** in Q1 and a further **1,343,475,000 VND** in Q2.
- These changes do not equal the 10-percentage-point ownership increase, the B04 NCI movement, or the B04-less-B02 residual.
- The note does not say whether the changes represent fair-value movements, transfers, redemptions, capital contributions, or another carrying-value event specific to the ownership change.
- Do not treat the 47.8548bn carrying value as the NAV of the fund, the price paid for the 10% stake, or the balance-sheet amount derecognized from NCI.

This provides a further cross-reference for the pending RVIF ownership-change investigation, but **does not close** the B04 NCI bridge. The supported conclusion remains: reported ownership moved from 85% at FY2025 year-end to 95% by Q1/2026; the amount and accounting mechanics of the transfer remain undisclosed in the reviewed pages.


## 15. Conflict in FY2025 Annual Report B05 — RVIF ownership percentage not yet resolved

A new primary-document contradiction was found and must be kept explicit:

| Source | Report date | RVIF capital | VDS ownership shown | Evidence mode |
|---|---|---:|---:|---|
| VDS Annual Report 2024, B05 / fund disclosure | 31-Dec-2024 | 70bn VND | **85%** | Vietstock-hosted official annual-report text |
| Q4/2025 HN B05 | 31-Dec-2025 | 70bn VND | **85%** | Direct image, PDF page 21 / printed page 16, 300 DPI |
| VDS Annual Report 2025, audited HN B05 text | 31-Dec-2025 | 70bn VND | **58%** | Extracted PDF table text; screenshot could not be fetched (cache miss), so not visually confirmed |
| Q1/2026 HN B05 | 31-Mar-2026 | 70bn VND | **95%** | Direct image, PDF page 21 / printed page 16, 300 DPI |
| Q2/2026 HN B05 | 30-Jun-2026 | 70bn VND | **95%** | Direct image, PDF page 22 / printed page 17, 300 DPI |

The FY2025 Annual Report PDF is the Vietstock-hosted file:
`https://static2.vietstock.vn/vietstock/2026/3/20/20260320___vds___bao_cao_thuong_nien_nam_2025.pdf`.
The extracted B05 table says VDAM direct ownership 58% and RVIF direct ownership 58%; it also says RVIF license amendment date 10-May-2024. PDF text lines 11319–11345 identify the entities, the 58% table entries and fund license date. The PDF screenshot service returned a cache miss for the attempted page screenshots, so the 58% entry is recorded as **text-extracted, not image-verified**. The report's management section separately states VDAM ownership 58%, RVIF NAV 93bn VND at FY2025 year-end; it does not independently state RVIF ownership percentage in that narrative.

By contrast, the Q4/2025 interim consolidated B05 image directly reviewed from the original VietstockFinance PDF clearly shows RVIF ownership **85%**. Q1/Q2 2026 B05 images directly show **95%**. The 2024 Annual Report also disclosed 85%. These are incompatible at the 31-Dec-2025 reporting date.

Do not silently decide that the Annual Report's 58% is a typographical error, even though it repeats VDAM's 58% in the adjacent B05 row and is inconsistent with the Q4/2025 interim B05. Equally, do not accept the 58% as correct without resolving the Q4 B05 contradiction. There is no verified correction/erratum identified in the documents reviewed.

### Revised conclusion for the RVIF/NCI hypothesis

- The previously described sequence “85% at FY2025 year-end → 95% by Q1/2026” is **not confirmed across all primary documents**.
- The supported finding is: Q4/2025 interim B05 image shows 85%; FY2025 Annual Report audited B05 text extraction shows 58% (not visually checked); Q1/Q2 2026 B05 images show 95%.
- Therefore, the exact change in RVIF ownership percentage, its effective date and the proportion of the H1/2026 NCI reduction attributable to that change remain **PENDING**.
- Do not use 10% of RVIF capital (7bn VND), 42% of NAV, Note10 carrying values, or the 6.861bn/6.514bn B04/B02 residuals as an inferred transfer consideration or plug.
- Note10 “other long-term investments” amounts remain separate carrying-value observations: opening FY2026 **49,497,795,000 VND**, Q1 **49,198,275,000 VND**, Q2 **47,854,800,000 VND**. These changes do not identify the ownership transaction or equal the B04 NCI movement.
- B04 arithmetic remains PASS; the transaction/classification bridge remains PENDING. The 2025 VDAM 50bn capital increase and NCI 21bn is a distinct closed case and is not affected by this RVIF ownership conflict.

Next evidence needed to close the conflict: an image-verified Annual Report B05 page or official corrected Annual Report, plus any RVIF ownership/transaction documentation and the accounting bridge from the transaction to the B04 NCI movement.


## 16. Verification of Annual Report B05 page image

A temporary verification step was initiated to retrieve the exact Vietstock-hosted FY2025 Annual Report PDF and render the B05 page containing RVIF at 300 DPI. The purpose is to determine whether the audited Annual Report page image itself shows 58% or whether the extracted PDF table text is wrong. No new ownership conclusion is made until the original page image is reviewed.
