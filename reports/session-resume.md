# Ghi chú tiếp nối phiên xử lý báo cáo tài chính

## Luôn làm theo cách này để tránh nạp lại toàn bộ dự án

1. Đọc `reports/processing-checkpoint.json` và trạng thái workflow Actions mới nhất trước tiên. Checkpoint là nguồn sự thật; các mốc tham chiếu ở dưới có thể cũ đi khi workflow vừa chạy xong.
2. Chỉ đọc `data/financials-{SYMBOL}.json` và sidecar thuộc `reports/raw/{SYMBOL}/` cho mã hiện tại. Không quét lại tất cả snapshot hay toàn bộ kho OCR.
3. Mỗi lượt xử lý một mã, lưu checkpoint/commit xong rồi mới chuyển mã khác. Nếu trường lõi chưa xác minh được, giữ trống, ghi trạng thái rà soát thủ công rồi tiếp tục hàng đợi.
4. Chỉ dùng danh mục tài liệu VietstockFinance `https://finance.vietstock.vn/{ticker}/tai-tai-lieu.htm?doctype=1` cùng PDF/ZIP liên kết tại đó. Không lấy số từ nguồn khác và không suy diễn để cân đối.

## Trạng thái gần nhất đã kiểm tra (2026-10-26)

- Checkpoint được cập nhật lúc `2026-10-25T21:27:17Z`: mã hoàn tất gần nhất là **GAS**, `activeSymbol=null`, `resumeSymbolHint=PLX`.
- Workflow #1605 xử lý GAS đã thành công: [run #1605](https://github.com/kiemtimem123/so-lieu/actions/runs/40235530380).
- Workflow #1606 đã chọn **PLX** và đang xử lý: [run #1606](https://github.com/kiemtimem123/so-lieu/actions/runs/40235585743). Trước khi thay đổi checkpoint hoặc sửa snapshot PLX, kiểm tra lượt này đã commit xong chưa.
- Các mã đã được đóng cho tự động xử lý do chỉ còn mục không xác minh: VCB đến Q2/2026; VCI đến Q3/2026; VCK đến Q3/2026. VCI/VCK sẽ tự được đưa lại vào hàng đợi khi snapshot có kỳ mới hơn mốc bỏ qua.
- **VCK:** cả 7 kỳ Q1/2025–Q3/2026 đều không xác nhận được phạm vi hợp nhất từ tiêu đề nguồn. Trong `data/financials-VCK.json`, 174 giá trị OCR đã được giữ trong `scope_unverified_financial_values.values`, còn các trường chỉ tiêu tài chính hiển thị ở cấp trên đã để `null`; liên kết nguồn không bị xóa. Checkpoint VCK là `terminal_needs_manual_review`, `completeForAutomation=true`, `skipUnconfirmedAutomation=true`, `skipUnconfirmedThroughPeriod=2026-Q3`.
- Frontend `assets/app.js` ẩn chỉ tiêu tài chính của các hàng có `source_validation.scope_validation_required` hoặc `manual_review_blocking_automatic_extraction`, nhưng giữ hàng nguồn/trạng thái để rà soát. Cache script trong `index.html` hiện là `assets/app.js?v=financial-line-items-10-scope-review-1`.
- Kiểm tra đã qua: [Validate Site and Data #964](https://github.com/kiemtimem123/so-lieu/actions/runs/40235420638) và [Validate quarterly financial data #416](https://github.com/kiemtimem123/so-lieu/actions/runs/40235360954).

## Các thay đổi liên quan

- [Ẩn số liệu tài chính khi phạm vi hợp nhất chưa xác nhận](https://github.com/kiemtimem123/so-lieu/commit/59628ea946335cbfee5bb811bc7cee2b4f10b26b).
- [Giữ lại giá trị VCK cho kiểm toán, không xuất ra trường chỉ tiêu](https://github.com/kiemtimem123/so-lieu/commit/78e98ad648876c14d4cf32bab59cfbdf31eca5a8).
- [Đóng kỳ VCK chờ rà soát thủ công trong checkpoint](https://github.com/kiemtimem123/so-lieu/commit/4d3882f9ca46d7d6f46bd227ccbcd7f24f41891e).
- [Sửa tên cache để kiểm định giao diện chấp nhận](https://github.com/kiemtimem123/so-lieu/commit/2cc15e75b610cbedb2ca585f18fbac281a470413).

Ghi chú này chỉ là lối tắt để tiếp tục. Trước khi làm việc, luôn đọc checkpoint và workflow mới nhất; không dựa vào con trỏ cũ và không nạp lại dữ liệu các mã đã hoàn tất.
