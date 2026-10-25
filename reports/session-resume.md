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

## 2026-10-26 checkpoint refresh

- Latest checked branch HEAD: `2c8f7fc3594056ec37ba5c688b9d2038e1071218`.
- Live checkpoint: `updatedAt=2026-10-25T21:31:22Z`, `lastCompletedSymbol=GEG`, `activeSymbol=null`, `resumeSymbolHint=null`.
- All 32 enabled symbols in `config/securities.json` are already `completeForAutomation=true` or listed in the checkpoint's completed set; no next configured ticker remains in the current queue. The most recent completed OCR pass is [#1611](https://github.com/kiemtimem123/so-lieu/actions/runs/40236304580), success.
- Last completed symbol in checkpoint: `GEG`; period coverage: 2024-Q1–2026-Q2.
- The two explicit skip-through policies remain VCI and VCK through `2026-Q3`. Unverified figures remain blank in public fields; VCK values are preserved under audit metadata and hidden from the front-end whenever the source scope flag is set.
- Resume efficiently: read only this note, `reports/processing-checkpoint.json`, `config/securities.json`, and the latest workflow run list. Do not reopen historical ticker data unless a newer quarter appears, a new ticker is added, or validation reveals a specific issue.
