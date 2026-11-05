# PLX Q1/2025 — cross-year cash basis reconciliation

## Scope and source set
- Company: Petrolimex (PLX), consolidated.
- Q1/2025 interim report: VietstockFinance document 504658, `reports/raw/PLX/auto-plx-20261021/8ebe33f1a2757507.pdf`.
- Q4/2024 interim report: `reports/raw/PLX/auto-plx-20261021/b80662485ac3e19f.pdf`.
- FY2024 audited consolidated report: `reports/raw/PLX/auto-plx-20261021/a264af3ddb771f63.pdf`. The PDF includes KPMG's independent audit report and states that the financial statements were approved for issue on 31 March 2025.
- The source archive remains inside the PLX VietstockFinance report archive. No figures from a third-party data provider were imported.

## Original discrepancy
The original Q4/2024 interim report records:
- B01 cash: 5,329,069,053,043 VND.
- B01 cash equivalents: 9,733,066,779,703 VND.
- B01 and B03 closing cash/equivalents: **15,062,135,832,746 VND**.

The Q1/2025 report records:
- B01 opening cash: 5,329,158,367,088 VND.
- B01 opening cash equivalents: 9,603,910,425,227 VND.
- B01 and B03 opening cash/equivalents: **14,933,068,792,315 VND**.

The total difference was **-129,067,040,431 VND** (-0.856897%). Both interim reports reconcile internally; therefore the difference was not treated as an OCR arithmetic error or corrected with a plug.

## Resolution from audited FY2024 report
Direct 300-DPI image review of the audited annual consolidated report confirms:

**B01 — physical PDF page 6 / printed page 5**
- Cash: 5,329,158,367,088 VND.
- Cash equivalents: 9,603,910,425,227 VND.
- Closing cash and cash equivalents at 31-Dec-2024: **14,933,068,792,315 VND**.

**B03 — physical PDF page 14 / printed page 13**
- Opening cash and cash equivalents: 14,048,245,083,619 VND.
- Net cash movement in FY2024: 883,159,652,074 VND.
- FX effect: 1,664,056,622 VND.
- Closing cash and cash equivalents at 31-Dec-2024: **14,933,068,792,315 VND**.

The audited annual B01 and B03 values match the Q1/2025 B01 opening and B03 opening **exactly**, to the VND.

The audited annual report's B01 cash components differ from Q4/2024 interim by:
- Cash: +89,314,045 VND.
- Cash equivalents: -129,156,354,476 VND.
- Total: -129,067,040,431 VND.

This establishes the proper cross-year continuity basis: the audited FY2024 report supersedes the earlier Q4/2024 interim balance for purposes of the 1-Jan-2025 opening amount. Keep both documents' original published values in their own provenance records. Do not overwrite the Q4 interim snapshot. The reviewed annual pages establish the final audited balance but do not provide a full line-by-line explanation of each adjustment from interim to audited; no additional transaction explanation is inferred.

## Direct visual evidence
- Audited FY2024 report: workflow run 42048402442, artifact 13426011034, 300 DPI, PDF pages 6 and 14.
- Q1/2025 report: workflow run 42047432084, artifact 13424607733, 300 DPI, PDF pages 2, 9 and 10.
- Q1 images directly confirm B01 opening amount and B03 opening/closing amount. Full Q1 B01/B02/B03 visual review remains pending; this audit closes only the cross-year cash-basis issue.

## Status and handling
- Cross-period Q4/2024-to-Q1/2025 cash basis: **EXPLAINED BY AUDITED FY2024 YEAR-END BASIS**.
- Q1/2025 B01 opening = Q1/2025 B03 opening = audited FY2024 B01 closing = audited FY2024 B03 closing = 14,933,068,792,315 VND.
- Q4/2024 interim original close 15,062,135,832,746 VND: preserved unchanged.
- No balancing plug or backsolved value inserted.
- Continue the remaining Q1/2025 source visual review, then proceed to PLX Q1/2026 and Q2/2026 manual checks.
