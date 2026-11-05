# GAS Q4/2024 — direct visual closeout

## Source
- VietstockFinance document ID: 490581.
- Consolidated Q4/2024 PDF: `reports/raw/GAS/auto-gas-20261021/7fa3b1653ff606d1.pdf`.
- Render artifact: workflow run 41787662520, artifact 13301557596.
- Directly reviewed PDF pages 4–7 (printed pages 1–4) at the saved render resolution.

## Visual validation
- B01 pages 4–5: PASS. Total assets 81,893,564,503,501 VND; total liabilities 20,322,569,237,871 VND; equity 61,570,995,265,630 VND. Assets = liabilities + equity exactly.
- B02 page 6: PASS. Net revenue 24,945,117,336,365 VND; PBT 2,558,297,020,087 VND; PAT 2,052,338,999,441 VND; parent PAT 2,044,102,438,055 VND; NCI PAT 8,236,561,386 VND; EPS 852 VND/share. Parent + NCI = PAT exactly.
- B03 page 7: PASS for the annual/YTD source values. CFO 8,705,303,886,462 VND; CFI 7,978,721,478,066 VND; CFF -16,711,006,239,817 VND; net cash movement -26,980,875,289 VND; beginning cash 5,668,895,214,949 VND; annual FX 7,569,091,808 VND; ending cash 5,649,483,431,468 VND. Annual flow sum and annual cash bridge reconcile to the source.

## Q4 standalone cashflow
Q4 standalone CFO/CFI/CFF/net movement were already derived from the original FY2024 YTD less original 9M/2024 YTD source:
- CFO 1,344,415,959,226 VND.
- CFI 5,520,432,980,286 VND.
- CFF -13,303,960,768,096 VND.
- Net cash movement -6,439,111,828,584 VND.
- Capex -568,193,423,765 VND.
- Dividends paid -12,971,054,206,100 VND.

These three cashflow components sum exactly to the reported standalone net movement. The standalone FX component is intentionally left null because the retained Q3/2024 original source sidecar does not provide a source-readable Q3 cumulative FX line. The large pre-FX cash bridge residual is therefore diagnostic only; no FX value is inferred and no plug is inserted.

## Cross-period exception
The Q1/2025 comparative opening B01 shows total assets/liabilities 38,683,095,343 VND lower than the original Q4/2024 report while equity is identical. Both source bases are retained separately; the Q4/2024 original values are not overwritten.

## Closeout
GAS Q4/2024 is now visually verified and closed for core automation. Remaining issue is terminal/manual: standalone Q4 FX cannot be independently sourced from the retained Q3/2024 sidecar, so the field stays null. No source values were invented or backsolved.
