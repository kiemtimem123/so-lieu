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

- Latest checked branch HEAD before this note update: `9fd6e960b2505ce07b2ff4379bae5a5cdf8d297d`.
- Live queue checkpoint: `updatedAt=2026-10-25T21:31:22Z`, `lastCompletedSymbol=GEG`, `activeSymbol=null`, `resumeSymbolHint=null`. All 32 enabled symbols are marked complete in the checkpoint/configured completion set; there is no remaining active ticker in the current configured queue.
- **VCK is closed for automatic extraction**: `status=terminal_needs_manual_review`, `completeForAutomation=true`, `pendingCorePeriods=[]`, all seven periods from `2025-Q1` through `2026-Q3` are terminal manual-review periods, and `statementPagesPending=false`.
- All seven VCK quarter rows keep the matching VietstockFinance source document and source-scope blocker. Public financial fields are blank (no numeric financial metrics exposed); the extracted candidates remain in `scope_unverified_financial_values` for audit only. Front-end sanitizer hides metrics for any item with `scope_validation_required` or `manual_review_blocking_automatic_extraction`.
- VCK is configured to skip unresolved extraction through `2026-Q3` and automatically re-open when a quarter newer than `2026-Q3` is added. VCI has the equivalent skip-through rule through `2026-Q3`.
- Validations already passed after the UI/cache adjustments: [Validate Site and Data #970](https://github.com/kiemtimem123/so-lieu/actions/runs/40238559814), [Validate quarterly financial data #416](https://github.com/kiemtimem123/so-lieu/actions/runs/40235360954). These runs predate the current branch HEAD; a fresh site/data validation is being triggered by this note-only commit.
- The most recent OCR run checked was [#1614](https://github.com/kiemtimem123/so-lieu/actions/runs/40253954933), which succeeded and skipped processing because the current configured queue was already complete. Independent market/economic data sync failures are not VCK financial-report failures.
- On continuation, read only this note and `reports/processing-checkpoint.json`; load a ticker snapshot only if a new quarter is added or a validator identifies a concrete issue. Never make unverified VCK numbers visible or manufacture missing values.
