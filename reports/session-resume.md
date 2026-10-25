# Ghi chú tiếp nối phiên xử lý báo cáo tài chính

## Cách tiếp tục để không phải nạp lại dữ liệu cũ

1. Đọc `reports/processing-checkpoint.json` và trạng thái GitHub Actions mới nhất trước tiên. Checkpoint là nguồn sự thật nếu ghi chú này cũ đi.
2. Chỉ đọc snapshot `data/financials-{SYMBOL}.json` và các sidecar trong `reports/raw/{SYMBOL}/` của mã đang làm. Không quét tất cả snapshot hoặc toàn bộ kho OCR.
3. Xử lý từng mã một; chờ dữ liệu và checkpoint của mã hiện tại được commit rồi mới sang mã khác.
4. Theo yêu cầu người dùng, trường chưa xác minh phải để trống ở các chỉ tiêu đang hiển thị, đánh dấu rà soát thủ công và tiếp tục hàng đợi. Không suy diễn số liệu để cân đối.
5. Nguồn duy nhất cho báo cáo: danh mục VietstockFinance `https://finance.vietstock.vn/{ticker}/tai-tai-lieu.htm?doctype=1` và PDF/ZIP được liên kết trực tiếp tại đó.

## Trạng thái checkpoint mới nhất

- Checkpoint tại thời điểm đọc: `updatedAt=2026-10-25T21:30:24Z`; `lastCompletedSymbol=KBC`; `activeSymbol=null`; `resumeSymbolHint=GEG`.
- Mã hoàn tất gần nhất: **KBC**, workflow [run #1608](https://github.com/kiemtimem123/so-lieu/actions/runs/40235752348).
- Mã kế tiếp theo checkpoint: **GEG**. Kiểm tra Actions và checkpoint sống trước khi mở snapshot mã này.
- Lượt OCR #1608 xử lý KBC thành công và checkpoint chuyển tiếp từ IDC → KBC → GEG: https://github.com/kiemtimem123/so-lieu/actions/runs/40235752348
- Kiểm định giao diện gần nhất thành công: [Validate Site and Data #966](https://github.com/kiemtimem123/so-lieu/actions/runs/40235725000).

## Các mã đang bỏ qua để rà soát thủ công

- VCB: bỏ qua các giá trị chưa xác minh đến Q2/2026.
- VCI: `skipUnconfirmedThroughPeriod=2026-Q3`.
- VCK: `skipUnconfirmedThroughPeriod=2026-Q3`. Cả 7 kỳ Q1/2025–Q3/2026 chưa xác minh được phạm vi hợp nhất. Có 174 giá trị OCR được giữ trong `scope_unverified_financial_values.values` để kiểm toán; các trường chỉ tiêu tài chính cấp trên đã `null` để không hiển thị. Các liên kết nguồn và lý do rà soát vẫn được giữ nguyên. VCI/VCK tự mở lại khi có kỳ mới hơn Q3/2026.

## Quy tắc an toàn giao diện

- `assets/app.js` làm trống giá trị hiển thị của hàng có `source_validation.scope_validation_required` hoặc `manual_review_blocking_automatic_extraction`, áp dụng cho biểu đồ, tổng quan, bảng và so sánh.
- Phiên bản cache trong `index.html`: `assets/app.js?v=financial-line-items-10-scope-review-1`.
- Sửa giao diện scope chưa xác nhận: https://github.com/kiemtimem123/so-lieu/commit/59628ea946335cbfee5bb811bc7cee2b4f10b26b
- Giữ số VCK trong audit, ẩn khỏi trường tài chính: https://github.com/kiemtimem123/so-lieu/commit/78e98ad648876c14d4cf32bab59cfbdf31eca5a8
- Đóng checkpoint VCK để bỏ qua tự động: https://github.com/kiemtimem123/so-lieu/commit/4d3882f9ca46d7d6f46bd227ccbcd7f24f41891e
- Tên cache tương thích kiểm định: https://github.com/kiemtimem123/so-lieu/commit/2cc15e75b610cbedb2ca585f18fbac281a470413

Ghi chú này là lối tắt tiếp nối, không thay thế checkpoint sống. Lần sau chỉ đọc checkpoint, workflow mới nhất và snapshot/sidecar của đúng mã đang được chọn.
