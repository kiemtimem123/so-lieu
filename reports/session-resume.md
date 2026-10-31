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
