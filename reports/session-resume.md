# Ghi chú tiếp nối phiên xử lý báo cáo tài chính

## Cách tiếp tục mà không nạp lại dữ liệu cũ

1. Đọc `reports/processing-checkpoint.json` và trạng thái GitHub Actions mới nhất trước tiên. Checkpoint là nguồn sự thật; nếu dữ liệu tham chiếu ở ghi chú này cũ, ưu tiên checkpoint.
2. Chỉ đọc `data/financials-{SYMBOL}.json` và sidecar thuộc `reports/raw/{SYMBOL}/` của mã đang làm. Không quét tất cả tệp financials hay toàn bộ kho OCR.
3. Xử lý từng mã một; đợi checkpoint/commit cho mã hiện tại được lưu trước khi sang mã kế tiếp.
4. Theo yêu cầu người dùng, nếu số liệu không xác minh được thì để trống các trường hiển thị, đánh dấu rà soát thủ công rồi tiếp tục. Không suy đoán số để cân đối báo cáo.
5. Nguồn duy nhất cho báo cáo tài chính: danh mục tài liệu VietstockFinance `https://finance.vietstock.vn/{ticker}/tai-tai-lieu.htm?doctype=1` và PDF/ZIP được liên kết trực tiếp từ danh mục này.

## Trạng thái sống gần nhất

- Checkpoint hiện tại trên `main` (đọc ngay trước khi ghi chú này): `updatedAt=2026-10-25T21:28:15Z`, `lastCompletedSymbol=PLX`, `activeSymbol=null`, `resumeSymbolHint=IDC`.
- Mã đã hoàn tất gần nhất: **PLX**, workflow [run #1606](https://github.com/kiemtimem123/so-lieu/actions/runs/40235585743).
- Mã được bộ chọn hàng đợi chọn kế tiếp sau khi đọc checkpoint: **IDC**, workflow #1607: https://github.com/kiemtimem123/so-lieu/actions/runs/40235656283. Khi tiếp tục, kiểm tra workflow này và checkpoint mới nhất trước khi mở snapshot IDC.
- Các mã VCB, VCI, VCK đang được bỏ qua ở hàng đợi tự động do còn kỳ cần rà soát thủ công:
  - VCB: bỏ qua phần chưa xác minh đến Q2/2026.
  - VCI: `skipUnconfirmedThroughPeriod=2026-Q3`.
  - VCK: `skipUnconfirmedThroughPeriod=2026-Q3`; khi tiêu đề VietstockFinance chưa xác minh được phạm vi hợp nhất, các giá trị OCR được giữ trong `scope_unverified_financial_values.values`, còn các trường tài chính cấp trên đã `null` để không hiển thị. Nguồn PDF và trạng thái rà soát vẫn được giữ.
- Frontend `assets/app.js` làm trống giá trị hiển thị cho hàng có `source_validation.scope_validation_required` hoặc `manual_review_blocking_automatic_extraction`, dùng cho biểu đồ/tổng quan/bảng/so sánh. Cache trong `index.html`: `assets/app.js?v=financial-line-items-10-scope-review-1`.
- Kiểm tra thành công gần nhất cho giao diện: [Validate Site and Data #964](https://github.com/kiemtimem123/so-lieu/actions/runs/40235420638). Kiểm tra dữ liệu báo cáo quý: [#416](https://github.com/kiemtimem123/so-lieu/actions/runs/40235360954).

## Các commit liên quan

- Giao diện ẩn metric khi phạm vi hợp nhất chưa xác nhận: https://github.com/kiemtimem123/so-lieu/commit/59628ea946335cbfee5bb811bc7cee2b4f10b26b
- Lưu các số VCK chưa xác minh vào audit và ẩn khỏi trường tài chính: https://github.com/kiemtimem123/so-lieu/commit/78e98ad648876c14d4cf32bab59cfbdf31eca5a8
- Đóng trạng thái VCK chờ rà soát trong checkpoint: https://github.com/kiemtimem123/so-lieu/commit/4d3882f9ca46d7d6f46bd227ccbcd7f24f41891e
- Tên cache tương thích với kiểm định: https://github.com/kiemtimem123/so-lieu/commit/2cc15e75b610cbedb2ca585f18fbac281a470413

Ghi chú này là lối tắt tiếp nối, không thay thế checkpoint sống. Lần sau, đọc checkpoint và workflow mới nhất rồi chỉ mở snapshot/sidecar của mã đang được chọn.
