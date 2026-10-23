# Kho báo cáo

Danh mục báo cáo của website được khai báo tại `library.json`.

## Lưu trữ file PDF

- Chỉ tải lên/lưu bản PDF khi có quyền lưu trữ và phân phối phù hợp.
- Đặt PDF tại thư mục `storage/reports/<nhóm>/<mã-cổ-phiếu>/<năm>/` trên hosting.
- Nếu không được phép lưu, để `storage_path` trống và điền `source_url` tới trang/tệp gốc.
- Không commit PDF có bản quyền vào GitHub.
- Mỗi báo cáo cần tên, mã cổ phiếu (nếu có), loại, ngày công bố, nguồn và đường dẫn.
- Các bản tóm tắt/chỉ tiêu trích xuất phải được kiểm tra trước khi đánh dấu đã xác minh.

## Lưu checkpoint và tiếp tục sau gián đoạn

- `processing-checkpoint.json` ghi mã đang xử lý, mã đã qua hàng đợi xử lý tự động, kỳ dữ liệu hiện có và các phần còn thiếu.
- Quy trình chỉ xử lý **một mã cổ phiếu tại một thời điểm** và tối đa **một báo cáo mỗi lượt OCR**. Sau khi tiến độ của báo cáo được lưu thành công, workflow mới kích hoạt lượt tiếp theo.
- `completedSymbols` nghĩa là không còn khoảng trống xử lý tự động được bộ chọn phát hiện; trạng thái này **không đồng nghĩa** toàn bộ chỉ tiêu đã được người kiểm tra đối chiếu trực quan.
- Khi tiếp tục thủ công, chạy workflow `OCR Financial Report Archive` và để trống đầu vào `symbol`. Workflow sẽ dò lại các snapshot và sidecar đã lưu để chọn điểm tiếp tục; không xóa `data/financials-*.json` hoặc `reports/raw/`.
- Snapshot JSON, PDF/ZIP nguồn được phép lưu và các tệp `.extracted.json` đã commit là nguồn dữ liệu khôi phục chính; checkpoint là bản tóm tắt tiến độ.

## Phạm vi kỳ báo cáo theo từng mã

- Mỗi mã có thể khai báo `startPeriod` trong `config/securities.json` khi chuỗi dữ liệu bắt đầu từ một kỳ khác nhau.
- Với VCK, `startPeriod` là `2025-Q1`. Những báo cáo quý 2024 tìm được dưới mã nguồn VPSS/đường dẫn OTC được giữ tại `pre_listing_legacy_reports`, không đưa vào `items` hoạt động dùng cho chuỗi VCK.
- Không xóa PDF/ZIP đã lưu; tách riêng dữ liệu ngoài phạm vi nhằm giữ khả năng truy vết nguồn.

