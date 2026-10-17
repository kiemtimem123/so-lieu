# Kho báo cáo

Danh mục báo cáo của website được khai báo tại `library.json`.

## Lưu trữ file PDF

- Chỉ tải lên/lưu bản PDF khi có quyền lưu trữ và phân phối phù hợp.
- Đặt PDF tại thư mục `storage/reports/<nhóm>/<mã-cổ-phiếu>/<năm>/` trên hosting.
- Nếu không được phép lưu, để `storage_path` trống và điền `source_url` tới trang/tệp gốc.
- Không commit PDF có bản quyền vào GitHub.
- Mỗi báo cáo cần tên, mã cổ phiếu (nếu có), loại, ngày công bố, nguồn và đường dẫn.
- Các bản tóm tắt/chỉ tiêu trích xuất phải được kiểm tra trước khi đánh dấu đã xác minh.
