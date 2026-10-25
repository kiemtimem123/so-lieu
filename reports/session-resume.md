# Ghi chú tiếp nối phiên xử lý báo cáo tài chính

## Cách tiếp tục mà không nạp lại dữ liệu cũ

1. Đọc `reports/processing-checkpoint.json` và trạng thái GitHub Actions mới nhất trước tiên. Checkpoint là nguồn sự thật; nếu mốc trong ghi chú cũ đi, ưu tiên checkpoint sống.
2. Chỉ đọc `data/financials-{SYMBOL}.json` và sidecar thuộc `reports/raw/{SYMBOL}/` của mã hiện tại. Không nạp lại tất cả snapshot hay kho OCR.
3. Xử lý từng mã một; chỉ chuyển mã khi dữ liệu/checkpoint của mã hiện tại đã được commit.
4. Theo yêu cầu người dùng: kỳ chưa xác minh thì để trống chỉ tiêu tài chính đang hiển thị, đánh dấu chờ rà soát thủ công và tiếp tục hàng đợi. Không suy đoán số để cân đối.
5. Nguồn duy nhất cho báo cáo tài chính là danh mục VietstockFinance `https://finance.vietstock.vn/{ticker}/tai-tai-lieu.htm?doctype=1` và PDF/ZIP liên kết trực tiếp ở đó.

## Trạng thái gần nhất đã ghi nhận

- Checkpoint tại thời điểm đọc: `updatedAt=2026-10-25T21:29:29Z`, `lastCompletedSymbol=IDC`, `activeSymbol=null`, `resumeSymbolHint=KBC`.
- Mã vừa hoàn tất: **IDC**, workflow [run #1607](https://github.com/kiemtimem123/so-lieu/actions/runs/40235656283).
- Mã kế tiếp theo checkpoint: **KBC**. Kiểm tra workflow mới nhất trước khi mở snapshot mã đó; không bắt đầu lại các mã đã hoàn thành.
- Lượt OCR IDC #1607 đã xử lý thành công, checkpoint chuyển từ PLX sang IDC rồi sang KBC. [Workflow #1607](https://github.com/kiemtimem123/so-lieu/actions/runs/40235656283).
- Kiểm định giao diện gần nhất thành công: [Validate Site and Data #966](https://github.com/kiemtimem123/so-lieu/actions/runs/40235725000).
- Kiểm định dữ liệu quý thành công sau khi ẩn các số liệu VCK chưa xác minh: [Validate quarterly financial data #416](https://github.com/kiemtimem123/so-lieu/actions/runs/40235360954).

## Các mã cần giữ ở trạng thái rà soát thủ công

- **VCB:** bỏ qua các số liệu chưa xác minh đến Q2/2026.
- **VCI:** `skipUnconfirmedThroughPeriod=2026-Q3`.
- **VCK:** `skipUnconfirmedThroughPeriod=2026-Q3`. Bảy kỳ Q1/2025–Q3/2026 đều chưa xác minh được phạm vi hợp nhất. 174 giá trị OCR được giữ trong `scope_unverified_financial_values.values`, còn trường tài chính cấp trên để `null`; liên kết nguồn và lý do rà soát vẫn còn. VCI/VCK sẽ tự được mở lại khi có kỳ sau Q3/2026.

## Quy tắc giao diện và các commit liên quan

- Frontend `assets/app.js` làm trống chỉ tiêu tài chính hiển thị đối với các hàng có `source_validation.scope_validation_required` hoặc `manual_review_blocking_automatic_extraction`; giữ nguồn/trạng thái để rà soát.
- Cache script trong `index.html`: `assets/app.js?v=financial-line-items-10-scope-review-1`.
- Ẩn số liệu theo phạm vi nguồn: https://github.com/kiemtimem123/so-lieu/commit/59628ea946335cbfee5bb811bc7cee2b4f10b26b
- Lưu số VCK vào audit thay vì trường hiển thị: https://github.com/kiemtimem123/so-lieu/commit/78e98ad648876c14d4cf32bab59cfbdf31eca5a8
- Đóng checkpoint VCK để bỏ qua tự động: https://github.com/kiemtimem123/so-lieu/commit/4d3882f9ca46d7d6f46bd227ccbcd7f24f41891e
- Cache tag tương thích với kiểm định: https://github.com/kiemtimem123/so-lieu/commit/2cc15e75b610cbedb2ca585f18fbac281a470413

Ghi chú này là lối tắt tiếp nối, không thay thế checkpoint sống. Mỗi lần tiếp tục, đọc checkpoint và workflow mới nhất rồi chỉ mở snapshot/sidecar của mã đang được chọn.
