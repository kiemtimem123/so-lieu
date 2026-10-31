# Ghi chú tiếp nối phiên xử lý báo cáo tài chính

## Cách tiếp tục mà không nạp lại dữ liệu cũ

1. Đọc `reports/processing-checkpoint.json` và trạng thái GitHub Actions mới nhất trước tiên. Checkpoint là nguồn sự thật nếu ghi chú này cũ đi.
2. Chỉ đọc `data/financials-{SYMBOL}.json` và sidecar trong `reports/raw/{SYMBOL}/` của mã đang được chọn. Không quét mọi snapshot hoặc toàn bộ kho OCR.
3. Xử lý từng mã một; chỉ chuyển mã sau khi mã hiện tại đã lưu dữ liệu/checkpoint.
4. Theo yêu cầu người dùng, trường chưa xác minh phải để trống ở các chỉ tiêu hiển thị, đánh dấu rà soát thủ công và không dựng số để cân đối.
5. Nguồn duy nhất cho báo cáo: danh mục VietstockFinance `https://finance.vietstock.vn/{ticker}/tai-tai-lieu.htm?doctype=1` và PDF/ZIP được liên kết trực tiếp tại đó.

## Trạng thái checkpoint tại lần lưu gần nhất

- `updatedAt=2026-10-25T21:31:22Z`
- `lastCompletedSymbol=GEG`
- `activeSymbol=null`
- `resumeSymbolHint=null`
- Mã cuối cùng vừa hoàn tất: **GEG**, [workflow #1609](https://github.com/kiemtimem123/so-lieu/actions/runs/40235829479).
- Đã kiểm tra cấu hình: **32/32 mã đang bật đều `completeForAutomation=true`**; hiện không có mã chưa hoàn tất trong danh sách cấu hình. `resumeSymbolHint=null`, nên hiện tại không còn mã tiếp theo để chạy trong hàng đợi này. Không mở lại mã chỉ vì `manualReviewRemaining=true`; đó là các mục chờ người rà soát, không phải việc tự động còn pending.
- Để tiếp tục sau này, đọc checkpoint mới nhất; khi có một kỳ báo cáo mới hoặc có mã mới/chưa hoàn tất, chỉ mở snapshot/sidecar của mã tương ứng.

## Các mã có chính sách bỏ qua chưa xác minh

- VCB: dữ liệu chưa xác minh được đánh dấu thủ công đến Q2/2026.
- VCI: `skipUnconfirmedThroughPeriod=2026-Q3`.
- VCK: `skipUnconfirmedThroughPeriod=2026-Q3`. Cả 7 kỳ Q1/2025–Q3/2026 chưa xác minh được phạm vi hợp nhất. 174 giá trị OCR đã giữ trong `scope_unverified_financial_values.values` để kiểm toán, trong khi trường chỉ tiêu tài chính cấp trên là `null`; liên kết nguồn được giữ lại. VCI/VCK tự được đưa lại vào hàng đợi nếu có kỳ mới hơn Q3/2026.

## An toàn giao diện

- `assets/app.js` làm trống giá trị tài chính hiển thị ở hàng có `source_validation.scope_validation_required` hoặc `manual_review_blocking_automatic_extraction`, áp dụng cho biểu đồ, tổng quan, bảng và so sánh.
- Cache script trong `index.html`: `assets/app.js?v=financial-line-items-10-scope-review-1`.
- Giao diện ẩn số chưa xác minh: https://github.com/kiemtimem123/so-lieu/commit/59628ea946335cbfee5bb811bc7cee2b4f10b26b
- Giữ số VCK trong audit, ẩn khỏi trường tài chính: https://github.com/kiemtimem123/so-lieu/commit/78e98ad648876c14d4cf32bab59cfbdf31eca5a8
- Đóng checkpoint VCK cho rà soát thủ công: https://github.com/kiemtimem123/so-lieu/commit/4d3882f9ca46d7d6f46bd227ccbcd7f24f41891e
- Cache tag tương thích kiểm định: https://github.com/kiemtimem123/so-lieu/commit/2cc15e75b610cbedb2ca585f18fbac281a470413
- Validate Site and Data #966 đã thành công: https://github.com/kiemtimem123/so-lieu/actions/runs/40235725000

Ghi chú này là lối tắt tiếp nối, không thay thế checkpoint sống. Khi có công việc mới, đọc checkpoint và workflow mới nhất, rồi chỉ nạp dữ liệu của mã đang được chọn.

## 2026-10-26 final checkpoint review

- Branch HEAD at this review: `51fa14a5474de34a8209a6d0a91635e1c0284b13` (message: `Record final VCK manual-review closure and queue status`).
- Live queue checkpoint at review: `updatedAt=2026-10-25T21:31:22Z`, `lastCompletedSymbol=GEG`, `activeSymbol=null`, `resumeSymbolHint=null`. All 32 enabled symbols are marked complete in the current checkpoint; no ticker remains active.
- **VCK is closed for automatic extraction**: `status=terminal_needs_manual_review`, `completeForAutomation=true`, `pendingCorePeriods=[]`, all seven periods from `2025-Q1` through `2026-Q3` are terminal manual-review periods, and `statementPagesPending=false`.
- All seven VCK quarter rows keep the matching VietstockFinance source document and source-scope blocker. Public financial fields are blank (no numeric financial metrics exposed); the extracted candidates remain in `scope_unverified_financial_values` for audit only. Front-end sanitizer hides metrics for any item with `scope_validation_required` or `manual_review_blocking_automatic_extraction`.
- VCK is configured to skip unresolved extraction through `2026-Q3` and automatically re-open when a quarter newer than `2026-Q3` is added. VCI has the equivalent skip-through rule through `2026-Q3`.
- Latest validation for the VCK closure: [Validate Site and Data #971](https://github.com/kiemtimem123/so-lieu/actions/runs/40265424833) passed on the closure commit. The previous financial-data validation also passed: [#416](https://github.com/kiemtimem123/so-lieu/actions/runs/40235360954).
- The most recent OCR run checked was [#1614](https://github.com/kiemtimem123/so-lieu/actions/runs/40253954933), which succeeded and skipped processing because the current configured queue was already complete. Independent market/economic data sync failures are not VCK financial-report failures.
- On continuation, read only this note and `reports/processing-checkpoint.json`; load a ticker snapshot only if a new quarter is added or a validator identifies a concrete issue. Never make unverified VCK numbers visible or manufacture missing values.


## 2026-10-31 STB financial-table coverage checkpoint

- STB was reviewed from `data/financials-STB.json` only (10 quarters, 2024-Q1 through 2026-Q2). No OCR/enrich was run and no snapshot values were changed.
- Effective coverage after applying the current `rowsFor` allow-list and rejected-field rules: CĐKT 88/340; KQKD 70/220; LCTT 70/90; ROA/ROE 4/20. Use the banking-specific row keys in `assets/app.js`.
- Found and fixed a renderer issue: rows with `auto_extracted_pending_visual_review` could bypass rejected-field sanitization, allowing numeric OCR candidates listed in `financial_line_items_rejected_fields` to remain visible. The fast path now blanks rejected numeric metrics for every status; rejected keys also block direct values, aliases, and formula inputs in `resolveStatementValue`.
- Regression tests in `tests/test_financial_table_allowlist.mjs` use the STB snapshot fixture to verify rejected values at 2024-Q3, 2025-Q1 and 2025-Q4 are hidden while approved unrelated fields remain and the source snapshot is unchanged.
- Validation passed: [Validate Site and Data #41193103186](https://github.com/kiemtimem123/so-lieu/actions/runs/41193103186). Hostinger package passed: [#41193089231](https://github.com/kiemtimem123/so-lieu/actions/runs/41193089231). Packaging is not confirmation of live deployment.
- Cashflow holds and source anomalies remain unchanged: H1/2024 reclassification above 0.01%; Q3/2024 FX bridge residual ~2,000 million VND but less than 0.01% of closing cash; H1/2026 component-sum mismatch above 0.01%. Manual review remains for 2025-Q2, 2025-Q3 and 2026-Q2. No balancing plug.
- NCI remains source-backed only where an accepted field exists (Q1/2024 value 0); do not backfill other periods. ROA/ROE remain only Q2/2024 and Q4/2024; rejected Q1/2025 and Q4/2025 ratios stay hidden.
- **Next UI coverage ticker: VCB.** Read only the VCB snapshot, one ticker at a time. Preserve all existing holds and do not run OCR/enrich.
- Latest STB checkpoint commit: [`9df950a1f379889ed573496feba2d84afe465ee2`](https://github.com/kiemtimem123/so-lieu/commit/9df950a1f379889ed573496feba2d84afe465ee2).

- Cache busting: `index.html` now loads `assets/app.js?v=financial-line-items-20261031-v23` (was v22) so the rejected-field sanitizer is not masked by the browser cache. Commit: [`1e0a0875ea93c0097def824f0d554199a7d60b98`](https://github.com/kiemtimem123/so-lieu/commit/1e0a0875ea93c0097def824f0d554199a7d60b98).

## 2026-10-31 VCB staged financial-table coverage checkpoint

- **STB remains completed and preserved** in `uiCoverageHistory`; do not revisit or reload its already validated snapshot. STB's last completed UI stage and rejected-OCR display regression fix remain unchanged.
- **VCB completed stages (reuse, do not repeat):**
  1. Source-text reconciliation for 10/10 periods, 2024-Q1–2026-Q2, reused from existing checkpoint. Existing validator commit: `5b57b6cac94c42055415ea73b2298303686a4011`; source correction commits: `8c7d327e3996a862cadfab2b9be244ce5f9f3a3f`, `a285b735946f7f1bcd62e1dd203dbab3e7a648ce`, `ee68cf5d177e98a071dd60c97e51e935006020aa`, `97951b4e9ad79031c17aeeeb4c657283ca9063cc`, `2a40b3a19dc49451f1f1cdacf960135356302b91`.
  2. Source/scope inventory: all 10 period entries use the VietstockFinance document index `https://finance.vietstock.vn/VCB/tai-tai-lieu.htm?doctype=1`; report scope is consolidated; no scope blocker was found.
  3. Banking statement row mapping and direct-value coverage, from existing snapshot SHA `bcca9d7c9bd45d0bf753aae70c8d78b3cb4db581`:
     - CĐKT 171/340 (50.3%), 34 rows.
     - KQKD 200/220 (90.9%), 22 rows.
     - LCTT 54/90 (60.0%), 9 rows.
     - ROA/ROE 18/20 (90.0%), 2 direct rows.
     - Combined direct coverage 443/670 (66.1%). Formula-derived presentation cells are excluded from these coverage figures.
  4. Rejected-field/blank-cell review: rejected cash-flow metrics at 2024-Q2, 2024-Q4 and 2025-Q2 stay hidden; 2025-Q4 rejected tax-reconciliation fields stay blocked. Capex, dividends paid and FX effect remain blank without source values. Bank interest expense has no direct field in the 10 rows; the renderer may calculate it only when same-period interest income and net-interest-income inputs both exist.
- No OCR/enrich was run, no source PDF text reconciliation was repeated, and no numeric value in `data/financials-VCB.json` was changed.
- **Pending stage only:** visual PDF review for 10/10 periods. Q1/2025 opening cash is recorded as 430,614,185 million VND, while the Q4/2024 closing cash field is currently rejected/blank; inspect the existing archived Q1/2025 source page before changing either field. The browser PDF viewer refused the 14.95 MB PDF for exceeding its content-size limit, so no visual validation is claimed.
- Resume rule: continue only `visual_pdf_review` using existing archived VietstockFinance PDFs. Do not reload/reprocess completed VCB reconciliation, rerun OCR/enrich, or alter normalized values without an image-confirmed correction. Once a period is visually confirmed, save a period-level checkpoint immediately; move to CTG only after VCB's pending stage is resolved or explicitly held for manual review.
- VCB checkpoint commit: `50e80378f99d1c5b5ecd231e69932c449f55776e`.



## 2026-10-31 VCB Q4/2024–Q1/2025 deep source-text audit

- Continued **VCB only**; do not move to SHS until VCB is fully closed.
- Reused existing OCR/text sidecars; no OCR/enrich rerun and no numeric source values changed.
- Q4/2024 VietstockFinance-linked report (reports/raw/VCB/auto-vcb-20261021/842e77aefd580828.pdf), B02 pages 5–6, B03 pages 8–9, B04 pages 10–11:
  - B02 originally reports total assets 2,085,397,244; liabilities 1,886,441,134; equity 198,956,110 million VND.
  - B03 Q4 reports interest income 23,581,262; net interest income 13,842,332; pre-provision profit 10,670,350; provision expense 32,330; PBT 10,702,680; PAT 8,569,931; attributable profit 8,565,388 million VND.
  - B04 annual values: CFO 56,572,468; CFI -1,303,327; CFF -19,963; net cash change 55,249,178; opening cash 372,818,730; closing cash 428,067,908 million VND. The cash-flow component and opening-to-closing bridges reconcile exactly.
- Q1/2025 VietstockFinance-linked report (reports/raw/VCB/auto-vcb-20261021/f25bf036ad962541.pdf), B02 pages 4–5, B03 pages 7–8, B04 pages 9–10:
  - Q1 B02 comparative restates 31/12/2024 balance values to assets 2,085,873,522; liabilities 1,889,664,354; equity 196,209,168 million VND. Q4 snapshot retains this restated comparative basis and the equation reconciles exactly.
  - Q1 B04 confirms CFO -13,180,595; CFI -174,898; CFF 0; net cash change -13,355,493; opening cash 430,614,185; closing cash 417,258,692 million VND. Q1 cash bridge reconciles exactly.
- **Material unresolved cross-period gap:** Q4/2024 B04 closing cash 428,067,908 vs Q1/2025 B04 opening cash 430,614,185 = 2,546,277 million VND (0.594830% of Q4 closing cash), above the user's 0.01% tolerance. Both source-reported cash balance values remain in the rejected-value audit and hidden from display until the source explanatory note and visual PDF pages establish the reason. Do not invent an FX effect, overwrite either amount, or force continuity.
- Corrected a stale renderer block on Q4/2024: eight cash-flow movement fields (CFO/CFI/CFF/net cash change, quarterly and YTD) were removed from financial_line_items_rejected_fields because the existing B04 page text proves they reconcile to zero. Only cash_beginning and cash_ending remain blocked for the inter-period gap. Commit: [605edf6c4025aa4149d2ad46fc2a0d51ecd57b3a](https://github.com/kiemtimem123/so-lieu/commit/605edf6c4025aa4149d2ad46fc2a0d51ecd57b3a).
- Checkpoint commit: [3472732c2c54bee39a31a243e8cad910fc88be8d](https://github.com/kiemtimem123/so-lieu/commit/3472732c2c54bee39a31a243e8cad910fc88be8d).
- Visual page review remains pending for all 10 VCB periods. This audit is source-text/OCR reconciliation only; it is not visual PDF confirmation. Continue VCB only; do not start SHS until all pending VCB review stages are closed.

- Validation passed after the Q4/2024 cash-flow display correction: [Validate Site and Data #1644](https://github.com/kiemtimem123/so-lieu/actions/runs/41211937050). Passed cash-flow bridge reconciliation, financial-table source allow-list, JSON snapshot validation, and JavaScript syntax checks. Checkpoint metadata commit: [9f7df44bba249137551582868ab5d9146a64c6fb](https://github.com/kiemtimem123/so-lieu/commit/9f7df44bba249137551582868ab5d9146a64c6fb).


## 2026-10-31 VCB Q2/2024 và Q2/2025 đối chiếu sâu B03/B04

- Tiếp tục **VCB בלבד**; chưa chuyển sang mã tiếp theo.
- Chỉ tái sử dụng sidecar OCR đã có; **không chạy OCR/enrich lại** và không nạp lại dữ liệu 10 kỳ từ đầu.
- Q2/2024 — tài liệu VietstockFinance document ID `472851`, PDF `reports/raw/VCB/auto-vcb-20261021/725730719cacd00b.pdf`:
  - B03 PDF trang 7–8: thu nhập lãi thuần 13.907.711; lãi thuần dịch vụ 1.498.953; ngoại hối 1.160.895; mua bán chứng khoán kinh doanh -1.324; chứng khoán đầu tư 1.854; lãi thuần hoạt động khác 24.387; góp vốn/cổ phần 159.133; tổng thu nhập hoạt động 16.751.609; chi phí hoạt động -5.121.793; PPOP 11.629.816; chi phí dự phòng (1.513.541); LNTT 10.116.275; thuế 1.991.566; LNST 8.124.709; lợi nhuận thuộc cổ đông ngân hàng 8.119.414 triệu VND.
  - **Sửa dấu sai** `bank_provision_expense`: từ -1.513.541 sang +1.513.541. Với quy ước trường chi phí dương, 11.629.816 - 1.513.541 = 10.116.275.
  - B04 PDF trang 9–10: CFO YTD -43.570.203; CFI -360.765; CFF 0; net cash YTD -43.930.968; cash đầu kỳ 372.818.730; cash cuối kỳ 328.887.762. Dòng tiền riêng Q2 = YTD Q2 trừ YTD Q1: CFO 19.604.283; CFI -230.231; CFF 0; net cash 19.374.052. Cash bridge và các tổng đều khớp 0.
  - Xóa 10 cờ rejected cũ cho CFO/CFI/CFF/net cash (quý và YTD) cùng cash_beginning/cash_ending; số liệu nay được phép hiển thị.
- Q2/2025 — tài liệu VietstockFinance document ID `514224`, PDF `reports/raw/VCB/auto-vcb-20261021/789948b37004bdfc.pdf`:
  - B03 PDF trang 7–8: PPOP 11.843.505; chi phí dự phòng 809.590; LNTT 11.033.915; thuế 2.196.544; LNST 8.837.371; lợi nhuận thuộc cổ đông ngân hàng 8.831.885 triệu VND.
  - B04 PDF trang 9–10: CFO YTD 24.736.707; CFI -354.102; CFF 0; net cash YTD 24.382.605; cash đầu kỳ 430.614.185; cash cuối kỳ 454.996.790. Dòng tiền riêng Q2: CFO 37.917.302; CFI -179.204; CFF 0; net cash 37.738.098. Cash bridge và các tổng đều khớp 0.
  - Xóa 10 cờ rejected cũ giống Q2/2024 vì dữ liệu YTD/riêng quý và cash bridge khớp báo cáo.
- Không thay đổi các số liệu nguồn khác; hai kỳ vẫn ở trạng thái `auto_extracted_pending_visual_review`. Đối chiếu này là **source text/OCR only**, không phải xác minh ảnh PDF.
- Commit snapshot: [cbd2ee88543d1c93ff1a3293e1ec003c13bf0b18](https://github.com/kiemtimem123/so-lieu/commit/cbd2ee88543d1c93ff1a3293e1ec003c13bf0b18).
- Commit checkpoint: [476fa10abf0c8dfe191cdd8b86f6fa3402c948ae](https://github.com/kiemtimem123/so-lieu/commit/476fa10abf0c8dfe191cdd8b86f6fa3402c948ae).
- Validate Site and Data #1647: [run 41214877946](https://github.com/kiemtimem123/so-lieu/actions/runs/41214877946), success; đã qua cash-flow bridge, source allow-list, JSON snapshot và JavaScript checks.
- Package Hostinger Stock Dashboard #301: [run 41214877956](https://github.com/kiemtimem123/so-lieu/actions/runs/41214877956), success; đây là đóng gói artifact, không xác nhận đã upload/deploy lên Hostinger.
- **Kỳ mới cần kiểm tra:** các trang công khai báo hiệu VCB đã có BCTC hợp nhất Q3/2026 vào cuối tháng 10/2026, nhưng hiện chưa xác nhận được document ID/PDF trực tiếp từ danh mục VietstockFinance theo policy nguồn duy nhất. Không lấy số liệu từ 24HMoney/Vietcap hay bất kỳ nguồn trung gian để ghi vào snapshot; chờ xác minh link VietstockFinance.
- **Việc còn mở, chỉ tiếp tục VCB:** (1) giải thích chênh cash 2.546.277 triệu VND giữa Q4/2024 và đầu Q1/2025 bằng thuyết minh; (2) visual PDF review cho 10 kỳ đã lưu; (3) xác minh Q3/2026 từ danh mục VietstockFinance và PDF được liên kết. Không chuyển SHS trước khi đóng hoặc ghi trạng thái giữ thủ công minh bạch.


## 2026-10-31 VCB final source-text arithmetic pass

- Continued VCB only; no OCR/enrich rerun; reused the existing VietstockFinance PDF text sidecars.
- Q4/2025 B03 PDF page 7 shows the investment-securities net income row as a dash in the current-year Q4 column; the number 2,735 belongs to the prior-year comparative column. Corrected `bank_investment_securities_net` from 2,735 to 0. After correction, current-year revenue components sum to 19,172,495 and exactly match reported revenue; PPOP bridge also reconciles. Snapshot commit: [87306b7ec0858b6c074983f237fbbc65a72a969c](https://github.com/kiemtimem123/so-lieu/commit/87306b7ec0858b6c074983f237fbbc65a72a969c).
- Q2/2024 B04 pages 9–10: restored `cash_beginning=372,818,730`, `cash_ending=328,887,762` from report text; net cash YTD -43,930,968, bridge delta 0.
- Q2/2025 B04 pages 9–10: restored `cash_beginning=430,614,185`, `cash_ending=454,996,790`; net cash YTD 24,382,605, bridge delta 0.
- Snapshot commit for Q2 opening/closing balances: [e8b493569bba2636c6599dc2e0702f3b4cb4857c](https://github.com/kiemtimem123/so-lieu/commit/e8b493569bba2636c6599dc2e0702f3b4cb4857c).
- Full arithmetic recheck across all 10 stored periods (2024-Q1 to 2026-Q2): balance equation, revenue component sum, revenue-to-PPOP bridge, PPOP-to-PBT provision bridge, PBT-tax-to-PAT bridge, quarterly CFO+CFI+CFF, YTD CFO+CFI+CFF, and YTD opening-to-closing cash bridge all have zero difference, except Q4/2024 cash bridge is intentionally not calculated because both cash balance values remain hidden. All discrepancies checked are exact zero; there is no tolerance exception being used here.
- Latest snapshot blob SHA: `de81130194d8d0da5e1f909d7fae1251a531ad57`.
- Checkpoint commit: [8405e889e4afd72772c4907f15633b53e4d09f5b](https://github.com/kiemtimem123/so-lieu/commit/8405e889e4afd72772c4907f15633b53e4d09f5b).
- Pending: (1) Q4/2024 cash close 428,067,908 vs Q1/2025 cash opening 430,614,185, gap 2,546,277 million VND / 0.594830%, unresolved; keep both Q4 cash fields hidden; (2) visual PDF review remains pending for all 10 reports; (3) external report listings indicate VCB Q3/2026 has been posted, but the direct VietstockFinance catalog page is inaccessible in the current lookup and no direct catalog document ID/PDF has been verified; do not import secondary-source figures.
- VCB remains `terminal_needs_manual_review`, `manualReviewRemaining=true`, and automation is skipped. Do not move to SHS until these pending items are cleared or explicitly held as manual review.


## 2026-11-01 VCB audited Q4/2024 cash-flow restatement

- Reused the existing validated VCB snapshot and PDF sidecars; no OCR/enrich rerun and no reload of the 10 source periods.
- Resolved the apparent 2,546,277 million VND difference between preliminary Q4/2024 closing cash and Q1/2025 opening cash. The Q4 publication was superseded by audited 2024 consolidated statements; Q1/2025 comparative cash and audited annual closing cash both equal 430,614,185.
- Updated `data/financials-VCB.json` in commit `01a27a27c3cf6e45dbe14f7e0d681e4a35a24d6b`: restored cash opening/closing and revised annual YTD flows to audited values (CFO 59,122,831; CFI -1,307,413; CFF -19,963; net 57,795,455). Standalone Q4 values are derived from audited YTD less Q3 YTD (CFO 117,112,806; CFI -501,783; CFF -19,963; net 116,591,060). All three arithmetic bridges equal zero.
- Audited B04 annual report page 134–135 (embedded PDF page 68) was visually checked. This is partial visual verification only; full review of the 10 report PDFs and all other statement sections remains pending.
- Q3/2026 still must be confirmed by document ID and PDF directly from `https://finance.vietstock.vn/VCB/tai-tai-lieu.htm?doctype=1`. Do not import figures from 24HMoney or Vietcap.
- Next: continue VCB only; do not advance to SHS before the remaining direct visual review and Q3/2026 source confirmation are resolved.


## 2026-11-01 VCB bank-validator basis correction

- Found a validator logic defect: B04 opening/closing cash fields are year-to-date basis, but the bank reconciliation script compared them against standalone-quarter net cash change and treated annual opening cash as the quarter opening balance.
- Patched `scripts/validate-bank-reconciliation.py` in commit `3d4c01923c00096bd1095c98178ce76225f94fde`: YTD cash bridge now uses `net_cash_change_ytd`; Q2-Q4 continuity compares the movement between consecutive quarter-end cash balances with the standalone-quarter net flow; added source-backed VCB Q4/2024 regression values.
- The script content was re-fetched and the new logic/regression presence was checked. The full script has not yet been executed; do not claim test PASS until the repository validator runs.
- Continue VCB only. Remaining: runtime execution of validator; full visual review of all report PDFs/statement pages; direct VietstockFinance catalog verification for Q3/2026.


## 2026-11-01 VCB source-link correction

- Corrected the audited annual-report URL in the Q4/2024 source audit metadata to the verified Vietstock-hosted original: `https://static2.vietstock.vn/data/HOSE/2024/BCTN/VN/VCB_Baocaothuongnien_2024.pdf`.
- No financial values changed in this correction; the audited annual report values remain visually checked from B04 page 134–135.


## 2026-11-01 VCB Q2 cash-flow visibility and signed provision audit

- Removed stale rejection flags from the ten B04 cash/cash-flow fields in VCB 2024-Q2 and 2025-Q2 after their source-text reconciliation; both rows' YTD sum, standalone-quarter sum and cash bridge each equal zero. Snapshot commit `a3e79eb9de035efb1d5cc5dd19d18104fe2e3ca4`.
- Confirmed Q4/2024 `bank_provision_expense=-32,330` is a reversal/income; the validator must preserve the sign, so PPOP - (-32,330) = PBT. Q2/2024 provision expense remains +1,513,541. Patched signed provision logic and regressions in commit `46b683d1d2d9374961715a078a45fabb2705283d`.
- Re-audited all ten persisted VCB quarters (2024-Q1..2026-Q2) programmatically: balance, income composition, revenue/PPOP, PBT signed-provision bridge, PAT, quarter flow, YTD flow and YTD cash bridge all have zero absolute difference. This was a direct snapshot audit, not a runtime execution of the repository's full validator.
- Continue VCB only. Pending: execute the validator after its patches, finish visual review of all ten report PDFs and all statement sections, and verify VCB Q3/2026 from the direct VietstockFinance catalog before importing.


## 2026-11-01 VCB audited annual report visual evidence

- Visually checked the Vietstock-hosted 2024 Annual Report: B02 consolidated financial position (printed pp.130–131 / PDF index 66), B03 income statement (p.133 / index 67), B04 cash flow (pp.134–135 / index 68), and Note 35 cash and cash equivalents (p.184 / index 93).
- The Note 35 visual table confirms 31/12/2024 cash equivalents 430,614,185 = cash 14,268,064 + NHNN deposits 49,340,493 + TCTD deposits/loans up to 3 months 367,005,628.
- This is partial visual confirmation of the audited annual report only, not completion of visual review for all ten quarterly PDFs. Leave VCB in manual review.
- Current snapshot blob SHA: `d126e7771e6b9bdb5dabb4523215439c19aa3368`.


## 2026-11-01 Shared test regression isolated and fixed

- CI exposed that changing the shared `cash_bridge_delta` helper to YTD basis broke 45 cross-ticker tests. Corrected the scope in commit `2c9b357b157397ecd61dac5035b7748c53816ddc`: restored generic `cash_bridge_delta` standalone-period semantics and introduced `bank_cash_bridge_delta` for bank B04 YTD opening/closing balances only. Bank audit and VCB Q4 regression now use the bank-specific helper.
- Both `Validate quarterly financial data` and `Validate Site and Data` workflows were in progress on commit `2c9b357b157397ecd61dac5035b7748c53816ddc` at checkpoint time. Do not claim CI passed until both complete.
