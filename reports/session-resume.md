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
