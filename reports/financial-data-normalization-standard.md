# Quy trình chuẩn hóa dữ liệu tài chính theo từng mảng

Phiên bản: 1.0  
Ngày thiết lập: 2026-10-28  
Phạm vi: `kiemtimem123/so-lieu`, dữ liệu BCTC quý từ 2024-Q1 trở đi.

## Nguyên tắc bắt buộc

1. Xử lý **một mảng dữ liệu tại một thời điểm**. Không thay đổi song song các mảng khác. Hoàn tất, kiểm thử và lưu mảng hiện tại rồi mới chuyển sang mảng tiếp theo.
2. Trong mỗi mảng, ưu tiên xử lý **một mã chứng khoán mỗi lượt**. Không chạy lại từ đầu nếu đã có checkpoint; tiếp tục từ trạng thái đã lưu.
3. Nguồn báo cáo duy nhất: danh mục tài liệu VietstockFinance `https://finance.vietstock.vn/{TICKER}/tai-tai-lieu.htm?doctype=1` và PDF/ZIP được liên kết trực tiếp từ danh mục đó. Ưu tiên BCTC hợp nhất; báo cáo riêng lẻ phải được nhận diện và tách đúng phạm vi.
4. Không tự suy đoán hoặc điền số liệu chưa có bằng chứng. Ô thiếu, OCR không chắc, sai phạm vi hợp nhất hoặc không đối chiếu được phải để trống và gắn trạng thái rà soát.
5. Giữ nguyên bố cục, cấu trúc thư mục và các chức năng đang hoạt động; chỉ sửa phần cần thiết cho mảng đang xử lý.
6. Mỗi sửa đổi phải truy vết được: mã, kỳ, trường dữ liệu, nguồn PDF, nguyên nhân, quy tắc đã áp dụng, kết quả kiểm tra và commit/checkpoint.

## Quy trình chuẩn cho mỗi mảng dữ liệu

### A. Khảo sát trước khi sửa
- Xác định đúng tab, danh sách trường dữ liệu, hàm ánh xạ/render, hàm kiểm tra và dữ liệu snapshot liên quan.
- Lấy trạng thái checkpoint và commit gần nhất; ghi rõ mảng đang xử lý, mã/kỳ đang xét.
- Chọn một mã và một kỳ đại diện có liên kết nguồn hợp lệ; không suy rộng lỗi từ một mã sang toàn bộ danh mục khi chưa kiểm chứng.

### B. Đối chiếu nguồn và chuẩn hóa
- Đọc đúng PDF do VietstockFinance liên kết; xác nhận mã, kỳ, loại báo cáo, hợp nhất/riêng lẻ, đơn vị, cột quý riêng hay lũy kế.
- Chuẩn hóa tên chỉ tiêu và đơn vị nhất quán; giữ nguyên dấu âm/dương theo báo cáo.
- Không dùng số lũy kế YTD thay cho số phát sinh riêng quý.
- Chỉ tính lại khi công thức kế toán xác định rõ, đầu vào đều có nguồn và phép tính được ghi chú. Không dùng phép tính để che lỗi OCR hoặc thiếu đầu vào.
- Không đưa trường bị đánh dấu rejected vào phần công khai chỉ vì trường đó có giá trị số. Chỉ khôi phục khi đã đối chiếu nguồn và lưu bằng chứng/trạng thái xác minh tương ứng.

### C. Sửa nguyên nhân gốc
- Phân biệt lỗi nguồn dữ liệu, lỗi schema/alias, lỗi kiểm định, lỗi chọn phạm vi báo cáo và lỗi hiển thị.
- Sửa nhỏ nhất có thể trong đúng mảng đang làm; không sao chép số giữa các mã, kỳ hoặc tab.
- Bảo đảm khi đổi mã/kỳ, bảng không giữ số liệu cũ và mọi tab dùng đúng trường dữ liệu riêng của tab đó.

### D. Kiểm thử bắt buộc
- Kiểm tra JSON/schema, mã và kỳ trùng, nguồn VietstockFinance, đơn vị, trạng thái xác minh và độ liên tục kỳ báo cáo.
- Kiểm tra cân đối kế toán: Tổng tài sản = Tổng nợ phải trả + Vốn chủ sở hữu trong dung sai đã quy định.
- Với kết quả kinh doanh: kiểm tra quan hệ doanh thu, giá vốn, lợi nhuận gộp và các tổng phụ khi các đầu vào có đủ.
- Với lưu chuyển tiền tệ: phân biệt quý riêng và YTD; kiểm tra tiền đầu kỳ + biến động tiền thuần = tiền cuối kỳ, tính đến ảnh hưởng tỷ giá nếu báo cáo có trình bày; đối chiếu liên kỳ khi cần.
- Với tỷ số: xác nhận đúng công thức, kỳ và mẫu số; không tính khi thiếu đầu vào hoặc không đủ dữ liệu so sánh.
- Chạy kiểm thử tự động liên quan và kiểm tra hồi quy ít nhất một mã khác cùng nhóm ngành; xác nhận các tab không hiển thị cùng một bộ số liệu do dùng nhầm nguồn.
- Phân loại kết quả: PASS, FAIL hoặc NEEDS_MANUAL_REVIEW. Không đánh dấu PASS nếu chỉ chạy được workflow nhưng chưa đối chiếu giá trị.

### E. Lưu kết quả và tiếp tục
- Lưu dữ liệu đã sửa, kiểm thử, ghi chú xác minh và cập nhật checkpoint/nhật ký trong cùng mảng công việc.
- Nhật ký tối thiểu: `data_domain`, `symbol`, `period`, `source_url`, `fields_changed`, `validation_results`, `manual_review_remaining`, `commit_sha`, `next_step`.
- Chỉ kết thúc mảng khi quy tắc được mô tả rõ, có kiểm thử tái sử dụng và không làm hỏng mảng khác.
- Sau khi mảng hiện tại được lưu, chuyển sang mã tiếp theo trong cùng mảng; chỉ chuyển sang mảng dữ liệu khác khi mảng trước đã có quy trình dùng lại được.

## Hồ sơ chuẩn hóa theo mảng

Mỗi mảng phải có hồ sơ riêng ghi quy tắc ánh xạ trường, phép kiểm tra, các ngoại lệ đã xác minh và ví dụ kiểm thử. Các thay đổi sau này phải dùng lại hồ sơ đó, chỉ bổ sung quy tắc mới khi có bằng chứng mới và ghi rõ phiên bản.

## Nhật ký khởi tạo

- Mảng đầu tiên cần xử lý: **Lưu chuyển tiền tệ**.
- Lý do ưu tiên: cần bảo đảm số quý riêng không bị nhầm với số lũy kế YTD, và kiểm tra cầu nối tiền đầu kỳ/biến động/tiền cuối kỳ.
- Mã đầu tiên: **TCB**, tiếp tục từ trạng thái và dữ liệu đã lưu; không chạy lại toàn bộ danh mục.
- Lưu ý: TCB từng có điều chỉnh cầu nối tiền quý trong phiên trước; cần kiểm tra lại snapshot và bài test hiện có trước khi thay đổi tiếp.

## Hồ sơ mảng 1 — Lưu chuyển tiền tệ (đang chuẩn hóa)

### Quy tắc đã xác nhận
- `net_cash_change` là biến động thuần từ ba nhóm hoạt động: kinh doanh + đầu tư + tài chính.
- Cầu nối số dư tiền phải tính cả ảnh hưởng tỷ giá khi báo cáo có dòng này:  
  `Tiền cuối kỳ = Tiền đầu kỳ + Lưu chuyển tiền thuần + Ảnh hưởng tỷ giá`.
- Khi so số phát sinh quý với lũy kế: `Quý N = YTD quý N − YTD quý N−1` trong cùng năm; Q1 riêng bằng YTD Q1.
- Nếu trường ảnh hưởng tỷ giá vắng mặt, không tự điền; chỉ ghi nhận phần chênh lệch để rà soát theo ngưỡng kiểm tra. Không tự quy chênh lệch thành ảnh hưởng tỷ giá.

### Lượt kiểm tra TCB
- Snapshot: `data/financials-TCB.json`, 11 kỳ từ 2024-Q1 đến 2026-Q3.
- Kiểm tra bằng số học trên snapshot: tổng ba luồng tiền khớp `net_cash_change` ở 11/11 kỳ; tổng ba luồng tiền YTD khớp `net_cash_change_ytd` ở 11/11 kỳ; luồng tiền quý khớp chênh lệch YTD với quý trước trong các kỳ Q2–Q4 có dữ liệu ở 8/8 kỳ.
- Cầu nối tiền sau khi tính ảnh hưởng tỷ giá: 2024-Q1 đến 2024-Q4 đều khớp chính xác; 2025-Q1 đến 2026-Q2 cũng khớp chính xác; 2026-Q3 còn chênh -20 triệu đồng trong snapshot và thiếu trường ảnh hưởng tỷ giá, giữ để rà soát chứ không tự sửa.
- Điểm cần lưu ý: số dư tiền đầu Q1/2026 trong snapshot cao hơn số dư cuối Q4/2025 là 565.285 triệu đồng. Vì chưa xác minh nguyên nhân trên PDF ở lượt này, không tự đồng bộ hai giá trị; cần kiểm tra trang lưu chuyển tiền tệ của báo cáo TCB Q4/2025 và Q1/2026 trước khi đánh dấu đã xác minh.
- Trạng thái lượt này: **PASS phần phép tính nội bộ; NEEDS_MANUAL_REVIEW phần đối chiếu PDF và chênh lệch số dư đầu năm**. Không tuyên bố đã xác minh trực quan nguồn PDF.

### Thay đổi quy tắc kiểm định
- `scripts/validate-bank-reconciliation.py` hiện trừ `foreign_exchange_effect` khỏi phần dư cầu nối khi trường này có số liệu; tránh báo lỗi giả do bỏ qua ảnh hưởng tỷ giá.
- Hàm `cash_bridge_delta` được tách riêng để kiểm thử hồi quy.
- Kiểm thử mới: `tests/test_cashflow_bridge.py` gồm trường hợp FX âm, FX dương, thiếu trường FX và thiếu dữ liệu đầu vào.
- Commit kiểm định FX: `59f4a86bfd935b8f8ed205506112899b69c5d320`; commit tách hàm dùng lại: `0f67a3bc99c177f33b1396c6c434824ae2e6784a`; commit kiểm thử: `301c23c1aa1e37f1798b4329dd2d257d4787a2e2`.

### Việc tiếp theo trong đúng mảng này
1. Chạy `python -m unittest tests/test_cashflow_bridge.py` và `python scripts/validate-bank-reconciliation.py` trong môi trường repo.
2. Đối chiếu PDF VietstockFinance cho TCB Q4/2025 và Q1/2026 để giải thích chênh lệch 565.285 triệu đồng ở số dư đầu kỳ.
3. Kiểm tra 2026-Q3 thiếu `foreign_exchange_effect`; chỉ cập nhật khi tìm thấy dòng tương ứng trong PDF.
4. Sau khi TCB hoàn tất, dùng cùng bộ quy tắc cho mã ngân hàng tiếp theo; không thay đổi mảng khác trong lượt này.
