# Dữ Liệu Kinh Tế Việt Nam — dự án mới hoàn toàn

Website PHP + HTML/CSS/JavaScript, không sử dụng mã nguồn hoặc tệp ZIP cũ. Không chứa giá thị trường hay báo cáo tài chính giả.

## 1. Chạy trên Hostinger

1. Tạo website/domain trong hPanel.
2. Tải nội dung ZIP lên `public_html/` (không tải thư mục bọc `dulieu-kinhte-fresh` nếu muốn `index.html` ở root).
3. Bật PHP 8.1+ nếu có thể. Giao diện tĩnh vẫn tải được, các endpoint `api/*.php` cần PHP.
4. Đảm bảo thư mục `data/` đọc được bởi PHP. Quyền thư mục thường 755 và tệp 644.
5. Mở website và kiểm tra Developer Tools > Network; thử mở `/api/status.php`.

## 2. Cập nhật giá tự động

Workflow `.github/workflows/update-data.yml` chạy 09:00 giờ Việt Nam (02:00 UTC) trên GitHub Actions. Nó lấy dữ liệu lịch sử cho các mã Yahoo chart đã cấu hình: `CL=F`, `BZ=F`, `HG=F`, `SI=F`.

Lưu ý:
- Đây là endpoint không chính thức. Khả năng truy cập, tính chính xác, giấy phép và điều khoản sử dụng phải được xác minh trước khi vận hành thương mại.
- Workflow cập nhật commit dữ liệu vào GitHub, nhưng **không tự đẩy lên Hostinger**. Cần cấu hình Hostinger Git deployment hoặc bổ sung FTP deploy riêng.
- Cron trên GitHub có thể chạy trễ. Dữ liệu hiển thị timestamp thực tế của nguồn, không giả định dữ liệu mới đúng 09:00.
- Không có API nguồn cho phân bón, hóa chất, hồ tiêu, cao su trong gói mặc định. Cần chọn nhà cung cấp và mã/định nghĩa giá cụ thể trước khi bật.

## 3. Báo cáo tài chính

12 mã: MBB, ACB, FPT, SHB, TCX, HCM, VND, SHS, NLG, BSR, TCB, VHM. Tệp `data/financials-<SYMBOL>.json` để trống cho đến khi được nạp dữ liệu có nguồn. Không được coi file rỗng là báo cáo đã đồng bộ.

Schema gợi ý:
```json
{
  "items": [
    {
      "period": "2025-Q4",
      "total_assets": 123,
      "total_liabilities": 45,
      "equity": 78,
      "pretax_profit": 10,
      "net_profit": 8,
      "roa": 2.1,
      "roe": 15.4,
      "unit": "tỷ VND",
      "source_url": "URL tài liệu gốc",
      "published_at": "2026-02-01"
    }
  ]
}
```
Các số trên chỉ minh họa **cấu trúc trường**, không phải dữ liệu doanh nghiệp; không đưa chúng vào dữ liệu chạy thật.

## 4. API nội bộ

- `GET /api/status.php`
- `GET /api/commodities.php`
- `GET /api/commodity-history.php?id=crude-brent&days=30`
- `GET /api/financials.php?symbol=MBB&from=2022-01-01`
- `GET /api/macro.php`

## 5. Bảo mật & vận hành

- Không đặt API keys trong `assets/app.js` hoặc tệp public.
- Không thu thập/scrape website bên thứ ba trái điều khoản; ưu tiên API được cấp phép, dữ liệu mở và tài liệu gốc.
- Trước khi vận hành thật, kiểm thử từng nguồn, kiểm tra đơn vị, thời điểm đóng cửa theo múi giờ Việt Nam, dữ liệu điều chỉnh và nhật ký lỗi.
- Bản này là nền tảng mới độc lập, chưa được triển khai lên tài khoản Hostinger của bạn.

## Giao diện tham chiếu

Trang chủ đã được điều chỉnh theo các ảnh tham chiếu do người dùng cung cấp: thanh danh mục dọc màu trắng ngà/tím, tiêu đề serif “Số liệu kinh tế vĩ mô Việt Nam”, thẻ chỉ số tối giản và đường xu hướng xanh. Đây là bản tái tạo giao diện dựa trên ảnh tham chiếu, không phải bản sao mã nguồn của website bên ngoài. Số liệu không có nguồn xác minh tiếp tục để trống.

## 6. Tích hợp API chính thức dulieukinhte.com (vĩ mô)

Thay vì scrape HTML cho GDP/CPI/bán lẻ/tỷ giá/lãi suất, cấu hình API chính thức theo `docs/DLKT-API-SETUP.md`. API key chỉ được lưu trong GitHub Actions Secret `DLKT_API_KEY`. Workflow đồng bộ một lần/ngày 09:00 giờ Việt Nam, gộp tối đa 20 series mỗi lượt và commit các JSON snapshot vào GitHub để Hostinger Git Deployment tự triển khai (cần bật Auto-deployment cho đúng branch). Không cần FTP secrets.

**Cần hoàn tất thủ công trước lần đồng bộ đầu tiên:** đăng ký key, khám phá `series_id` thật từ từng dataset, rồi điền `config/api_series.json`. Dataset ID trong cấu hình không phải series ID. Chưa có key/series IDs thì dashboard không hiển thị số liệu giả; biểu đồ báo chưa có dữ liệu.


## 7. Đồng bộ báo cáo phân tích PDF vào MySQL (hàng tuần)

Pipeline mới được tách khỏi luồng dữ liệu tài chính chính thức để không làm thay đổi các bảng/biểu đồ đang chạy:

1. GitHub Actions chạy mỗi Chủ nhật lúc 02:30 UTC (09:30 giờ Việt Nam), đọc danh mục `data/analysis-reports.json`.
2. Worker chỉ tải PDF từ liên kết HTTPS thuộc danh sách miền cho phép, xử lý trong bộ nhớ tạm, không lưu file PDF hoặc toàn văn trích xuất vào repository.
3. Worker tạo tóm tắt trích xuất ngắn và các ứng viên chỉ tiêu tài chính; mọi chỉ tiêu tự trích xuất được lưu trạng thái `needs_review`, không được coi là số liệu đã xác minh.
4. Payload được gửi qua HTTPS tới `/api/analysis-reports.php`. Giao diện thư viện báo cáo ưu tiên API DB; nếu DB chưa cấu hình hoặc API lỗi, giao diện tự quay lại snapshot JSON hiện tại.

### Thiết lập một lần trên Hostinger

- Tạo cơ sở dữ liệu MySQL và user riêng chỉ có quyền cần thiết trên cơ sở dữ liệu đó.
- Chạy file `database/analysis-reports.sql` trong phpMyAdmin.
- Cấu hình các biến môi trường phía máy chủ PHP: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `REPORT_SYNC_TOKEN`. Tạo token ngẫu nhiên dài; không ghi giá trị thật vào GitHub hay mã nguồn.
- Nếu Hostinger không hỗ trợ biến môi trường PHP trực tiếp, đặt cấu hình trong file riêng **ngoài public_html** và nạp từ cấu hình máy chủ; không tạo file thông tin đăng nhập có thể tải công khai.
- Trong GitHub repository Settings → Secrets and variables → Actions, thêm variable `REPORT_SYNC_URL` bằng URL HTTPS đầy đủ tới API và secret `REPORT_SYNC_TOKEN` có cùng giá trị token trên máy chủ.
- Triển khai các file mới lên Hostinger. Trước lần đồng bộ đầu tiên, kiểm tra `GET /api/analysis-reports.php` trả về JSON (nếu DB chưa cấu hình, endpoint trả HTTP 503 nhưng giao diện vẫn dùng JSON dự phòng). Sau đó chạy workflow thủ công để kiểm tra kết nối.

### Giới hạn và quyền sử dụng

- Đây là danh mục và phần tóm tắt ngắn, không phải bản sao lưu PDF. Không xuất bản PDF/toàn văn hoặc nội dung trích xuất đầy đủ.
- Tóm tắt do thuật toán trích xuất tạo ra cần rà soát biên tập trước khi xem là khuyến nghị đầu tư.
- Số liệu nhận dạng tự động là **ứng viên cần kiểm tra**; đối chiếu tài liệu gốc, kỳ báo cáo, đơn vị và ngữ cảnh trước khi duyệt. Không tự động ghi đè dữ liệu báo cáo tài chính chính thức.
- Nếu nguồn chặn truy cập, không phải PDF, yêu cầu đăng nhập hoặc trả lỗi, worker giữ liên kết và ghi trạng thái tương ứng; không vượt qua cơ chế truy cập.
- Việc đồng bộ vào cơ sở dữ liệu thật chỉ hoạt động sau khi người quản trị cấu hình database và Actions variable/secret ở trên. Repository không chứa thông tin đăng nhập.
