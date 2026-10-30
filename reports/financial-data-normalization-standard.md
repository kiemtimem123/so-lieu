# Quy trình chuẩn hóa dữ liệu tài chính theo từng mảng

Phiên bản: 2.6  
Ngày thiết lập: 2026-10-28  
Cập nhật gần nhất: 2026-10-29  
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


### Đối chiếu nguồn PDF TCB — lượt tiếp theo (2026-10-28)

Đã đọc sidecar OCR của các PDF hợp nhất được lưu từ danh mục VietstockFinance, đúng trang LCTT:

- **TCB BCTC hợp nhất Q4/2025, PDF trang 10 (trang in 8):** báo cáo ghi tiền đầu kỳ **147.484.415**, biến động tiền thuần **43.777.643**, tiền cuối kỳ **191.262.058** triệu đồng. Cầu nối nội bộ khớp chính xác.
- **TCB BCTC hợp nhất Q1/2026, PDF trang 10 (trang in 8):** báo cáo ghi tiền đầu kỳ **191.827.343**, biến động tiền thuần **-12.117.985**, tiền cuối kỳ **179.709.358** triệu đồng. Cầu nối nội bộ khớp chính xác. Vì vậy chênh **565.285 triệu đồng** giữa số cuối Q4/2025 và số đầu Q1/2026 đã xuất hiện trong hai báo cáo gốc qua OCR, không phải do phép tính giữa các trường của snapshot. Chưa có bằng chứng giải thích việc chênh lệch; giữ nguyên từng số theo báo cáo, không tự đồng bộ.
- **TCB BCTC hợp nhất Q3/2026, PDF trang 12 (trang in 8):** báo cáo ghi biến động tiền thuần **-14.548.362**, tiền đầu kỳ **191.827.343**, tiền cuối kỳ **177.278.961** triệu đồng. Phép tính cuối kỳ − đầu kỳ − biến động thuần = **-20 triệu đồng**. Ba luồng hoạt động trong cùng báo cáo cộng đúng ra biến động tiền thuần; trang OCR không có dòng ảnh hưởng tỷ giá. Đây là sai lệch còn lại cần đối chiếu hình ảnh trang PDF, không được tự thêm FX hay sửa số.
- Kiểm thử tự động “Test cash-flow bridge reconciliation” trong GitHub Actions **PASS** ở run [40651448162](https://github.com/kiemtimem123/so-lieu/actions/runs/40651448162). Đây là kiểm thử logic cầu nối, không thay thế xác minh trực quan PDF.

**Kết luận lượt TCB:** phép kiểm tra nội bộ và bài test hồi quy PASS; đối chiếu OCR nguồn đã thực hiện cho Q4/2025, Q1/2026, Q3/2026; trạng thái tổng vẫn **NEEDS_MANUAL_REVIEW** do chênh lệch liên kỳ 565.285 triệu đồng và sai lệch cầu nối 20 triệu đồng. Chỉ đóng các ngoại lệ sau khi kiểm tra ảnh PDF gốc và có căn cứ rõ ràng. Không chuyển sang mảng dữ liệu khác ở bước này.


### Xác minh trực quan PDF Q4/2025 và Q1/2026

Đã xem trực tiếp ảnh trang 8 in trên PDF (trang PDF thứ 10) của cả hai báo cáo hợp nhất:
- [TCB Q4/2025, trang 8](https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%204/TCB_Baocaotaichinh_Q4_2025_Hopnhat.pdf): dòng tiền cuối kỳ là **191.262.058 triệu đồng**.
- [TCB Q1/2026, trang 8](https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/TCB_Baocaotaichinh_Q1_2026_Hopnhat.pdf): dòng tiền đầu kỳ là **191.827.343 triệu đồng**.

Như vậy chênh **565.285 triệu đồng được xác nhận bằng hình ảnh PDF gốc**, không phải lỗi OCR. Mỗi báo cáo tự cân đối theo số của chính báo cáo đó, nhưng chưa tìm thấy thuyết minh giải thích khác biệt giữa số cuối Q4 và số đầu Q1. Không sửa dữ liệu tự động; cần kiểm tra thêm thuyết minh số 34 và/hoặc tài liệu điều chỉnh nếu có trong chính danh mục VietstockFinance.

Q3/2026 vẫn còn chênh cầu nối **20 triệu đồng** theo OCR; PDF trực tiếp Q3 chưa được công cụ ảnh mở thành công trong lượt này, nên chưa coi là đã xác minh trực quan.

## Quy tắc bổ sung — ưu tiên BCTC năm đã kiểm toán khi chuẩn hóa LCTT Q4

Khi danh mục VietstockFinance có cả báo cáo Q4/năm trước kiểm toán và BCTC hợp nhất năm đã kiểm toán được công bố sau đó, với **mảng LCTT** cần:
1. Dùng số lũy kế cả năm và số dư tiền cuối năm từ BCTC năm đã kiểm toán mới hơn.
2. Tính số phát sinh riêng Q4 = số lũy kế cả năm đã kiểm toán − số lũy kế 9 tháng của cùng năm, cùng phạm vi hợp nhất.
3. Xác minh ba nhóm luồng tiền cộng thành biến động tiền thuần; xác minh tiền cuối kỳ − tiền đầu kỳ = biến động thuần khi báo cáo không trình bày dòng tỷ giá riêng.
4. Không quy chênh lệch giữa bản trước kiểm toán và bản kiểm toán thành tỷ giá chỉ để ép cầu nối khớp. Ghi nhận rõ bản nguồn cũ, bản kiểm toán thay thế, các trường bị sửa và công thức dẫn xuất. Chỉ sửa các trường của mảng đang xử lý; không ngầm thay số liệu KQKD hoặc bảng cân đối.

## Sửa TCB Q4/2025 theo BCTC hợp nhất năm đã kiểm toán — 2026-10-28

**Phát hiện mới thay thế kết luận sơ bộ ở nhật ký đối chiếu trước đó:** chênh 565.285 triệu đồng giữa số cuối Q4/2025 và số đầu Q1/2026 không phải là một khoản tỷ giá riêng. Trong kho nguồn VietstockFinance có PDF BCTC hợp nhất năm 2025 đã kiểm toán, công bố ngày 17/03/2026; sidecar được bổ sung đúng hai trang LCTT bằng OCR 300dpi:
- [PDF đã lưu trong kho: báo cáo hợp nhất năm 2025 đã kiểm toán](https://github.com/kiemtimem123/so-lieu/blob/main/reports/raw/TCB/vietstock-tcb-2024-2026-20261019/553195cdc772f58a.pdf)
- [Sidecar trích xuất trang 15–16](https://github.com/kiemtimem123/so-lieu/blob/main/reports/raw/TCB/vietstock-tcb-2024-2026-20261019/553195cdc772f58a.pdf.extracted.json)
- Danh mục nguồn chính: https://finance.vietstock.vn/TCB/tai-tai-lieu.htm?doctype=1

BCTC kiểm toán (PDF trang 15–16, trang in 10–11) ghi: LCTT kinh doanh cả năm **39.923.618**, LCTT đầu tư **-816.440**, LCTT tài chính **5.235.750**, biến động tiền thuần **44.342.928**, tiền đầu năm **147.484.415**, tiền cuối năm **191.827.343** triệu đồng. Báo cáo không trình bày dòng ảnh hưởng tỷ giá riêng trên hai trang LCTT này; phép tính tiền cuối − tiền đầu − biến động thuần bằng 0, được ghi nhận là giá trị đối chiếu dẫn xuất chứ không phải giá trị đọc từ một dòng tỷ giá.

Đã sửa data/financials-TCB.json, kỳ 2025-Q4:
- LCTT kinh doanh YTD: **39.358.333 → 39.923.618**; Q4 riêng: **38.511.806 → 39.077.091**.
- Biến động tiền thuần YTD: **43.777.643 → 44.342.928**; Q4 riêng: **31.338.378 → 31.903.663**.
- Tiền cuối kỳ báo cáo và tiền cuối Q4: **191.262.058 → 191.827.343**.
- LCTT đầu tư và tài chính giữ nguyên YTD theo bản kiểm toán; các số Q4 riêng được tính bằng lũy kế năm kiểm toán trừ lũy kế Q3/2025. Tiền đầu Q4 lấy đúng số cuối Q3/2025 là 159.923.680.

Kết quả sau sửa: ba luồng tiền Q4 cộng đúng **31.903.663**; cầu nối tiền Q4 159.923.680 + 31.903.663 = 191.827.343; cầu nối cả năm 147.484.415 + 44.342.928 = 191.827.343. Số cuối Q4 đã khớp với số đầu Q1/2026. Các trường KQKD và cân đối kế toán không bị thay đổi bởi sửa lỗi LCTT này.

### Bài kiểm thử hồi quy bắt buộc

tests/test_cashflow_bridge.py có thêm test nguồn thực kiểm tra số năm đã kiểm toán, công thức Q4 = FY kiểm toán − 9 tháng, tổng luồng tiền và cầu nối số dư. Test riêng cũng khóa sai lệch 20 triệu đồng còn lại ở TCB Q3/2026 để không ai vô tình tự bù tỷ giá hoặc sửa số khi chưa có bằng chứng. Workflow trích xuất có mục tiêu và workflow kiểm định được lưu trong repo; xem lịch sử GitHub Actions trước khi tuyên bố PASS.

**Trạng thái hiện tại:** TCB LCTT Q4/2025 đã **PASS nguồn OCR và phép đối chiếu số học**, chờ kiểm tra trực quan cuối cùng. Ngoại lệ còn mở trong mảng này là chênh cầu nối **20 triệu đồng ở Q3/2026**; tiếp tục xác minh trên PDF nguồn, không chuyển sang mảng dữ liệu khác cho đến khi đóng ngoại lệ hoặc ghi rõ terminal manual review.


## Đóng ngoại lệ cầu nối TCB Q3/2026 bằng OCR nguồn 300dpi — 2026-10-28

**Cập nhật sau phần nhật ký trước:** chênh 20 triệu đồng đã được giải quyết bằng cách đọc lại dòng số dư cuối kỳ trên đúng PDF gốc, không bằng cách ước lượng hoặc tự thêm tỷ giá.

- Nguồn: PDF BCTC hợp nhất Q3/2026 liên kết từ danh mục VietstockFinance: [PDF lưu trong kho](https://github.com/kiemtimem123/so-lieu/blob/main/reports/raw/TCB/repair-tcb-2026q3-full-report/fd82d64db310dbdb.pdf), PDF trang 12 (trang in 8).
- Sidecar trang 12 được OCR lại ở 300dpi bằng `tesseract-vie+eng-psm6-300dpi-targeted-rescan`; dòng báo cáo đọc là tiền cuối kỳ **177.278.981** triệu đồng. Lượt OCR trước ghi nhầm **177.278.961** do sai chữ số cuối.
- Đã sửa `data/financials-TCB.json` kỳ 2026-Q3: `cash_ending` và `cash_ending_reported_ytd` từ **177.278.961 → 177.278.981**. Không thay đổi các dòng lưu chuyển tiền.
- Kiểm tra lại: lũy kế `191.827.343 + (-14.548.362) = 177.278.981`; riêng quý `170.247.424 + 7.031.557 = 177.278.981`. Cả hai cầu nối dư **0**. Ba luồng tiền hoạt động vẫn cộng thành biến động tiền thuần đã báo cáo. Không thêm trường ảnh hưởng tỷ giá do báo cáo không trình bày dòng tỷ giá riêng và cầu nối nay đã khớp.
- Lịch sử sửa OCR cũ được bảo toàn trong `financial_line_items_value_corrections.cash_ending.prior_correction_record`; sidecar lưu dấu thời gian, trang nguồn, bộ OCR và giá trị trước/sau.
- Bài kiểm thử `tests/test_cashflow_bridge.py` được cập nhật để bắt buộc giá trị 177.278.981, xác nhận nguồn/trang OCR mục tiêu và kiểm tra cả cầu nối quý/YTD. Chỉ đánh dấu PASS hoàn chỉnh sau khi workflow kiểm thử cho commit sửa này thành công.

**Trạng thái mảng Lưu chuyển tiền tệ — TCB:** Q4/2025 đã chuẩn hóa bằng BCTC năm đã kiểm toán; Q3/2026 đã đọc lại nguồn và sửa lỗi OCR. Hai ngoại lệ số học đã khép lại. Dữ liệu đã qua OCR nguồn và đối chiếu số học; chưa tuyên bố kiểm tra thủ công từng pixel. Chờ workflow kiểm thử hậu sửa xác nhận PASS, sau đó lưu checkpoint hoàn tất mã TCB trước khi chuyển sang mã kế tiếp trong cùng mảng.


### Kết quả CI sau sửa TCB — xác nhận 2026-10-28

- [Validate Site and Data run 40666435248](https://github.com/kiemtimem123/so-lieu/actions/runs/40666435248): **SUCCESS**; bước `Test cash-flow bridge reconciliation` PASS, JSON snapshots PASS và kiểm tra cú pháp PASS.
- [Validate quarterly financial data run 40666351827](https://github.com/kiemtimem123/so-lieu/actions/runs/40666351827): **SUCCESS**; bước `Validate quarterly financial snapshots` và `Run bank statement reconciliation regression checks` PASS.
- [Targeted OCR run 40665985748](https://github.com/kiemtimem123/so-lieu/actions/runs/40665985748): **SUCCESS**; sidecar trang 12 Q3/2026 đã được OCR lại ở 300dpi và giá trị mới đã được kiểm tra bằng test.

Do đó TCB–LCTT không còn sai lệch số học mở: Q4/2025 đã được chuẩn hóa theo BCTC năm đã kiểm toán và Q3/2026 đã sửa sai chữ số do OCR. Trạng thái: **PASS nguồn OCR + đối chiếu số học + CI**; không đồng nghĩa với tuyên bố kiểm tra thủ công từng pixel. Bước kế tiếp theo hàng đợi trong cùng mảng là **MBB**, không chuyển sang tab/mảng khác.


## Lượt chuẩn hóa MBB — Lưu chuyển tiền tệ (2026-10-28)

### Cách làm đã chuẩn hóa thêm

- Với PDF BCTC hợp nhất ngân hàng, đọc trang LCTT 7–8; khi trường số bị trống, sai ánh xạ hoặc nghi OCR, chạy OCR mục tiêu 300dpi và ghi sidecar riêng trước khi thay snapshot. Script tái sử dụng: `scripts/extract-mbb-cashflow-pages.py`; workflow: [Extract MBB Cash-Flow Source Pages](https://github.com/kiemtimem123/so-lieu/actions/runs/40666978535).
- Không coi mọi số trong snapshot trước là đúng: so sánh từng luồng tiền, tổng biến động tiền, số dư đầu/cuối kỳ và số lũy kế. Những trường từng lấy nhầm dòng thu lãi hoặc chi phí đầu tư riêng phải được thay theo dòng tổng lưu chuyển tiền thuần.
- Nếu BCTC VietstockFinance của kỳ sau có cột so sánh năm trước, chỉ dùng số so sánh mới hơn khi cột đó xác định rõ cùng phạm vi hợp nhất và được kiểm tra trực quan. Lưu cả nguồn tài liệu gốc của kỳ và nguồn so sánh cập nhật; giữ lịch sử giá trị cũ/mới. Không lấy số so sánh từ một PDF khác mà không ghi provenance.
- Tách rõ ba phép kiểm: (a) tổng ba nhóm tiền = biến động tiền thuần; (b) cầu nối số dư trong riêng quý; (c) cầu nối số dư lũy kế từ đầu năm. Không thay đổi số báo cáo chỉ để làm (b) bằng 0 khi số dư hoặc cột so sánh gốc có chênh lệch; lưu residual và chuyển NEEDS_MANUAL_REVIEW.

### Kết quả MBB đã cập nhật

Đã OCR lại PDF trang 7–8 ở 300dpi cho đủ 10 kỳ từ Q1/2024 đến Q2/2026; workflow hoàn tất 10/10 nguồn, không lỗi. Thay đổi đã lưu trong [snapshot MBB](https://github.com/kiemtimem123/so-lieu/blob/main/data/financials-MBB.json), commit dữ liệu `eaf527a35f2b5a8bae098aebe0d85a94d4ea27cf`.

- Khôi phục trường thiếu LCTT tài chính, biến động tiền thuần và số dư tiền đầu/cuối ở những kỳ nguồn đã xác nhận.
- Sửa ánh xạ sai ở Q4/2024: `operating_cash_flow_ytd` trước đây lấy nhầm giá trị **68.529.262** từ dòng thu lãi, và `cash_ending` từng là **1.357.407**; thay bằng số LCTT đúng theo cột so sánh mới hơn trong BCTC Q4/2025.
- Sửa tiền đầu năm Q3/2024 từ OCR nhầm **409.095.118** về **109.095.118** sau kiểm tra trực quan trang 8.
- Dùng số so sánh H1/2025 từ PDF BCTC hợp nhất Q2/2026 đã kiểm tra trực quan trang 7–8: CFO **1.516.540**, đầu tư **-400.976**, tài chính **5.698.563**, biến động thuần **6.814.127**, tiền đầu/cuối kỳ **97.040.273 / 103.854.400** triệu VND. Số này thay các giá trị cũ của H1/2025 được trích từ báo cáo Q2/2025 trước đó. Số Q3/2025 riêng được tính dựa trên lũy kế H1 đã cập nhật.

### Ngoại lệ còn mở — MBB Q2/2025

Q1/2025 trong báo cáo gốc ghi tiền đầu kỳ **97.040.275**, tiền cuối kỳ **72.986.872**, biến động thuần **-24.053.403**. Cột so sánh H1/2025 trong báo cáo Q2/2026 sau đó ghi tiền đầu kỳ **97.040.273**, cuối kỳ **103.854.400**, biến động thuần **6.814.127**. Cả bộ số Q1 trong nguồn gốc tự cân, và cả bộ số H1 trong nguồn so sánh mới hơn tự cân; ba nhóm LCTT H1 cũng cộng đúng. Tuy nhiên số riêng Q2 tính từ chênh lệch YTD là **30.867.530**, trong khi cầu nối bằng tiền cuối Q2 trừ tiền cuối Q1 là **30.867.528**, chênh **-2 triệu VND**.

Không thay 2 triệu này vào CFO, dòng tài chính hay số dư tiền để làm cho cầu nối khớp giả tạo. Giữ số báo cáo theo nguồn tương ứng, lưu lịch sử và trạng thái `NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BRIDGE_2_MILLION` ở kỳ 2025-Q2. Đây là ngoại lệ duy nhất còn mở trong 10 kỳ MBB của mảng này; các kỳ còn lại có tổng các luồng và cầu nối quý/YTD khớp.

### CI sau chuẩn hóa MBB

- [Targeted source-page OCR](https://github.com/kiemtimem123/so-lieu/actions/runs/40666978535): PASS, đã xử lý đủ 10/10 archive nguồn.
- [Validate quarterly financial data](https://github.com/kiemtimem123/so-lieu/actions/runs/40668008382): PASS; quarterly snapshots và bank reconciliation regression checks PASS.
- [Validate Site and Data, có bài kiểm thử MBB](https://github.com/kiemtimem123/so-lieu/actions/runs/40668224913): PASS; kiểm thử cash-flow bridge và xác nhận JSON snapshots PASS. Bài kiểm thử chặn việc thay 2 triệu đồng như một balancing plug.

**Trạng thái MBB:** dữ liệu tự động đã chuẩn hóa/kiểm tra cho 10/10 kỳ; có 1 residual cross-quarter -2 triệu VND được lưu công khai để rà soát thủ công. Không gắn nhãn “mọi nguồn đã cân tuyệt đối”; các giá trị nguồn được giữ nguyên đúng theo chứng từ.


### Bảo đảm trường dữ liệu chuẩn hóa được tab LCTT hiển thị

Sau khi bổ sung hoặc khôi phục số LCTT, phải cập nhật `financial_line_items_extracted_fields` cho các trường nguồn đã đối chiếu (LCTT kinh doanh/đầu tư/tài chính, biến động tiền thuần, số dư tiền đầu/cuối quý và YTD). Trạng thái `pending_visual_review` vẫn phải giữ nếu chưa duyệt bằng mắt toàn bộ kỳ, nhưng không để bộ lọc của giao diện ẩn giá trị đã trích xuất có nguồn. Không đưa các trường thực sự bị từ chối hoặc phạm vi nguồn chưa xác nhận vào danh sách này. Bài test hồi quy kiểm tra cả số liệu, ngoại lệ nguồn và sự hiện diện của các trường.


## Rà soát bổ sung MBB — phát hiện liên tục số dư liên kỳ bị bỏ sót (2026-10-28)

### Phát hiện

Lượt rà soát thứ hai cho thấy kiểm tra trước đây chỉ xét cầu nối **bên trong từng quý** và cầu nối **YTD**, chưa khóa riêng điều kiện **tiền cuối quý trước = tiền đầu quý sau**, kể cả khi qua năm tài chính. Vì vậy, chỉ gắn cờ Q2/2025 là chưa mô tả đủ toàn bộ lỗi nguồn.

Đã đối chiếu trực quan ba PDF hợp nhất được lưu/định tuyến từ VietstockFinance:

1. [BCTC hợp nhất Q4/2025, PDF trang 7–8](https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%204/MBB_Baocaotaichinh_Q4_2025_Hopnhat.pdf) — cột so sánh năm 2024 ghi tiền cuối năm **97.040.273** triệu VND; LCTT kinh doanh năm 2024 **-18.576.384**, đầu tư **-2.238.209**, tài chính **8.759.748**, biến động tiền thuần **-12.054.845**.
2. [BCTC hợp nhất Q1/2025, PDF trang 8](https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%201/MBB_Baocaotaichinh_Q1_2025_Hopnhat.pdf) — tiền đầu kỳ **97.040.275**, biến động tiền thuần Q1 **-24.053.403**, tiền cuối kỳ **72.986.872**. Cầu nối trong chính báo cáo khớp bằng 0.
3. [BCTC hợp nhất Q1/2026, PDF trang 8](https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/MBB_Baocaotaichinh_Q1_2026_Hopnhat.pdf) — cột so sánh Q1/2025 lặp lại đúng ba số của báo cáo Q1/2025: **97.040.275**, **-24.053.403**, **72.986.872**.
4. [BCTC hợp nhất Q2/2026, PDF trang 7–8](https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%202/MBB_Baocaotaichinh_Q2_2026_Hopnhat.pdf?ver=8b5fd9ba) — cột so sánh H1/2025 ghi tiền đầu kỳ **97.040.273**, LCTT kinh doanh **1.516.540**, đầu tư **-400.976**, tài chính **5.698.563**, biến động tiền thuần **6.814.127**, tiền cuối kỳ **103.854.400**. Bộ số H1 tự cân; ba luồng tiền cộng đúng biến động thuần.

### Kết luận số học sau khi rà lại

- Chuyển tiếp Q4/2024 → Q1/2025: tiền đầu Q1 trừ tiền cuối Q4 = **+2 triệu VND**.
- Q1/2025: cầu nối nội kỳ vẫn bằng 0 theo số được ghi trên báo cáo Q1/2025 và cột so sánh Q1/2026.
- H1/2025: cầu nối lũy kế trong báo cáo Q2/2026 bằng 0 theo số được ghi trong báo cáo.
- Q2/2025 riêng, tính bằng lũy kế H1 mới hơn trừ Q1/2025 đã báo cáo: CFO **27.591.551**, đầu tư **-224.021**, tài chính **3.500.000**, biến động thuần **30.867.530**. Tuy nhiên, thay đổi số dư từ cuối Q1 **72.986.872** đến cuối Q2 **103.854.400** chỉ là **30.867.528**, vì vậy cầu nối riêng Q2 có residual **-2 triệu VND**.

Hai residual này có cùng độ lớn nhưng ngược dấu; chúng thuộc cùng một bất nhất cơ sở số dư liên kỳ. Q1/2025 và cột so sánh Q1/2026 xác nhận lẫn nhau, trong khi báo cáo Q4/2025 và cột so sánh H1/2025 ở Q2/2026 dùng số đầu/ cuối năm trước thấp hơn 2 triệu. Chưa có tài liệu đính chính trong tập nguồn đã kiểm tra giải thích sự khác biệt. **Không sửa giá trị báo cáo, không tự thêm tỷ giá, không thêm “plug” 2 triệu vào bất kỳ dòng tiền nào.** Ghi trạng thái rà soát thủ công ở cả Q1/2025 (đứt mạch số dư đầu kỳ so với Q4 trước) và Q2/2025 (cầu nối quý riêng).

### Quy tắc kiểm tra bắt buộc được bổ sung

Sau mỗi kỳ, chạy đủ bốn lớp:

1. Ba nhóm luồng tiền riêng quý = biến động tiền thuần riêng quý.
2. Ba nhóm luồng tiền YTD = biến động tiền thuần YTD.
3. Tiền cuối kỳ − tiền đầu kỳ − biến động tiền thuần (cộng ảnh hưởng tỷ giá **chỉ khi báo cáo có dòng riêng**), kiểm tra riêng cho quý và YTD.
4. **Liên tục số dư giữa hai quý liền kề:** tiền cuối quý trước phải bằng tiền đầu quý sau, kể cả Q4 → Q1 và khi có cột so sánh được trình bày lại. Nếu bất kỳ báo cáo/cột so sánh mới hơn làm đổi cơ sở, ghi nhận cả hai nguồn, residual và trạng thái review; không âm thầm thay giá trị nguồn cũ.

Kiểm thử `tests/test_cashflow_bridge.py` nay bao phủ phép tính phát sinh quý = chênh lệch YTD cho từng luồng, continuity liên quý qua năm, cùng hai residual nguồn MBB (+2 ở chuyển tiếp Q4→Q1 và -2 ở cầu nối riêng Q2). Test tổng quát “thiếu FX thì không tự bịa FX” dùng dữ liệu giả lập, không lấy lại giá trị OCR TCB đã sửa.

**Trạng thái MBB sau rà soát bổ sung:** 10/10 kỳ khớp thành phần luồng tiền và cầu nối YTD; phát sinh quý khớp chênh lệch YTD ở mọi kỳ đã có số liệu. Cầu nối nội kỳ tự khớp ở 9/10 kỳ. Tuy nhiên, kiểm tra liên tục số dư phát hiện thêm mâu thuẫn Q4/2024 → Q1/2025 **+2 triệu VND**, gắn với residual **-2 triệu** tại Q2/2025. Hai residual được ghi nhận là **một vấn đề so sánh liên kỳ chưa giải quyết**, không phải lỗi phép cộng trong snapshot. Chỉ đóng ngoại lệ khi có bằng chứng nguồn mới có thẩm quyền hoặc tài liệu đính chính rõ ràng.


### Sửa lỗi đơn vị ở residual metadata — 2026-10-28

Trong lượt test continuity MBB, phát hiện một lỗi ghi metadata: snapshot báo cáo dùng **triệu VND**, nhưng hai trường `opening_minus_prior_closing_residual` và `prior_year_end_to_q1_opening_residual` đã lưu giá trị `2.000.000` trong khi phép trừ trên dữ liệu snapshot là `97.040.275 − 97.040.273 = 2`. Đã sửa cả hai trường về **2** và gắn `units: "triệu VND"`; các số dư nguồn không đổi. Đã quét đệ quy các trường tên residual/bridge trong snapshot MBB và TCB: không còn residual metadata nào có trị tuyệt đối lớn hơn 1.000 mà có vẻ bị phóng đại đơn vị.

Quy tắc chuẩn hóa: mọi phép chênh và residual phải ở **đúng đơn vị của các trường đầu vào**. Với snapshot dùng triệu VND, residual `2` nghĩa là 2 triệu VND; không nhân thêm 1.000.000. Bài test hồi quy xác nhận giá trị ở cả metadata của Q1 và Q2, đồng thời vẫn giữ hai dấu khác nhau của cùng bất nhất: +2 ở điểm chuyển Q4/2024→Q1/2025 và -2 ở cầu nối Q2/2025 riêng. Không quy đổi sang VND nguyên nếu không khai báo đơn vị và chuyển đổi tường minh.


## Lượt chuẩn hóa ACB — lưu chuyển tiền tệ (2026-10-28)

### Sửa nguyên nhân gốc của dòng tiền kinh doanh bị ẩn/sai
- Snapshot: `data/financials-ACB.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2.
- Trước khi sửa, một số bản ghi dùng dòng **“Lưu chuyển tiền thuần từ hoạt động kinh doanh trước những thay đổi của tài sản và công nợ hoạt động”** như thể đó là lưu chuyển tiền kinh doanh thuần. Đây là subtotal trước biến động vốn lưu động, không phải dòng cuối nhóm; phải luôn lấy dòng `I. Lưu chuyển tiền thuần từ hoạt động kinh doanh`.
- Đối với từng kỳ, chuẩn hóa đủ ba nhóm lưu chuyển tiền và biến động tiền thuần theo cột YTD trên PDF; tiền đầu/cuối kỳ và ảnh hưởng tỷ giá được ghi theo báo cáo. Giá trị quý riêng được tính bằng YTD hiện tại trừ YTD quý trước trong cùng năm.
- Ưu tiên so sánh mới hơn ngay trong danh mục VietstockFinance: dùng FY2024 so sánh từ BCTC Q4/2025 (CFO YTD 8.370.231; CFI YTD -733.310; net change 3.752.870) thay cho số trích xuất cũ của Q4/2024; dùng Q1/2026 comparison cho Q1/2025; dùng Q2/2026 comparison cho H1/2025. Q4/2024 có chênh dịch chuyển 1 triệu đồng giữa CFO và CFI, tổng biến động tiền thuần không đổi.
- Nguồn Q2/2026 trên PDF trang 8 xác nhận tiền cuối kỳ là **116.533.043 triệu đồng**, không phải 416.533.043 do OCR đọc nhầm chữ số đầu; cấu phần tiền tương đương tiền cũng cộng thành 116.533.043.
- Q2/2026 comparison được dùng để đặt lại cơ sở YTD H1/2025. Các số quý riêng Q2/Q3/2025 được tính lại bằng chênh lệch YTD trên cùng cơ sở đã chọn; tuyệt đối không chèn một khoản “plug” để khớp cầu nối.
- Đối chiếu trực quan các trang nguồn đã hoàn thành cho Q1/2024, H1/2024, Q3/2024, FY2024 comparison trong Q4/2025, Q3/2025, FY2025, H1/2025 comparison trong Q2/2026 và Q2/2026. Q1/2025 comparative trong Q1/2026 và một số trang nguồn còn lại vẫn được đánh dấu chờ rà soát hình ảnh; việc tổng số học khớp không đồng nghĩa toàn bộ trường đã được xác minh trực quan.
- Kiểm tra trong snapshot sau chuẩn hóa: cả 10/10 kỳ đều có tổng CFO+CFI+CFF bằng net cash change; cả 10/10 kỳ YTD cũng khớp; cầu nối số dư tiền YTD và theo quý (có FX) đều dư 0; mọi luồng tiền quý bằng hiệu YTD liên tiếp; các trường LCTT được thêm vào danh sách `financial_line_items_extracted_fields` và gỡ khỏi danh sách trường bị loại.
- Bộ kiểm thử dùng lại: `tests/test_cashflow_bridge.py`, bổ sung regression riêng ACB cho 10 kỳ, FX, cầu nối, so sánh mới hơn và điều chỉnh OCR Q2/2026.
- Trạng thái: **PASS về số học và nguồn dòng chính; còn rà soát trực quan hạn chế ở các kỳ được ghi trạng thái pending**. Không đánh dấu toàn bộ ACB đã xác minh thủ công.


## Quy tắc dung sai tương đối 0,01% — cập nhật 2026-10-28

Quy tắc này **thay thế ngưỡng tuyệt đối 10 triệu VND** đã ghi ở checkpoint cũ khi đánh giá sai lệch số học:

- Với một phép đối chiếu, tính `relative_difference_percent = abs(actual - expected) / comparison_scale × 100`. Dùng mẫu số phù hợp với phép kiểm tra; đối với cầu nối tiền, mẫu số là quy mô số dư tiền cuối kỳ/dự kiến; đối với tổng các luồng tiền, so với quy mô các luồng thành phần và biến động tiền thuần.
- Nếu sai lệch tương đối **≤ 0,01%**, cho phép tiếp tục và phân loại là `ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT` (hoặc PASS nếu residual bằng 0). Lưu giá trị residual cùng đơn vị với snapshot để truy vết; không sửa số gốc và không chèn khoản cân bằng.
- Nếu sai lệch tương đối **> 0,01%**, giữ nguyên các giá trị đã được xác nhận trên nguồn, gắn `NEEDS_MANUAL_REVIEW` và tiếp tục các mã khác nếu phần tự động hóa cốt lõi của mã hiện tại đã hoàn tất.
- Dung sai chỉ áp dụng cho sai lệch số học/ làm tròn. Nó **không** cho phép tự sửa OCR sai chữ số, dùng sai kỳ, trộn BCTC riêng lẻ với hợp nhất, bỏ qua trang nguồn thiếu, hoặc suy đoán một trường không có bằng chứng. Trường FX không có trong báo cáo không được tự tạo chỉ vì chênh lệch nhỏ.

## Lượt chuẩn hóa FPT — lưu chuyển tiền tệ (2026-10-28)

- Snapshot `data/financials-FPT.json`: 10 kỳ từ 2024-Q1 đến 2026-Q2 được chuẩn hóa theo dòng 20 (CFO), 30 (CFI), 40 (CFF), 50 (biến động tiền thuần), 60 (tiền đầu kỳ), 61 (ảnh hưởng tỷ giá) và 70 (tiền cuối kỳ) trên BCTC hợp nhất từ danh mục VietstockFinance.
- Đã ưu tiên so sánh mới hơn: FY2024 sử dụng cột so sánh trong BCTC Q4/2025; H1/2025 sử dụng cột so sánh trong BCTC Q2/2026. Với FY2024, CFO/CFI so với snapshot cũ được trình bày lại lần lượt thành **11.703.777** và **-8.461.812 triệu VND**; CFF **-2.197.766**, biến động tiền thuần **1.044.199**. Đây là phân loại/số so sánh của báo cáo mới hơn, không lấy số cũ để bù cho tổng dòng tiền.
- Theo cột so sánh Q2/2026, H1/2025 là CFO **1.683.573**, CFI **-7.233.992**, CFF **6.254.833**, biến động tiền thuần **704.415**, FX **-224**, tiền cuối kỳ **10.019.631 triệu VND**. Số quý riêng Q2 và Q3/2025 được tính lại từ chênh lệch YTD theo cơ sở H1/2025 mới này.
- Residual số học nhỏ do các dòng tiền gốc chính xác đến VND nhưng snapshot lưu triệu VND và làm tròn, ví dụ Q1/2025 cầu nối tiền có residual **-10 triệu VND**; tỷ lệ so với số dư tiền nhỏ hơn 0,01%, nên được chấp nhận theo chính sách mới, được ghi trong metadata, không sửa số gốc.
- Ngoại lệ vượt ngưỡng: tiền cuối FY2025 **10.540.182 triệu VND** trong BCTC Q4/2025 so với tiền đầu Q1/2026 **10.522.106 triệu VND**; chênh **-18.076 triệu VND**, khoảng **0,17%**. Mỗi báo cáo tự khớp cầu nối của mình nhưng continuity liên kỳ vượt 0,01%; giữ nguyên cả hai số nguồn, đánh dấu `NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT`, không ép đồng bộ.
- Kiểm thử hồi quy FPT bao phủ 10 kỳ, so sánh FY2024/H1-2025 mới hơn, quý riêng = chênh lệch YTD, FX, cầu nối tiền và quy tắc 0,01%. Workflow `Validate Site and Data`, `Validate quarterly financial data` và `Package Hostinger Stock Dashboard` đều PASS sau thay đổi snapshot; kiểm thử xác nhận continuity Q4/2025 → Q1/2026 còn là ngoại lệ thủ công, không phải lỗi test.
- Trạng thái FPT: tự động hóa cốt lõi và kiểm thử hoàn tất; còn một ngoại lệ so sánh liên kỳ vượt ngưỡng ở Q1/2026. Có thể chuyển sang mã tiếp theo trong cùng miền dòng tiền, không chuyển mảng.


## Lượt chuẩn hóa SHB — lưu chuyển tiền tệ (2026-10-28)

### Sửa dữ liệu và chọn cơ sở so sánh
- Snapshot `data/financials-SHB.json`: 10 kỳ từ 2024-Q1 đến 2026-Q2.
- Đã sửa việc ẩn dòng tiền ở Q1–Q4/2024 do parser cũ trộn lẫn subtotal, số bị ánh xạ nhầm và các cơ sở báo cáo so sánh khác nhau. Cột YTD của từng nhóm phải lấy dòng tổng cuối nhóm (mã 24/34/41 trong mẫu SHB), không lấy subtotal trước biến động tài sản/vốn lưu động.
- Áp dụng quy tắc ưu tiên cột so sánh mới hơn trong tài liệu VietstockFinance:
  - Q1/2024: cột so sánh trong BCTC Q1/2025, CFO -52.416.402; CFI 202.387; CFF -327; biến động tiền thuần -52.214.342; tiền đầu kỳ 110.859.786; cuối kỳ 58.645.444. Cột này điều chỉnh CFO/net change +10.000.000 triệu đồng so với bản Q1/2024 cũ và khớp cầu nối tiền của chính báo cáo so sánh; ghi giữ dấu vết bản cũ.
  - H1/2024: cột so sánh trong BCTC Q2/2025, CFO -22.155.105; CFI -66.706; CFF 434.732; biến động tiền thuần -21.787.079; cuối kỳ 89.072.707.
  - 9T/2024: cột so sánh trong BCTC Q3/2025, CFO 5.828.557; CFI -88.386; CFF 400.074; biến động tiền thuần 6.140.245; cuối kỳ 117.000.031. Các tổng số khớp báo cáo Q3/2024 đã đối chiếu trực quan.
  - FY2024: cột so sánh trong BCTC Q4/2025, CFO 11.949.125; CFI -179.988; CFF -1.311.389; biến động tiền thuần 10.457.748; cuối kỳ 121.317.534. Bộ số này thay thế bản trình bày trước trong báo cáo Q4/2024.
- Quý riêng được tính bằng YTD mới của kỳ hiện tại trừ YTD mới của quý trước cùng năm. Sau khi áp dụng cùng cơ sở, tất cả luồng tiền quý/ytd và cầu nối tiền từng kỳ khớp chính xác; không cần dùng dung sai để che sự lệch nguồn lớn do bản trình bày khác nhau.
- Soát trực quan trang lưu chuyển tiền của BCTC SHB Q1/2025, Q2/2025, Q4/2025 và Q1/2026; Q3/2024 cũng đã đối chiếu trực quan ở PDF gốc. Q3/2025 và Q2/2026 có sidecar OCR đã lưu, nhưng cần xem ảnh trực tiếp ở lượt sau trước khi tuyên bố xác minh toàn bộ trực quan.
- Ngoại lệ liên kỳ còn lại: tiền cuối Q4/2025 là 162.627.663 triệu VND; tiền đầu Q1/2026 được báo cáo là 161.907.719 triệu VND; residual -719.944 triệu VND, tương đương khoảng **0,4427%**, lớn hơn ngưỡng 0,01%. Mỗi báo cáo riêng tự cân đối. Giữ nguyên hai số nguồn, gắn `NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT`; không đồng bộ, không tự suy diễn tỷ giá và không thêm khoản bù.
- Regression mới trong `tests/test_cashflow_bridge.py` bao phủ 10 kỳ, tổng ba luồng tiền, chênh YTD, cầu nối có FX, các cột so sánh được chọn và ngoại lệ Q4/2025→Q1/2026. Validator được mở rộng để chạy schema dữ liệu SHB hiện hành và kiểm tra liên tục số dư qua ranh giới năm bằng ngưỡng tương đối 0,01%.
- Trạng thái SHB: **PASS phép tính nội kỳ và lựa chọn cơ sở so sánh; NEEDS_MANUAL_REVIEW duy nhất cho residual mở đầu năm 2026 vượt 0,01%**, kèm rà soát trực quan còn lại ở các trang đã đánh dấu pending.


## Lượt chuẩn hóa HCM — lưu chuyển tiền tệ (2026-10-28)

### Quy tắc dữ liệu theo báo cáo CTCK
- Snapshot: `data/financials-HCM.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2.
- Báo cáo lưu chuyển tiền tệ của HCM dùng mẫu CTCK: dòng 60 là lưu chuyển tiền thuần từ hoạt động kinh doanh, dòng 70 từ đầu tư, dòng 80 từ tài chính, dòng 90 là lưu chuyển tiền thuần trong kỳ, dòng 101 là tiền đầu kỳ và dòng 103 là tiền cuối kỳ. Không lấy subtotal trước thay đổi vốn lưu động và không dùng phần tiền môi giới/ủy thác của khách hàng để thay cho tiền của công ty.
- Nguồn đã lưu từ danh mục VietstockFinance cho thấy dòng FX không được trình bày riêng trong báo cáo lưu chuyển tiền tệ HCM; vì vậy không tạo `foreign_exchange_effect`.
- Đơn vị nguồn là VND, snapshot quy đổi sang triệu VND bằng cách làm tròn từng dòng về triệu gần nhất. Do làm tròn độc lập, tổng hoặc cầu nối có thể lệch 1 triệu đồng; chấp nhận khi chênh lệch tương đối không vượt 0,01%. Không thay số nguồn để khớp tuyệt đối.
- Ưu tiên số so sánh mới hơn:
  - FY2024 dùng cột so sánh trong BCTC Q4/2025; Q1–Q3/2024 lần lượt được lấy từ cột so sánh trong Q1/Q2/Q3 năm 2025. Các số YTD của 2024 khớp cùng cơ sở so sánh đã chọn.
  - H1/2025 dùng cột so sánh mới hơn trong BCTC Q2/2026: CFO **-4.154.431**, CFI **-9.068**, CFF **3.273.395**, net change **-890.104**, tiền đầu năm **1.963.445**, tiền cuối kỳ **1.073.341 triệu VND**. Cơ sở này thay thế giá trị H1/2025 trước đó trong snapshot (net change -714.404; opening 2.023.945; closing 1.309.541). Không ghi đè mất dấu vết cơ sở cũ.
  - Giá trị quý riêng tính bằng YTD mới của kỳ hiện tại trừ YTD kỳ trước trong cùng năm theo cơ sở đã chọn. Nếu cột so sánh mới hơn làm phát sinh mâu thuẫn giữa báo cáo, ghi residual và trạng thái rà soát; không thêm khoản bù.
- Các báo cáo HCM được lưu ở `reports/raw/HCM/vietstock-hcm-2024-2026-20261019/`. Lượt này dùng sidecar OCR của trang B03(b)a. Công cụ xem PDF trực tiếp không mở được các PDF lớn trong lượt này, nên tất cả trang nguồn vẫn mang trạng thái `ocr_text_reconciled_visual_review_pending`; không tuyên bố đã xác minh hình ảnh trang PDF.

### Ngoại lệ nguồn/basis bắt buộc giữ lại
- **2025-Q2:** YTD H1/2025 từ so sánh Q2/2026 mở đầu năm **1.963.445** và kết thúc **1.073.341**, trong khi Q1/2025 trước đó kết thúc **1.591.074**. Cầu nối quý riêng theo chênh YTD có residual **-60.500 triệu VND** (vượt 0,01%). Đồng thời opening YTD mới khác closing FY2024 **-60.500 triệu VND**. Giữ cột so sánh mới hơn và gắn cờ; không tự sửa Q1/2025.
- **2025-Q3:** YTD 9T/2025 theo báo cáo Q3/2025 có kết thúc **6.709.100**; khi lấy chênh so với H1/2025 đã trình bày lại từ Q2/2026, cầu nối Q3 riêng dư **+60.500 triệu VND** (vượt 0,01%). Đây là mâu thuẫn cơ sở giữa báo cáo, không phải lý do để bịa hoặc cắm số cân bằng.
- **2026-Q2:** YTD H1/2026 tự cân đối theo báo cáo hiện hành với opening **3.381.063**, closing **2.202.389**, net change **-1.178.674 triệu VND**. Tuy nhiên, opening H1/2026 lệch **-320.500 triệu VND** so với closing FY2025 **3.701.563**; cầu nối quý riêng sau chênh YTD dư **-320.499 triệu VND** (relative difference xấp xỉ 12,70%, vượt 0,01%). Giữ nguyên cả hai số của báo cáo, đánh dấu `NEEDS_MANUAL_REVIEW_CROSS_REPORT_BASIS_GT_0_01_PERCENT`, không ép liên tục.
- Regression bổ sung trong `tests/test_cashflow_bridge.py` kiểm tra đủ 10 kỳ, YTD/quarter sums, quý riêng = YTD delta, cầu nối, cơ sở so sánh mới hơn và cả ba ngoại lệ vượt ngưỡng. Sai lệch làm tròn 1 triệu đồng ở những kỳ khác được chấp nhận theo 0,01%.
- Trạng thái HCM: **PASS phép tính và ánh xạ dòng tiền cốt lõi trong các kỳ không có mâu thuẫn basis; NEEDS_MANUAL_REVIEW ở Q2/2025, Q3/2025 và Q2/2026**. Trang PDF trực tiếp chưa được xem nên review hình ảnh còn pending cho cả 10 kỳ; các số giữ trạng thái thận trọng.


## Lượt chuẩn hóa VNDIRECT (VND) — lưu chuyển tiền tệ (2026-10-29)

### Quy tắc ánh xạ cho báo cáo CTCK B03b-CTCK
- Snapshot: `data/financials-VND.json`, 11 kỳ từ 2024-Q1 đến 2026-Q3.
- Đối với báo cáo lưu chuyển tiền tệ của VNDIRECT, dùng đúng các dòng của **công ty**: dòng 60 (lưu chuyển thuần kinh doanh), 70 (lưu chuyển thuần đầu tư), 80 (lưu chuyển thuần tài chính), 90 (tăng/giảm tiền thuần), 101 (tiền đầu kỳ), 103 (tiền cuối kỳ). Không lấy phần riêng "lưu chuyển tiền tệ hoạt động môi giới, ủy thác của khách hàng".
- Báo cáo Q2/Q3 và năm trình bày lưu chuyển tiền **lũy kế từ đầu năm**. Đặt `cashflow_period_basis = year_to_date` cho mọi kỳ. Quý riêng được tính bằng YTD kỳ hiện tại trừ YTD quý trước trong cùng năm; không coi số YTD là số riêng quý.
- Đơn vị trên PDF là VND; snapshot lưu triệu VND, làm tròn từng dòng báo cáo độc lập đến triệu gần nhất. Không ép tổng thành tuyệt đối bằng cách sửa số nguồn. Chấp nhận residual tương đối ≤ 0,01% và lưu residual trong `cashflow_source_reconciliation`.
- Báo cáo không có dòng riêng "điều chỉnh ảnh hưởng tỷ giá" cho cầu nối tiền mặt của công ty; không tạo `foreign_exchange_effect` hoặc `foreign_exchange_effect_ytd`.
- Ưu tiên số so sánh mới hơn khi dòng số và tổng báo cáo có thể đối chiếu nhất quán:
  - Q1/2024: cột so sánh trong Q1/2025.
  - H1/2024: cột so sánh trong Q2/2025 cho CFO/CFI/net/cash; riêng CFF giữ số của báo cáo Q2/2024 vì OCR cột so sánh trong Q2/2025 trả về một giá trị khác 2.000 triệu VND và làm hỏng tổng. Ngoại lệ được giữ để kiểm tra hình ảnh, không thêm khoản cân bằng.
  - 9T/2024: cột so sánh trong Q3/2025.
  - FY2024: cột so sánh trong Q4/2025.
  - Q1/2025: cột so sánh trong Q1/2026.
  - H1/2025: cột so sánh trong Q2/2026.
  - Các kỳ khác dùng cột YTD hiện hành ở báo cáo tương ứng của VietstockFinance.
- Trong lần này, công cụ mở PDF trực tiếp không kết xuất được các PDF dung lượng lớn; số liệu được tái dựng từ sidecar OCR đã lưu, phép đối chiếu dòng/tổng và cầu nối. Không đánh dấu đã xác minh trực quan. Các trang nguồn vẫn mang trạng thái `ocr_text_reconciled_visual_review_pending_pdf_tool_limit`.

### Kết quả kiểm tra VND
- 11/11 kỳ đã được chuẩn hóa về cùng cơ sở YTD; các trường CFO/CFI/CFF/net change và số dư đầu/cuối kỳ được lấy theo dòng nguồn phù hợp. Số quý riêng được tính lại từ YTD.
- Tổng ba luồng tiền và dòng net change, cùng cầu nối tiền đầu/cuối kỳ, có sai lệch làm tròn tương đối ≤ 0,01% ở các kỳ đã có đủ giá trị; không thay số nguồn để khớp.
- Ngoại lệ còn mở: **CFF H1/2024**: OCR cột so sánh trong Q2/2025 tương đương 1.078.401,553 triệu VND; cần xác minh trực quan trước khi dùng. Snapshot giữ 1.076.401,553 triệu VND theo báo cáo Q2/2024 gốc, vì giá trị này khớp CFO/CFI/net/cash bridge; độ lệch của ứng viên so sánh 2.000 triệu VND, tương đối lớn hơn 0,01%.
- Q2/2026 có residual tổng luồng do làm tròn độc lập chỉ **-3 triệu VND** trong snapshot (tương đối dưới 0,01%); được chấp nhận, vẫn giữ residual, không sửa giá trị thành phần.
- Regression được bổ sung trong `tests/test_cashflow_bridge.py`: 11 kỳ, đơn vị/basis, CFO+CFI+CFF, net change, YTD bridge, quarter bridge, quý riêng = chênh YTD, continuity số dư và kiểm soát CFF H1/2024.
- Trạng thái VND: **automation complete; manual-review remaining** cho so sánh CFF H1/2024 vượt 0,01% và trực quan PDF chưa hoàn tất. Chuyển tiếp sang mã kế tiếp được phép; không thay đổi mảng dữ liệu khác.


## Gia cố quy trình hồi quy và bảo toàn trường đã chuẩn hóa — 2026-10-29

### 1. Quy tắc bắt buộc cho bộ kiểm thử
- Trong `tests/test_cashflow_bridge.py`, `if __name__ == "__main__": unittest.main()` phải nằm **sau cùng file**, bên dưới mọi lớp test theo mã chứng khoán. Nếu đặt giữa file, Python chạy test trước khi khai báo các lớp ACB/FPT/SHB/HCM/VND; CI có thể báo xanh nhưng bỏ sót các test được thêm ở cuối file.
- Sau khi di chuyển guard xuống cuối, CI đã thực thi đủ **25 test** trong `python tests/test_cashflow_bridge.py` và đạt **PASS** (run [40735388788](https://github.com/kiemtimem123/so-lieu/actions/runs/40735388788)).
- Trong test, chỉ kiểm tra kiểu số trên các trường số; trường phân loại như `cashflow_period_basis` là chuỗi và phải được kiểm tra riêng, không đưa vào điều kiện `isinstance(value, (int, float))`.

### 2. Không để quy trình OCR ghi đè trường đã chuẩn hóa
- Lượt rà soát 2026-10-29 phát hiện commit làm giàu OCR MBB `8367764` đã để trống một số trường dòng tiền và số dư tiền đã chuẩn hóa, trong khi các trường phi dòng tiền khác vẫn mới hơn.
- Đã khôi phục **chỉ nhóm trường dòng tiền và metadata đối chiếu** của MBB từ snapshot đã qua kiểm định tại commit `694989992688`; giữ các trường phi dòng tiền mới hơn. Không tự tạo giá trị mới, không điều chỉnh số nguồn, không thay đổi các tab/mảng khác.
- Các kiểm thử hiện xác nhận lại MBB đủ ba luồng tiền, net cash change, quý riêng = chênh YTD, cầu nối tiền và residual liên kỳ được ghi lại. Việc khôi phục được ghi tại các trường ghi chú dòng tiền của snapshot MBB.
- Quy tắc chung cho mọi lượt OCR/enrichment: **trước khi ghi snapshot mới, so sánh trường đã chuẩn hóa với phiên bản trước; không ghi `null` hoặc giá trị chưa xác minh đè lên trường có nguồn và đã kiểm định**. Nếu cần cập nhật, phải ghi nhận nguyên nhân, nguồn và kết quả kiểm thử trong cùng commit.

### 3. Chuẩn hóa metadata mâu thuẫn liên kỳ HCM
- Đã bổ sung `selected_ytd_opening_vs_prior_fy_close` cho HCM 2025-Q2 và 2026-Q2, gồm số dư cuối năm trước, số dư đầu YTD từ báo cáo so sánh, residual, tỷ lệ tương đối và cờ rà soát.
- Các residual HCM vượt 0,01% vẫn giữ nguyên và ở trạng thái manual review; đây chỉ là bổ sung truy vết, không thay đổi số liệu tài chính.

### Trạng thái
- Quy tắc chấp nhận residual số học tương đối **≤ 0,01%** tiếp tục có hiệu lực: lưu residual nhưng không sửa số nguồn. Ngoại lệ trên 0,01% và vấn đề OCR/khác kỳ/khác phạm vi phải gắn manual review.
- Mảng đang làm: lưu chuyển tiền tệ. VND đã được chuẩn hóa 11 kỳ; còn mâu thuẫn OCR CFF H1/2024 vượt ngưỡng và rà soát trực quan PDF pending. Mã kế tiếp theo thứ tự danh mục là SHS.


## Lượt chuẩn hóa SHS — lưu chuyển tiền tệ (2026-10-29)

### Ánh xạ nguồn và kỳ
- Snapshot: `data/financials-SHS.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2.
- Đọc BCTC theo mẫu B03b-CTCK của SHS, chỉ lấy dòng tiền của **công ty**: mã 60 (CFO), 70 (CFI), 80 (CFF), 90 (tăng/giảm tiền thuần), 101/102 (tiền đầu kỳ), 103/104 (tiền cuối kỳ). Không lấy phần lưu chuyển tiền môi giới/ủy thác của khách hàng.
- Dòng ảnh hưởng tỷ giá được trình bày nhưng ghi dấu gạch “-”; trường hợp này được chuẩn hóa thành 0 theo dấu gạch nguồn, không suy ra từ cầu nối.
- Đơn vị PDF là VND, snapshot triệu VND; làm tròn mỗi dòng độc lập đến triệu gần nhất. Số quý riêng = YTD quý hiện tại trừ YTD quý trước trong cùng năm, chỉ khi cả hai cơ sở YTD đã được nguồn xác nhận.
- Không thay `financial_line_items_source` chung của snapshot bằng nguồn lựa chọn riêng cho LCTT. Nguồn được chọn, trang, lý do thay thế và các giá trị cũ chỉ ghi trong `cashflow_audit_revision` / `cashflow_source_reconciliation` để không làm sai xuất xứ các trường ngoài LCTT.

### Kiểm tra nguồn trực quan và các ngoại lệ
- **2024-Q1:** dùng cột so sánh Q1/2024 trong BCTC Q1/2025 được liên kết từ VietstockFinance. Trang lưu chuyển tiền đã được xem trực tiếp; CFO YTD -382.576 triệu, CFI -650 triệu, CFF -46.000 triệu, biến động thuần -429.226 triệu, tiền đầu kỳ 851.889 triệu, cuối kỳ 422.664 triệu. Giá trị cũ CFO 443.876 triệu thực chất là lợi nhuận trước thuế trên dòng 01, không phải CFO; được thay bằng dòng 60.
- **2024-Q2:** tổng CFO/CFI/CFF/net từ sidecar ZIP gốc không đọc đủ tin cậy. Cột so sánh H1/2024 trong PDF Q2/2025 đã kiểm tra trực quan nhưng lặp lại số Q1/2024 (tiền cuối kỳ 422.664 triệu), mâu thuẫn với số tiền cuối Q2/2024 OCR từ báo cáo gốc là 971.739 triệu. Không dùng cột so sánh đó để lấp H1/2024; giữ các trường dòng tiền YTD/quý riêng để trống và đặt trạng thái `NEEDS_MANUAL_REVIEW_H1_2024_SOURCE_TOTALS_UNREADABLE`.
- **2024-Q3:** tổng YTD trên sidecar có thể đối chiếu: CFO -1.098.690, CFI -5.707, CFF +692.982, biến động thuần -411.415 triệu; tiền đầu YTD 851.889, cuối YTD 440.474 triệu. Vì H1/2024 vẫn chưa có cơ sở dòng tiền YTD đã xác nhận, không tính quý riêng Q3 bằng cách trừ số liệu không đáng tin. Các trường quý riêng để trống; YTD được giữ và status ghi manual review.
- **2024-Q4:** dùng cột so sánh FY2024 mới hơn từ BCTC Q4/2025, các tổng YTD khớp nhau và cầu nối tiền khớp. So với PDF gốc Q4/2024 đã xem trực tiếp, CFO/CFI/CFF được phân loại khác nhưng biến động tiền thuần và số dư tiền không thay đổi. Chênh lệch tương đối của CFO và đặc biệt CFI lớn hơn 0,01%, vì vậy chọn cột so sánh mới hơn nhưng vẫn gắn manual review; không tạo số cân bằng. Quý riêng Q4 được tính từ YTD FY2024 mới hơn trừ 9T/2024 YTD.
- **2025-Q1 và Q2/2025:** B03b-CTCK Q1/2025 và H1/2025 đã được xem trực tiếp. Đối với H1/2025, so sánh từ BCTC Q2/2026 sau đó đổi CFO/CFI so với báo cáo Q2/2025 gốc nhưng giữ biến động tiền thuần và số dư tiền. Chênh lệch tương đối CFI lớn hơn 0,01%; dùng cơ sở so sánh mới hơn, lưu cả hai bộ số ở metadata và giữ trạng thái manual review. Không ép hai bộ số khớp bằng cách thêm plug.
- **2025-Q3, Q4 và 2026-Q1, Q2:** YTD values lấy từ dòng tổng cuối nhóm trong PDF/ZIP sidecar của báo cáo tương ứng. Các trang ZIP này chưa được xem trực tiếp; trạng thái visual review vẫn được giữ pending. Kiểm tra số học đã thực hiện trên dòng cuối nhóm, lũy kế, số quý riêng, cầu nối tiền và sai lệch tương đối.
- Các residual phát sinh do làm tròn trong các kỳ còn đầy đủ đầu vào đều không quá 0,01% và được chấp nhận mà không sửa số nguồn. Residual 1 triệu đồng được lưu rõ trong metadata; không dùng ngưỡng này để bỏ qua khác biệt nguồn trên 0,01%, lỗi OCR hoặc thiếu cơ sở kỳ.

### Kết quả và trạng thái
- YTD và quý riêng đã chuẩn hóa cho các kỳ có cơ sở nguồn đủ tin cậy; mọi kỳ có đủ bốn thành phần đều khớp CFO+CFI+CFF với net change trong dung sai 0,01% và kiểm tra cầu nối tiền có thể thực hiện đều đạt dung sai.
- Q2/2024 và quý riêng Q3/2024 được chủ động để trống ở phần thiếu bằng chứng; Q4/2024 và H1/2025 vẫn được dùng theo nguồn so sánh mới hơn nhưng giữ cảnh báo thay đổi nguồn vượt 0,01%.
- Bài kiểm thử `SHSCashFlowNormalizationTests` kiểm tra 10 kỳ, mapping CFO không được lấy từ lợi nhuận trước thuế, tách YTD/quarter, cách xử lý các ngoại lệ và ngưỡng tương đối 0,01%.
- Trạng thái: **automation complete; manual-review remaining**. Chuyển sang mã kế tiếp theo thứ tự danh mục là NLG; không thay đổi mảng dữ liệu khác.


## Lượt chuẩn hóa NLG — lưu chuyển tiền tệ (2026-10-29)

### Quy tắc dung sai được áp dụng
- Quy tắc người dùng xác nhận: sai lệch tương đối **≤ 0,01%** được phép chấp nhận khi là sai số làm tròn số học. Mẫu số dùng `max(|actual|, |expected|, 1)`; phần dư và đơn vị vẫn được lưu lại, không sửa số nguồn.
- Ngưỡng này **không** cho phép bỏ qua OCR không khớp, thiếu trang nguồn, sai kỳ/phạm vi, hoặc thay đổi phân loại giữa các báo cáo. Nếu nguồn chưa xác nhận hoặc sai lệch nguồn vượt 0,01%, phải để trống trường không chắc hoặc ghi `NEEDS_MANUAL_REVIEW`; không thêm “plug”.
- Validator đang dùng `RELATIVE_TOLERANCE_PERCENT = 0.01`, `relative_difference_percent()`, `within_relative_tolerance()` và `require_close()`. Bộ test hiện có kiểm tra cả trường hợp bằng/nhỏ hơn và lớn hơn ngưỡng.

### Quy tắc ánh xạ NLG
- Snapshot: `data/financials-NLG.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2; nguồn gốc duy nhất là danh mục VietstockFinance và PDF được liên kết từ đó.
- Với BCTC hợp nhất của NLG, ánh xạ các dòng tổng trong báo cáo lưu chuyển tiền tệ: **20 = CFO**, **30 = CFI**, **40 = CFF**, **50 = biến động tiền thuần**, **60 = tiền đầu kỳ**, **70 = tiền cuối kỳ**. Không lấy dòng 08 “lợi nhuận trước thay đổi vốn lưu động” làm CFO.
- PDF ghi VND, snapshot dùng triệu VND. Mỗi dòng YTD và số dư được làm tròn độc lập đến triệu VND gần nhất. Quý II–IV = YTD quý hiện tại trừ YTD quý trước trong cùng năm; Q1 bằng YTD Q1. Số dư đầu quý riêng lấy từ số dư cuối quý liền trước khi đã có nguồn hợp lệ. NLG không trình bày dòng ảnh hưởng tỷ giá riêng trong các trang LCTT đã đọc; không tự tạo trường FX.
- Kiểm tra bắt buộc: tổng ba luồng tiền YTD và quý riêng so với dòng 50; cầu nối tiền đầu/cuối kỳ; quý riêng so với chênh lệch YTD; liên tục số dư qua ranh giới quý/năm. Residual nội kỳ ≤ 0,01% được chấp nhận, giữ lại trong metadata.

### Đối chiếu nguồn và ngoại lệ
- **2024-Q2 (H1/2024):** đã xem trực tiếp PDF Q2/2024 trang in 6–7 và PDF Q2/2025 trang in 6–7. BCTC Q2/2025 trình bày cột so sánh H1/2024 với CFO **-957.220.112.115 VND**, CFI **230.887.984.065 VND**, CFF **259.630.708.491 VND**, net change **-466.701.419.559 VND**, số dư đầu **2.540.097.046.548 VND**, cuối **2.073.395.626.989 VND**. So với BCTC Q2/2024 gốc, CFO và CFI thay đổi phân loại trên 0,01% nhưng CFF, biến động tiền thuần và số dư tiền được giữ nguyên. Snapshot chọn comparative mới hơn, lưu cả bộ cũ/mới và gắn manual review cho việc phân loại; không “cân” bằng cách đổi dòng khác.
- **2024-Q3:** YTD 9T/2024 lấy từ dòng 20/30/40/50 trong báo cáo Q3/2024. Quý III riêng được dẫn xuất từ YTD 9T trừ H1/2024 comparative mới được chọn ở báo cáo Q2/2025; vì H1 CFO/CFI đã đổi phân loại so với bộ cũ, CFO/CFI quý III riêng chịu ảnh hưởng cơ sở so sánh. Net flow và cầu nối tiền vẫn khớp trong 0,01%; giữ cờ manual review cho sự khác biệt phân loại, không xem phép tính cộng đúng là bằng chứng rằng hai cách phân loại nguồn giống nhau.
- **2024-Q4:** chọn số từ BCTC năm 2024 gốc vì OCR sidecar của cột so sánh FY2024 trong báo cáo Q4/2025 đưa CFO ứng viên **4.225.075.645.565 VND** cùng CFI **1.050.946.776.427 VND**, CFF **627.174.142.918 VND** trong khi dòng 50 là **2.903.196.564.910 VND**. Tổng ba ứng viên vượt net change **3.000.000 triệu VND**; sai lệch rất lớn, không thuộc ngưỡng 0,01%. PDF Q4/2025 không mở được ở công cụ xem ảnh do giới hạn kích thước, vì vậy không đoán chữ số đầu hay thay số gốc. Giữ bộ FY2024 đã cân đối từ báo cáo gốc, kèm ngoại lệ cần xác minh trực quan.
- **2025-Q1 đến 2025-Q4:** các dòng YTD CFO/CFI/CFF/net và số dư đầu/cuối lấy từ BCTC tương ứng. H1/2025 được đối chiếu thêm với cột so sánh trong BCTC Q2/2026 (trang in 6–7), các giá trị H1/2025 khớp và tự cân đối. Các trang chưa được xem trực tiếp vẫn mang trạng thái OCR/pending; bài toán số học khớp không đồng nghĩa đã kiểm tra trực quan tất cả PDF.
- **2026-Q1:** sidecar OCR cho ba luồng lần lượt là CFO **-619.058.317.030 VND**, CFI **-1.148.948.074.666 VND**, CFF **-118.464.195.182 VND**; tổng là **-1.886.470.586.878 VND**, lệch **-100.000.000.000 VND** so với dòng 50 **-1.786.470.586.878 VND** (sai lệch tương đối khoảng 5,30%). Không thể xác định chỉ dựa vào số học dòng nào bị OCR sai. Vì vậy giữ ứng viên trong metadata nhưng để trống ba trường thành phần dòng tiền trên giao diện, đồng thời giữ net change và số dư đầu/cuối vì cầu nối của báo cáo khớp. Không suy ra thành phần để buộc khớp.
- **2026-Q2:** PDF trang in 6–7 đã được xem trực tiếp. H1/2026 CFO **-1.087.390.948.867 VND**, CFI **-1.181.784.099.843 VND**, CFF **-744.326.150.991 VND**, net change **-3.013.501.199.701 VND**, tiền đầu kỳ **6.781.220.022.525 VND**, cuối kỳ **3.767.718.822.824 VND**; tổng và cầu nối YTD khớp. Tuy nhiên tiền đầu YTD thấp hơn số cuối FY2025 **33.084.719.822 VND**, tương đương khoảng **0,485%**, vượt 0,01%. Do Q1/2026 thành phần dòng tiền chưa giải quyết, thành phần quý riêng Q2 để trống; net flow quý riêng được tính bằng chênh lệch YTD nhưng cầu nối quý còn dư **-33.085 triệu VND** (khoảng 0,87% so với số dư cuối quý). Giữ nguyên số nguồn và flag manual review.
- Các trang PDF đã xem trực tiếp trong lượt này: Q2/2024, Q2/2025 và Q2/2026 (trang in 6–7). Những kỳ khác được đánh dấu OCR/pending để không tuyên bố đã xác minh trực quan quá mức.

### Kết quả kiểm định và checkpoint
- Test NLG trong `tests/test_cashflow_bridge.py` kiểm tra 10 kỳ, YTD/quý riêng, cầu nối tiền, quy tắc tương đối 0,01%, thay đổi phân loại H1/2024, comparator FY2024 bị chặn và hai ngoại lệ 2026.
- Kết quả snapshot: các kỳ có đủ thành phần đều thỏa dung sai 0,01% cho tổng dòng tiền và cầu nối; Q1/2026 giữ trống thành phần chưa xác minh, Q2/2026 giữ trống thành phần quý riêng phụ thuộc Q1 chưa xác minh. Không ghi số cân bằng.
- Trạng thái NLG: **tự động hóa được các trường có bằng chứng; manual review còn lại** cho phân loại H1/2024/Q3 riêng, cột so sánh FY2024 bị OCR không khớp, ba thành phần Q1/2026 và liên tục tiền H1/2026.
- Sau khi lưu NLG, mã kế tiếp theo thứ tự cấu hình là **BSR**; tiếp tục trong mảng cashflow, một mã mỗi lượt.


## Lượt chuẩn hóa BSR — lưu chuyển tiền tệ (2026-10-29)

### Nguyên nhân gốc và cơ sở nguồn
- Snapshot `data/financials-BSR.json`: chuẩn hóa 10 kỳ từ 2024-Q1 đến 2026-Q2 từ BCTC hợp nhất được liên kết tại danh mục VietstockFinance BSR.
- Sửa lỗi ánh xạ ở các kỳ còn trống/sai: dùng đúng dòng cuối nhóm lưu chuyển tiền thuần từ hoạt động kinh doanh (mã 20), đầu tư (mã 30), tài chính (mã 40), lưu chuyển tiền thuần trong kỳ (mã 50), tiền đầu kỳ (mã 60), ảnh hưởng tỷ giá (mã 61) và tiền cuối kỳ (mã 70). Không lấy subtotal “lợi nhuận từ hoạt động kinh doanh trước thay đổi vốn lưu động” thay cho CFO.
- Tất cả số nguồn VND được chuyển sang đơn vị snapshot `triệu VND` bằng cách làm tròn đến triệu gần nhất. Quý riêng Q2–Q4 tính bằng YTD hiện tại trừ YTD quý trước trên cùng cơ sở đã chọn; FX riêng quý cũng tính bằng chênh lệch FX YTD. Không dùng công thức để điền những giá trị khi thiếu dòng nguồn hoặc sai phạm vi báo cáo.
- Khi có cột so sánh mới hơn trên VietstockFinance, ưu tiên giá trị đó nhưng giữ nguyên lịch sử nguồn cũ trong `cashflow_audit_revision`. Cụ thể:
  - **H1/2024:** dùng cột so sánh H1/2024 của BCTC Q2/2025 thay vì bộ cũ của BCTC Q2/2024. CFO và CFI khác biệt tương đối trên 0,01%; net change, FX và số dư cuối kỳ vẫn khác biệt trong ngưỡng 0,01%.
  - **FY2024:** dùng cột FY2024 so sánh trong BCTC Q4/2025. CFO và CFF khác biệt phân loại trên 0,01%; net change, CFI, FX và tiền cuối kỳ nằm trong ngưỡng. Hai bộ số vẫn được lưu trong lịch sử; không đổi số gốc để khớp.
  - **H1/2025:** dùng cột so sánh H1/2025 trong BCTC Q2/2026. CFI, CFF và ảnh hưởng tỷ giá khác biệt tương đối trên 0,01%; net change vẫn trong ngưỡng. Cột so sánh được chọn theo quy tắc nguồn mới hơn và có cờ rà soát phân loại nguồn.
- Nguồn gốc cho các kỳ kiểm tra trực quan: Q1/2024; H1/2024 so sánh từ Q2/2025; 9M/2024 so sánh từ Q3/2025; FY2024 so sánh Q4/2025; Q1/2025 so sánh Q1/2026; Q3/2025; FY2025; Q1/2026. H1/2025 so sánh từ Q2/2026 và H1/2026 còn trạng thái OCR đã đối chiếu số học nhưng chờ rà soát trực quan, không tuyên bố đã xem hình ảnh đầy đủ.
- Tiền cuối Q3/2025 được tính từ các số đã có nguồn trong báo cáo: tiền đầu kỳ + biến động tiền thuần + ảnh hưởng tỷ giá. Dòng tiền cuối kỳ trong sidecar OCR bị che/đứt đoạn, nên công thức và trạng thái rà soát được ghi rõ; không dùng giá trị OCR sai `50`.
- Tiền cuối FY2025 **7.625.815,658 triệu VND** so với tiền đầu Q1/2026 **7.625.822,769 triệu VND** lệch xấp xỉ **7,11 triệu VND**, tương đương khoảng **0,000093%**. Được chấp nhận theo ngưỡng tương đối 0,01%, phần dư vẫn được lưu; không đồng bộ số của hai báo cáo.

### Kết quả kiểm tra và trạng thái
- Cả 10/10 kỳ hiện có đủ trường lưu chuyển tiền cốt lõi; các trường được thêm vào `financial_line_items_extracted_fields` và gỡ khỏi danh sách bị loại để tab LCTT có thể hiển thị dữ liệu đã có chứng cứ.
- Kiểm tra tổng CFO+CFI+CFF với net change cho cả quý riêng và YTD, cầu nối tiền mở/đóng kỳ có FX, chênh lệch quý = chênh lệch YTD liên tiếp và chuyển năm Q4→Q1. Các phần dư còn lại đều do làm tròn riêng từng dòng khi đổi VND sang triệu VND; mọi sai lệch số học đều không quá 0,01%.
- Ba tình huống khác biệt phân loại theo nguồn được gắn `NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT`: H1/2024, FY2024 và H1/2025. Sai lệch số học nhỏ không xoá cờ nguồn này. Không chèn “plug” và không dùng dung sai để bỏ qua lỗi OCR, thiếu trang hoặc sai phạm vi hợp nhất.
- Bộ test tái sử dụng `BSRCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py` bao phủ đủ 10 kỳ, đơn vị, nguồn VietstockFinance, allowlist UI, công thức quý/YTD, bridge có FX, comparator history, 3 cờ phân loại nguồn và ngoại lệ liên tục tiền năm mới trong ngưỡng.
- Trạng thái BSR: **chuẩn hóa số liệu và kiểm tra số học hoàn tất; rà soát thủ công còn lại** đối với khác biệt phân loại so sánh H1/2024, FY2024, H1/2025 và các trang PDF còn được gắn `ocr_text_reconciled_visual_review_pending`.
- Mã tiếp theo: tiếp tục trong cùng mảng `cashflow`, một mã mỗi lượt, theo checkpoint đã lưu. Không mở mảng khác trước khi tiến độ dòng tiền được cập nhật.


## Lượt chuẩn hóa VHM — lưu chuyển tiền tệ (2026-10-29)

### Phục hồi dòng tiền và sửa lỗi ánh xạ
- Snapshot: `data/financials-VHM.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2.
- Bốn dòng tổng của BCTC hợp nhất được ánh xạ theo mã báo cáo: 20 = lưu chuyển tiền thuần từ hoạt động kinh doanh; 30 = từ hoạt động đầu tư; 40 = từ hoạt động tài chính; 50 = lưu chuyển tiền thuần trong kỳ. Các dòng 60/70 là tiền đầu/cuối kỳ.
- VHM trình bày đơn vị **triệu VND**; dấu chấm trong số như `68.675.210` là dấu phân cách hàng nghìn, nên giá trị lưu phải là số nguyên `68,675,210` triệu VND, không phải số thập phân `68,675.210`. Giữ đúng thang đo và các chữ số được công bố; không tự chia/multiply số để làm cho cầu nối khớp.
- Q2/2024–Q3/2024 và các báo cáo sau có số lũy kế YTD; số quý riêng được tính từ YTD kỳ hiện tại trừ YTD quý trước cùng năm. Q1 được lấy trực tiếp từ báo cáo quý I.
- Các biểu mẫu đã kiểm tra không trình bày dòng “ảnh hưởng tỷ giá” riêng trong cầu nối tiền. Trường FX được để trống và đánh dấu `not_reported_separately`, không suy ra FX để ép cầu nối.
- H1/2024 sử dụng cột so sánh mới hơn trong BCTC Q2/2025: CFO -10.945.610; CFI +1.139.644; CFF +12.882.761; biến động tiền thuần +3.076.795; tiền cuối kỳ 17.179.976 triệu VND. So với bản Q2/2024 gốc, thành phần CFO/CFI/CFF thay đổi trên 0,01%, nhưng biến động tiền thuần và số dư cuối kỳ đều nằm trong ngưỡng 0,01%. Cả hai bộ số được giữ trong lịch sử nguồn, không tự đồng bộ.
- FY2024 lấy từ cột so sánh của BCTC Q4/2025, nhất quán với BCTC năm 2024 đã kiểm toán; các dòng tổng đã được đối chiếu trực quan.
- H1/2025 sử dụng cột so sánh mới hơn trong BCTC Q2/2026: CFO +41.093.814; CFI -30.084.340; CFF +8.882.295; biến động tiền thuần +19.891.769; tiền cuối kỳ 48.671.892 triệu VND. Các thành phần khác biệt trên 0,01% so với bản gốc Q2/2025; net cash/closing balance khác biệt dưới 0,01%. Giữ hai cơ sở nguồn và gắn cờ rà soát phân loại.
- Q1/2026: tiền cuối FY2025 là 49.948.510 nhưng tiền đầu Q1/2026 được báo cáo là 49.086.598 triệu VND; chênh -861.912 triệu VND, tương đương khoảng 1,7256%, **vượt ngưỡng 0,01%**. Đánh dấu `NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT`; giữ nguyên cả hai số báo cáo, không chèn điều chỉnh.
- **Ngoại lệ nguồn Q2/2026:** ảnh PDF gốc (trang PDF 17, trang in 10) hiển thị dòng 40 “Lưu chuyển tiền thuần từ hoạt động tài chính” **+68.675.210 triệu VND**; trang kế (trang PDF 18, trang in 11) báo dòng 50 biến động tiền thuần **+4.092.385 triệu VND**. Tổng CFO + CFI + CFF theo các dòng in ra là **+3.092.385**, thấp hơn dòng 50 **1.000.000 triệu VND** (lệch tương đối khoảng 24,44%, tương đương một nghìn tỷ VND, vượt xa ngưỡng 0,01%). Trong khi đó dòng 50 khớp chính xác với tiền đầu kỳ + biến động thuần = tiền cuối kỳ (49.086.598 + 4.092.385 = 53.178.983). **Giữ nguyên dòng 40, dòng 50 và số dư tiền đúng như tài liệu; gắn NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT; không sửa CFF thành 69.675.210 và không chèn plug.**
- Danh mục lưu trữ còn có ZIP đính chính BCTC hợp nhất soát xét Q2/2026 (bản đính chính tháng 9/2026), nhưng sidecar đã trích hiện chưa có trang LCTT để xác minh liệu dòng 40 có được sửa. Cần rà soát đúng trang LCTT của bản đính chính trước khi đóng ngoại lệ này.
- Trạng thái trực quan: Q3/2024, FY2024 so sánh Q4/2025, Q1/2025, H1/2025 so sánh Q2/2026, Q3/FY2025, Q1/Q2/2026 đã được xem trang nguồn. Q1/2024 và H1/2024 so sánh Q2/2025 còn chờ xem ảnh trực tiếp; số đã lấy từ sidecar OCR và đối chiếu nội bộ, không tuyên bố đã xác minh hình ảnh đầy đủ.
- Kiểm thử tái sử dụng: `VHMCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py` kiểm tra 10 kỳ, nguồn/VietstockFinance, quý riêng so với chênh lệch YTD, cầu nối tiền, dung sai 0,01%, so sánh H1 mới hơn và ngoại lệ dòng 40 Q2/2026. Ngoại lệ >0,01% được kiểm tra tường minh, không được phép bỏ qua.
- Trạng thái VHM: **chuẩn hóa dữ liệu tự động hoàn tất; cần rà soát thủ công nguồn phân loại H1/2024, H1/2025, trang Q2/2026 đính chính và sai lệch tổng luồng tiền Q2/2026**. Tiếp tục mã tiếp theo cùng mảng dòng tiền sau khi lưu checkpoint.


## Lượt chuẩn hóa TPB — lưu chuyển tiền tệ (2026-10-29)

### Phục hồi dòng tiền cho 10 kỳ
- Snapshot: `data/financials-TPB.json`, kỳ 2024-Q1 đến 2026-Q2; nguồn chính sách là danh mục VietstockFinance `https://finance.vietstock.vn/TPB/tai-tai-lieu.htm?doctype=1`.
- Ánh xạ theo BCTC hợp nhất mẫu B04a/TCTD-HN: lấy **dòng tổng cuối nhóm** CFO, CFI, CFF và “Lưu chuyển tiền thuần trong kỳ”; không lấy subtotal tiền trước biến động tài sản/công nợ. Cả ba luồng tiền và dòng tổng được đọc từ cột YTD của báo cáo; số quý riêng = YTD hiện tại − YTD quý trước trong cùng năm.
- Tiền đầu kỳ, tiền cuối kỳ và ảnh hưởng tỷ giá được đưa vào cầu nối. TPB có dòng FX riêng; FX của quý riêng cũng được tính bằng chênh lệch FX YTD. Tất cả giá trị lưu trong snapshot là số nguyên **triệu VND**, dấu chấm trong tài liệu gốc là phân cách hàng nghìn.
- Các kỳ đã chuẩn hóa gồm đủ ba luồng tiền, biến động tiền thuần, tiền đầu/cuối kỳ và FX; trường nguồn đã được đưa vào `financial_line_items_extracted_fields` và gỡ khỏi danh sách bị loại để giao diện tab LCTT có thể hiển thị.
- Số YTD theo các báo cáo được chọn:
  - 2024-Q1: CFO 9.238.390; CFI -94.074; CFF -5.000; net +9.139.316; open 45.441.602; FX +6.866; close 54.587.784.
  - 2024-Q2/H1: CFO 5.477.002; CFI -223.559; CFF +195.800; net +5.449.243; open 45.441.602; FX 0; close 50.890.845.
  - 2024-Q3/9M: CFO 10.812.233; CFI -255.280; CFF +515.999; net +11.072.952; open 45.441.602; FX +419.867; close 56.934.421.
  - 2024-Q4/FY: CFO 40.343.273; CFI -399.918; CFF +763.682; net +40.707.037; open 45.441.602; FX 0; close 86.148.639.
  - 2025-Q1: CFO -41.476.406; CFI -71.756; CFF -30.000; net -41.578.162; open 86.148.639; FX +210.436; close 44.780.913.
  - 2025-Q2/H1: CFO -19.720.550; CFI -134.135; CFF +984.444; net -18.870.241; open 86.148.639; FX 0; close 67.278.398.
  - 2025-Q3/9M: CFO -1.958.525; CFI -161.466; CFF +2.331.644; net +211.653; open 86.148.639; FX +252.197; close 86.612.489.
  - 2025-Q4/FY: CFO +29.797.620; CFI -1.571.779; CFF +1.372.844; net +29.598.685; open 86.148.639; FX 0; close 115.747.324.
  - 2026-Q1: CFO -7.280.016; CFI -94.901; CFF -192.100; net -7.567.017; open 115.747.324; FX +373.117; close 108.553.424.
  - 2026-Q2/H1: CFO -16.932.973; CFI -127.716; CFF -1.663.300; net -18.723.989; open 115.747.324; FX 0; close 97.023.335.
- H1/2024 is sourced from the later Q2/2025 comparative table. The Q2/2024 source table reported CFI -201.252 vs the later comparative -223.559 million VND, while CFF, net cash movement and closing balance are recorded as matching. The CFI classification delta is greater than 0,01%; keep `NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT` and preserve the two source references.
- FY2024 uses the later Q4/2025 comparative table. Versus the original Q4/2024 report, CFO changes 40.342.756 → 40.343.273, CFI -399.917 → -399.918 and CFF 764.198 → 763.682; net movement remains 40.707.037 and closing cash 86.148.639. The CFF difference 516 million VND is about 0,0675%, above the 0,01% threshold. The newer comparative is selected and the original values kept in `cashflow_audit_revision`; flag for manual review, do not use a plug.
- Visual source pages checked with PDF screenshots: Q1/2025 (including Q1/2024 comparator), Q2/2025 (including H1/2024 comparator), and Q3/2025 (including 9M/2024 comparator). Q4/2025 comparative, FY2025, Q1/2026 and H1/2026 PDFs are marked OCR/source-text reconciled but pending direct visual review because direct PDF fetch exceeded the viewer size limit. Do not claim these pages were visually verified.
- Regression tests: `TPBCashFlowNormalizationTests` in `tests/test_cashflow_bridge.py` validates all 10 periods, YTD component sums, FX-aware cash bridges, quarterly = YTD differences, source reclassification exceptions and visual-review statuses.
- Result before CI: all 10 periods pass all four arithmetic checks exactly: YTD flow sum, standalone quarter flow sum, YTD cash bridge with FX and quarter cash bridge with FX. The H1/2024 and FY2024 source component reclassifications remain manual-review items because they exceed 0,01%; visual review remains pending for the large later reports listed above. No balancing adjustments were inserted.
- Next ticker in this data domain: **VPB**. Continue one ticker at a time.


## Lượt chuẩn hóa VPB — lưu chuyển tiền tệ (2026-10-29)

### Phạm vi và quy tắc nguồn
- Snapshot: `data/financials-VPB.json`, 11 kỳ từ 2024-Q1 đến 2026-Q3. Nguồn tài liệu duy nhất: danh mục VietstockFinance `https://finance.vietstock.vn/VPB/tai-tai-lieu.htm?doctype=1` và PDF/ZIP được liên kết trực tiếp.
- Dùng các dòng tổng cuối của BCTC hợp nhất B04a/TCTD-HN: **CFO = lưu chuyển tiền thuần từ hoạt động kinh doanh**, **CFI = lưu chuyển tiền thuần từ hoạt động đầu tư**, **CFF = lưu chuyển tiền thuần từ hoạt động tài chính**, **net cash flow = lưu chuyển tiền thuần trong kỳ**. Không dùng dòng subtotal “trước những thay đổi về tài sản và nợ phải trả hoạt động” làm CFO.
- Số trong snapshot được lưu bằng **triệu VND**. Các báo cáo VPB trong loạt đang chuẩn hóa không trình bày một dòng ảnh hưởng tỷ giá riêng trong cầu nối tiền; không tự tạo trường FX hoặc tự gán một giá trị FX để ép khớp.
- Số quý II–IV được tính bằng YTD kỳ hiện tại trừ YTD quý trước trong cùng năm. Nếu thiếu căn cứ cho một dòng tổng nguồn, không dùng tổng ba thành phần để thay thế con số nguồn bị OCR sai trên giao diện; chỉ tính trường có đầy đủ đầu vào có bằng chứng và ghi rõ công thức.

### Cơ sở YTD đã chọn và các giá trị đã phục hồi
- **2024-Q1:** chọn cột so sánh Q1/2024 trong báo cáo hợp nhất Q1/2025, thay cho subtotal CFO và CFI bị ánh xạ sai trong snapshot cũ. YTD CFO **-5.358.644**, CFI **-69**, CFF **0**, net **-5.358.713**, tiền đầu **93.667.470**, tiền cuối **88.308.757** triệu VND.
- **H1/2024:** chọn cột so sánh H1/2024 trong BCTC hợp nhất Q2/2025: CFO **16.535.602**, CFI **-565**, CFF **-7.935.139**, net **8.599.898**, tiền đầu **93.667.470**, tiền cuối **102.267.368** triệu VND.
- **9M/2024:** chọn cột so sánh 9M/2024 trong BCTC hợp nhất Q3/2025: CFO **33.481.922**, CFI **1.658**, CFF **-7.935.139**, net **25.548.441**, tiền đầu **93.667.470**, tiền cuối **119.215.911** triệu VND. Số OCR cũ tiền cuối **419.215.911** được sửa theo cột so sánh nguồn mới hơn.
- **FY2024:** dùng BCTC hợp nhất Q4/2024 gốc đã xem trực tiếp trên trang PDF 8–9 (trang in 7–8). CFO **57.316.185**, CFI **-45.039**, CFF **-7.935.832**, net **49.335.314**, tiền đầu **93.667.470**, tiền cuối **143.002.784** triệu VND. Cầu nối trong báo cáo và tổng ba luồng tiền đều khớp.
- **Q1/2025:** dùng các dòng tổng trong báo cáo Q1/2025: CFO **8.550.806**, CFI **-55.847**, CFF **0** (không có nhóm dòng tài chính riêng, và net bằng CFO+CFI), net **8.494.959**, tiền đầu **143.002.784**, tiền cuối **151.497.743** triệu VND. Giá trị tiền đầu kỳ OCR cũ **443.002.784** được sửa về số đúng của nguồn.
- **H1/2025:** dùng cột so sánh H1/2025 trong báo cáo Q2/2026, nhất quán với số nguồn sau này: CFO **23.353.876**, CFI **-29.653**, CFF **-3.968.172**, net **19.356.051**, tiền đầu **143.002.784**, tiền cuối **162.358.835** triệu VND. OCR cũ đọc ứng viên **49.356.051**; không dùng ứng viên này vì cột so sánh Q2/2026 ghi **19.356.051** và tổng ba luồng tiền/cầu nối đều khớp.
- **9M/2025:** CFO **27.397.628**, CFI **-31.788**, CFF **-3.968.172**, net **23.397.668**, tiền đầu **143.002.784**, tiền cuối **166.400.452** triệu VND.
- **FY2025:** CFO **44.532.621**, CFI **-88.786**, CFF **8.650.600** (tăng vốn góp/phát hành cổ phiếu trừ cổ tức đã trả), net **53.094.435**, tiền đầu **143.002.784**, tiền cuối **196.097.219** triệu VND.
- **Q1/2026:** CFO **12.145.698**, CFI **-18.002**, CFF **0** (không có nhóm dòng tài chính riêng; net bằng CFO+CFI), net **12.127.696**, tiền đầu **196.097.219**, tiền cuối **208.224.915** triệu VND.
- **9M/2026:** CFO **46.180.388**, CFI **-11.841.627**, CFF **-3.965.367**, net **30.373.394**, tiền đầu **196.097.219**, tiền cuối **226.470.613** triệu VND. Tổng ba luồng tiền khớp net; cầu nối tiền YTD khớp chính xác.

### Ngoại lệ H1/2026 — giữ để rà soát thủ công
- Sidecar OCR của BCTC hợp nhất Q2/2026 ghi các thành phần YTD CFO **42.064.417**, CFI **-1.149.285**, CFF **-3.965.367** triệu VND; tổng ba thành phần là **36.949.765** triệu VND. Ứng viên OCR cho dòng “lưu chuyển tiền thuần trong kỳ” là **6.949.765** triệu VND, chênh **30.000.000 triệu VND**, tương đương khoảng **81,19%** theo công thức sai lệch tương đối. Giá trị tiền cuối H1/2026 cũng không được sidecar OCR đọc chắc chắn.
- Mức chênh **vượt rất xa ngưỡng 0,01%** mà người dùng cho phép. Không được coi là sai số làm tròn, không tự sửa thành 36.949.765, không chèn khoản bù, và không cho công khai ứng viên net OCR. Snapshot giữ các thành phần có căn cứ, đưa ứng viên 6.949.765 vào `financial_line_items_rejected_values`, để trống `net_cash_change`, `net_cash_change_ytd`, `cash_ending`, `cash_ending_reported_ytd`, đồng thời gắn `NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT`. Cần xem trực tiếp trang PDF/ảnh gốc trước khi đóng ngoại lệ.
- Quý II/2026: các thành phần quý riêng được tính từ hiệu số YTD nguồn của CFO, CFI, CFF (lần lượt **29.918.719**, **-1.131.283**, **-3.965.367** triệu VND), nhưng net cash quý và số dư cuối quý vẫn để trống vì total H1/cash ending chưa xác nhận. Không coi tổng thành phần quý **24.822.069** là số net đã công bố.
- Quý III/2026: các thành phần quý riêng từ hiệu số YTD là CFO **4.115.971**, CFI **-10.692.342**, CFF **0** triệu VND; net riêng **-6.576.371** được tính bằng tổng ba thành phần có nguồn và ghi rõ công thức. Net YTD 9M và cầu nối YTD của báo cáo Q3 khớp. Vì tiền cuối H1/2026 chưa xác minh, `cash_beginning` riêng Q3 và cầu nối tiền quý riêng vẫn để trống/gắn rà soát; không suy ra tiền cuối H1 từ cầu nối để lấp chỗ trống.
- Chỉ Q4/2024 đã được kiểm tra trực quan trang PDF gốc trong lượt này. Các kỳ khác dùng sidecar OCR đã lưu và đối chiếu số học nhưng vẫn gắn trạng thái `ocr_text_reconciled_visual_review_pending`; không tuyên bố đã xem hình ảnh trực tiếp nếu chưa xem.

### Kiểm thử và cách tiếp tục
- Đã thêm `VPBCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py`: 11 kỳ, dòng tổng nguồn, công thức quý/YTD, cầu nối tiền, nguồn comparative mới hơn, allowlist hiển thị, không tự tạo FX và ngoại lệ H1/2026 vượt 0,01%.
- Validator `scripts/validate-bank-reconciliation.py` nhận diện schema `2026-10-26-bank-reconciliation-cashflow-v5` của VPB để đưa các kiểm tra này vào chạy CI.
- Trước CI, 10 kỳ hoàn chỉnh (2024-Q1 đến 2026-Q1 và 2026-Q3 về tổng YTD/các luồng) khớp số học; H1/2026 là ngoại lệ duy nhất có thành phần CFO/CFI/CFF nguồn nhưng dòng net/cash ending chưa được công nhận, vì OCR sai lệch vượt 0,01%.
- Trạng thái: **automation hoàn tất, manual review còn lại cho H1/2026**. Sau khi checkpoint và CI được lưu, mã kế tiếp là **STB**, vẫn trong mảng cashflow và xử lý một mã mỗi lượt.


## Lượt chuẩn hóa STB — lưu chuyển tiền tệ (2026-10-29)

### Áp dụng dung sai tương đối 0,01%
- Quy tắc được áp dụng cho từng đối chiếu số: `abs(actual - expected) / max(abs(actual), abs(expected), 1) × 100`. Độ lệch **≤ 0,01%** được chấp nhận cho đúng phép đối chiếu đó, không cần điều chỉnh số nguồn. Độ lệch **> 0,01%** phải được ghi nhận và rà soát; không được thay số báo cáo hoặc thêm khoản bù để ép khớp.
- Khi kiểm tra số dư tiền, mẫu số của tỷ lệ chênh cầu nối là số dư tiền cuối kỳ được báo cáo (so với số cuối kỳ tính được). Khi so sánh hai phiên bản của một dòng BCTC, mẫu số là giá trị lớn hơn về trị tuyệt đối của chính dòng đó. Hai tỷ lệ khác nhau nên phải lưu riêng: một sai lệch nhỏ so với số dư tiền lớn vẫn có thể là thay đổi lớn tương đối với dòng FX nhỏ.
- Tỷ lệ chênh lệch dùng để quyết định chấp nhận **phép đối chiếu**, không cho phép xóa lịch sử khác biệt nguồn. Nếu một dòng được nguồn sau phân loại lại trên 0,01%, vẫn chọn cơ sở có nguồn phù hợp gần nhất theo quy trình, lưu cả giá trị cũ và mới, và giữ `NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT`.

### Phạm vi và cách chuẩn hóa
- Snapshot: `data/financials-STB.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2. Danh mục nguồn duy nhất: `https://finance.vietstock.vn/STB/tai-tai-lieu.htm?doctype=1`, cùng PDF/ZIP được liên kết tại đó.
- BCTC hợp nhất STB dùng mẫu B04/TCTD hoặc B04a/TCTD-HN. Phải lấy dòng tổng cuối nhóm CFO, CFI, CFF và “Lưu chuyển tiền thuần trong kỳ”, không lấy subtotal trước biến động tài sản và vốn lưu động.
- STB có dòng “Điều chỉnh ảnh hưởng của thay đổi tỷ giá”; trường FX YTD và số FX riêng quý đều được lấy theo báo cáo, với FX quý = FX YTD kỳ hiện tại − FX YTD quý trước. Không mặc định FX bằng 0 và không bỏ dòng này khỏi cầu nối.
- Số quý riêng = YTD kỳ hiện tại − YTD kỳ trước cùng năm cho CFO, CFI, CFF và net cash. Cầu nối tiền riêng quý dùng số cuối quý trước làm số đầu quý; cầu nối YTD dùng số đầu năm theo báo cáo.

### Cơ sở số liệu đã chọn
- **Q1/2024:** dùng cột so sánh Q1/2024 trong BCTC hợp nhất Q1/2025; CFO 12.979.972; CFI -197.483; CFF -2.303.904; net 10.478.585; tiền đầu 70.507.716; FX +65.715; tiền cuối 81.052.016 triệu VND. Các dòng tổng khớp số học.
- **H1/2024:** ưu tiên cột so sánh H1/2024 trong BCTC hợp nhất Q2/2025. CFO 27.113.464; CFI -418.378; CFF -2.267.691; net 24.427.395; tiền đầu 70.507.716; FX -7.606; tiền cuối 94.927.505 triệu VND. So với BCTC Q2/2024 ban đầu, CFO thay đổi +11.679 triệu VND (~0,043%) và CFI thay đổi -11.678 triệu VND (khoảng 2,79% tính theo trị tuyệt đối của dòng CFI), trong khi CFF chỉ khác 1 triệu và net/tiền cuối kỳ không đổi. Hai thay đổi CFO/CFI vượt 0,01%; chọn nguồn so sánh mới hơn nhưng giữ **manual review** và đầy đủ dấu vết cũ/mới.
- **9M/2024:** dùng cột so sánh 9M/2024 trong BCTC hợp nhất Q3/2025. CFO 17.278.651; CFI -625.096; CFF -2.716.339; net 13.937.216; tiền đầu 70.507.716; FX -8.227; tiền cuối 84.438.705 triệu VND. Cột FX mới hơn là -8.227, khác -6.227 ở báo cáo Q3/2024 ban đầu (chênh 2.000 triệu, lớn hơn 0,01% nếu so riêng dòng FX), nên giữ **manual review nguồn FX**. Cầu nối tiền YTD và riêng quý có residual 2.000 triệu VND, tương đương khoảng **0,00237%** của tiền cuối kỳ; residual của cầu nối nằm trong ngưỡng 0,01% và được chấp nhận nguyên trạng, không tạo plug.
- **FY2024:** dùng cột so sánh FY2024 trong BCTC Q4/2025. CFO 38.365.249; CFI -1.007.900; CFF -1.459.275; net 35.898.074; tiền đầu 70.507.716; FX +87.265; tiền cuối 106.493.055 triệu VND. So với bản Q4/2024 gốc, CFO/CFF chênh 1 triệu VND mỗi dòng; tỷ lệ chênh của cả hai dòng đều dưới 0,01%, vì vậy dùng cột so sánh mới hơn và ghi lại giá trị cũ nhưng không nâng thành lỗi trọng yếu.
- **Q1/2025:** dùng cột so sánh Q1/2025 trong BCTC Q1/2026. CFO -4.502.482; CFI -106.676; CFF -1.638.284; net -6.247.442; tiền đầu 106.493.055; FX -10.387; tiền cuối 100.235.226 triệu VND.
- **H1/2025:** dùng cột so sánh H1/2025 trong BCTC Q2/2026. CFO 22.993.304; CFI -295.309; CFF -3.885.533; net 18.812.462; tiền đầu 106.493.055; FX +184.939; tiền cuối 125.490.456 triệu VND. Giá trị CFO/CFI dùng cơ sở sau soát xét so sánh mới hơn, không giữ dòng subtotal CFO 7.716.659 cũ.
- **9M/2025:** CFO 34.871.233; CFI -409.902; CFF -3.386.136; net 31.075.195; tiền đầu 106.493.055; FX +166.291; tiền cuối 137.734.541 triệu VND. Trang 6 PDF (trang in 5) đã được xem trực tiếp: FX là **166.291**, không phải 198.218 như OCR cũ; net, số đầu và số cuối khớp sau khi sửa.
- **FY2025:** CFO 92.478.001; CFI -764.337; CFF -3.818.948; net 87.894.716; tiền đầu 106.493.055; FX +84.812; tiền cuối 194.472.583 triệu VND.
- **Q1/2026:** CFO -58.545.352; CFI -128.122; CFF -24.412; net -58.697.886; tiền đầu 194.472.583; FX +10.352; tiền cuối 135.785.049 triệu VND.
- **H1/2026:** các dòng nguồn hiện có CFO -41.480.644; CFI -47.599; CFF -1.468.762; net -43.097.005; tiền đầu 194.472.583; FX -5.701; tiền cuối 151.369.877 triệu VND. Net và cầu nối tiền khớp, nhưng tổng ba thành phần CFO+CFI+CFF = -42.997.005, lệch **100.000 triệu VND** so với net. Sai lệch là **0,2320%** theo tỷ lệ YTD và khoảng **0,6369%** với tổng luồng quý II riêng, đều lớn hơn 0,01%. Giữ nguyên các ứng viên theo dòng báo cáo và trạng thái **`NEEDS_MANUAL_REVIEW_SOURCE_FLOW_COMPONENT_SUM_GT_0_01_PERCENT`**; không tự sửa thành phần nào, không thay net bằng tổng tự tính, không thêm plug. Cần đối chiếu ảnh PDF gốc để xác định dòng OCR sai trước khi đóng.
  
### Kiểm thử hồi quy
- Bổ sung `STBCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py`, kiểm tra 10 kỳ; nguồn/VietstockFinance; bốn phép kiểm tra YTD/quý riêng/cầu nối YTD/cầu nối quý; FX; quý riêng bằng hiệu số YTD; so sánh sau hơn; lỗi OCR FX 9M/2025; sự khác biệt nguồn H1/2024; và ngoại lệ H1/2026 > 0,01%.
- Tất cả các kỳ STB đều có luồng tiền riêng quý, lũy kế, số đầu/cuối kỳ và FX được ghi nhận, và các trường đã được đưa vào `financial_line_items_extracted_fields` cho giao diện có thể đọc đúng. Mọi residual cầu nối tiền đều không vượt 0,01%; 2026-Q2 là **ngoại lệ duy nhất ở phép tổng ba luồng tiền** vượt 0,01%, được đánh dấu rõ ràng và không bị tính thành PASS.
- Trạng thái tại thời điểm ghi mục STB: **automation hoàn tất; manual review còn lại cho phân loại H1/2024, thay đổi FX nguồn 9M/2024, và tổng luồng tiền H1/2026**. Cập nhật sau đó theo checkpoint: VCB được bỏ qua theo chỉ dẫn trước đó; CTG trở thành mã đủ điều kiện tiếp theo và đã được chuẩn hóa tại mục CTG bên dưới. Sau khi lưu CI/checkpoint CTG, mã tiếp theo là BID trong cùng mảng cashflow.


## Lượt chuẩn hóa CTG — lưu chuyển tiền tệ (2026-10-29)

### Sửa lỗi ánh xạ và phục hồi dữ liệu
- Snapshot: `data/financials-CTG.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2. Nguồn tài liệu duy nhất là danh mục VietstockFinance CTG và các PDF/ZIP hợp nhất liên kết trực tiếp.
- Bộ trích xuất cũ đã dùng nhầm subtotal **“Lưu chuyển tiền thuần từ hoạt động kinh doanh trước thay đổi về tài sản và vốn lưu động”** làm CFO cuối nhóm ở một số kỳ. Quy tắc bắt buộc: lấy dòng tổng cuối nhóm CFO, CFI, CFF và dòng **“Lưu chuyển tiền thuần trong kỳ”**; không dùng subtotal trước biến động tài sản/công nợ.
- Phục hồi đủ bốn dòng YTD CFO/CFI/CFF/net, tiền đầu-cuối YTD và FX cho cả 10 kỳ. Quý riêng = YTD đã chọn của kỳ hiện tại trừ YTD quý trước cùng năm; FX riêng quý cũng tính bằng hiệu YTD. Không suy ra FX khi báo cáo không có dòng tương ứng.
- Cơ sở comparative mới hơn đã chọn: H1/2024 từ Q2/2025; 9M/2024 từ Q3/2025; FY2024 từ Q4/2025; Q1/2025 từ Q1/2026; H1/2025 từ Q2/2026. Lịch sử nguồn cũ/mới được lưu trong `cashflow_audit_revision`; các thay đổi phân loại CFO/CFI lớn hơn 0,01% được gắn manual review, không dùng plug.
- **Q3/2024:** nguồn OCR cũ cho net cash là 99.013.649 triệu VND, nhưng ba dòng cuối nhóm cộng thành 99.913.649; comparative 9M/2024 trong Q3/2025 báo cáo 99.913.649 và khớp cầu nối tiền. Chọn comparative mới hơn, nhưng chưa đóng ngoại lệ cho net-row của báo cáo gốc cho đến khi kiểm tra ảnh trang gốc trực tiếp.
- **Q1/2026:** kiểm tra trực tiếp [PDF Q1/2026 trang in 6–8](https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/CTG_Baocaotaichinh_Q1_2026_Hopnhat.pdf) xác nhận tiền cuối kỳ là **578.995.009 triệu VND**, không phải 578.095.009 do OCR trước đó đọc nhầm chữ số. Sau khi sửa, tiền đầu 451.745.475 + net flow 127.164.150 + FX 85.384 = tiền cuối 578.995.009; cầu nối khớp chính xác. Q2/2026 mở đầu từ số dư này và cầu nối quý riêng cũng khớp; không còn ngoại lệ 900.000 triệu do OCR.
- Các trang đã được xem trực tiếp: comparative FY2024 trong Q4/2025, comparative Q1/2025 trong Q1/2026, báo cáo Q1/2026 và báo cáo H1/2026. Các trang nguồn còn lại được đối chiếu OCR và số học, vẫn được đánh dấu `ocr_text_reconciled_visual_review_pending`; không khẳng định đã xác minh trực quan chúng.

### Kết quả kiểm định
- 10/10 kỳ: CFO + CFI + CFF bằng net cash change ở cấp quý riêng và YTD.
- 10/10 kỳ: cầu nối tiền YTD và quý riêng đều khớp sau khi tính FX; quý riêng khớp hiệu YTD; số dư đầu quý liền trước bằng tiền cuối quý trước, gồm ranh giới FY2024/Q1/2025 và FY2025/Q1/2026.
- Tất cả trường LCTT liên quan được đăng ký trong `financial_line_items_extracted_fields` và gỡ khỏi `financial_line_items_rejected_fields` để giao diện không ẩn dữ liệu đã phục hồi.
- Trạng thái **manual review còn lại**: Q2/2024, Q3/2024, FY2024, H1/2025 và Q3/2025 do khác biệt phân loại nguồn >0,01% hoặc net-row OCR cũ cần xác minh trực quan. Sai lệch số học nội kỳ đã được sửa/xác nhận; không tự thay số báo cáo và không thêm plug.
- Kiểm thử hồi quy tái sử dụng: `CTGCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py`, bao phủ 10 kỳ, YTD/quý, FX-aware cash bridge, nguồn comparative, correction OCR Q1/2026 và các cờ manual review.
- Quy tắc dung sai được áp dụng đúng phạm vi: residual số học tương đối ≤0,01% có thể chấp nhận và vẫn lưu metadata; sự khác nhau của một dòng do nguồn/ phân loại >0,01%, OCR không chắc hoặc thiếu trang vẫn phải rà soát thủ công. Không dùng ngưỡng dung sai để che lỗi OCR.
- Trạng thái CTG: **automation complete; manual-review remaining**. Theo hàng đợi hiện tại, VCB tiếp tục bỏ qua theo chỉ dẫn đã lưu; mã tiếp theo là **BID** trong cùng mảng lưu chuyển tiền tệ.


## Lượt chuẩn hóa BID — lưu chuyển tiền tệ (2026-10-29)

### Phục hồi dòng tiền và nguồn so sánh
- Snapshot: `data/financials-BID.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2. Nguồn được dùng là các báo cáo hợp nhất PDF/ZIP liên kết trong danh mục VietstockFinance của BID.
- Sửa nguyên nhân gốc: các bản ghi cũ có trường trống/bị loại hoặc dùng nhầm dòng **“Lưu chuyển tiền thuần từ hoạt động kinh doanh trước những thay đổi về tài sản và vốn lưu động”** thành CFO cuối nhóm. Quy tắc cố định: chỉ lấy dòng tổng cuối nhóm I (CFO), II (CFI), III (CFF) và IV (net cash change); không dùng subtotal trước thay đổi tài sản/công nợ.
- Khôi phục đủ CFO, CFI, CFF, net cash change, tiền đầu/cuối kỳ cho 10 kỳ. Số quý riêng Q2–Q4 tính bằng YTD kỳ hiện tại trừ YTD quý trước cùng năm; các trường YTD giữ đúng cột lũy kế của nguồn đã chọn.
- Báo cáo BID được kiểm tra trong lượt này không có dòng điều chỉnh ảnh hưởng tỷ giá tách riêng trong LCTT; vì vậy `foreign_exchange_effect` và `foreign_exchange_effect_ytd` để null, không suy diễn 0 hay tự tạo một khoản FX. Phép kiểm tra cầu nối dùng FX bằng 0 chỉ khi trường nguồn không có dòng FX, trong khi metadata vẫn nêu rõ trường chưa được báo cáo.
- Comparative H1/2024 từ Q2/2025 được chọn vì sai khác với báo cáo Q2/2024 cũ đều không quá 0,01%: CFO khoảng 0,00985%, net cash khoảng 0,00996%, số dư cuối kỳ khoảng 0,0017%. Sai khác được chấp nhận và lưu metadata, không sửa số nguồn.
- Comparative FY2024 từ Q4/2025 được chọn để chuẩn hóa Q4/2024. Báo cáo sau thay đổi đáng kể cách phân loại các luồng tiền CFO/CFI/CFF so với bản Q4/2024 cũ; các sai khác vượt 0,01%, nên trạng thái vẫn **NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT**. Hai cơ sở nguồn đều được lưu trong audit metadata.
- Comparative H1/2025 từ Q2/2026 được chọn. CFI đổi từ -869.550 sang -867.517 triệu VND (khoảng 0,234%, vượt ngưỡng); sai khác được giữ để rà soát thủ công. CFO và net/ending chênh trong ngưỡng 0,01%, không được dùng để che việc phân loại CFI đã đổi. Q3/2025 đứng trên cùng cơ sở H1/2025 mới hơn và cũng được đánh dấu cần review.
- Q1/2026 mở đầu bằng 530.277.690 triệu VND, thấp hơn 18.308 triệu so với số cuối FY2025 được chọn là 530.295.998. Sai khác tương đối khoảng 0,00345%, nên nằm trong dung sai 0,01%; giữ nguyên cả hai giá trị đã báo cáo, lưu residual và không đồng bộ cưỡng bức.
- Trạng thái nguồn: sidecar OCR của các PDF/ZIP đã được đối chiếu số học. Một số PDF BID có kích thước vượt khả năng mở trực tiếp của bộ xem trong lượt này; do đó các kỳ đều giữ cờ `ocr_text_reconciled_visual_review_pending`. Không tuyên bố đã xác minh trực quan toàn bộ ảnh trang nguồn.

### Kiểm định và ngoại lệ
- 10/10 kỳ: CFO + CFI + CFF bằng net cash change ở cấp quý riêng và YTD.
- 10/10 kỳ: cầu nối tiền YTD và quý riêng khớp theo số nguồn đã chọn; số quý riêng bằng hiệu YTD; các trường LCTT được đưa vào `financial_line_items_extracted_fields` và gỡ khỏi danh sách trường bị loại để UI không ẩn số đã phục hồi.
- Regression class `BIDCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py` bao phủ 10 kỳ, lũy kế/quý riêng, cầu nối tiền, nguồn comparative, FX để null khi không có dòng và dung sai tương đối 0,01%.
- Cờ manual review chỉ còn cho sai khác nguồn vượt 0,01% (comparative FY2024 và H1/2025). H1/2024 variance đã được chấp nhận vì mỗi residual liên quan không quá 0,01%. Q1/2026 opening-cash residual liên kỳ cũng được chấp nhận trong dung sai. Không có balancing plug.
- Trạng thái BID: **automation normalized; manual review remains for source reclassifications and source-image review**. Dùng mốc checkpoint để tiếp tục sau khi kiểm thử/đóng gói hoàn tất; không chuyển sang miền dữ liệu khác.


## Lượt chuẩn hóa SSI — lưu chuyển tiền tệ (2026-10-29)

### Phục hồi dữ liệu nguồn
- Snapshot: `data/financials-SSI.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2. Nguồn gốc chỉ lấy từ PDF/ZIP hợp nhất trong danh mục VietstockFinance của SSI.
- Trường chính được trích từ các dòng tổng của báo cáo lưu chuyển tiền tệ: dòng 60 = CFO thuần, dòng 70 = CFI thuần, dòng 80 = CFF thuần, dòng 90 = biến động tiền thuần, dòng 101 = tiền và tương đương tiền đầu năm, dòng 103 = tiền và tương đương tiền cuối kỳ. Không dùng dòng 30 “lợi nhuận từ hoạt động kinh doanh trước thay đổi vốn lưu động” làm CFO.
- Q4/2024 được đối chiếu với cột so sánh FY2024 trong BCTC Q4/2025; Q1/2025 với cột so sánh trong BCTC Q1/2026; H1/2025 với cột so sánh trong BCTC Q2/2026. Các dòng tổng LCTT liên quan trùng với cơ sở báo cáo gốc; lịch sử nguồn so sánh vẫn được ghi vào `cashflow_audit_revision`.
- Đơn vị nguồn là VND; snapshot được lưu bằng triệu VND, làm tròn từng dòng về triệu gần nhất. Số quý riêng Q2–Q4 là YTD hiện tại trừ YTD quý trước cùng năm; Q1 = YTD. CAPEX và cổ tức trả cũng được quarterize bằng cùng quy tắc.
- Sai lệch số học sau quy đổi được chấp nhận khi tỷ lệ `abs(actual - expected) / max(abs(actual), abs(expected), 1) × 100` không vượt **0,01%**. Residual và đơn vị vẫn lưu trong `cashflow_source_reconciliation`; không sửa số gốc, không ép cộng tuyệt đối và không chèn “plug”.
- Tất cả 10 kỳ SSI: tổng ba luồng tiền YTD và theo quý, cầu nối tiền YTD và theo quý đều nằm trong ngưỡng 0,01%; số đầu quý bằng số cuối quý trước; số quý riêng khớp chênh lệch YTD. Residual còn lại là số học làm tròn độc lập từ VND sang triệu VND, không phải lý do để thay đổi số nguồn.
- **Quy tắc đặc thù SSI về dòng 102/104:** BCTC SSI hiển thị thêm các dòng “Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ” dưới phần cấu phần tiền đầu kỳ/cuối kỳ. Các dòng đó giải thích chênh lệch giữa tổng tiền và tương đương tiền với hai dòng thành phần, không phải một dòng FX cộng thêm vào dòng 90 để nối số dư tiền. Vì vậy `foreign_exchange_effect` và `foreign_exchange_effect_ytd` trong snapshot được để `null`; các giá trị dòng 102/104 được giữ ở metadata `cash_component_detail_adjustment_line_102_vnd` và `cash_component_detail_adjustment_line_104_vnd`, theo đơn vị VND. Không suy diễn thành một khoản FX cầu nối.
- Dòng 102 của Q1/2024 trong OCR ghi 2.242.128.854 VND, trong khi hiệu giữa số tổng đầu kỳ và hai cấu phần hiện ra khoảng 2.242.128.654 VND: chênh 200 VND, tỷ lệ dưới 0,01%. Giữ nguyên giá trị trích từ dòng nguồn và ghi chú sai số OCR nhỏ; không tự sửa số.
- Trạng thái xác minh: **PASS/ACCEPTED_WITHIN_RELATIVE_TOLERANCE_0_01_PERCENT về phép tính; NEEDS_VISUAL_REVIEW cho toàn bộ trang nguồn trong lượt này**. Dù số học khớp, chưa tuyên bố ảnh PDF từng trang đã được kiểm tra trực quan; trường dữ liệu vẫn ghi rõ trạng thái OCR chờ xác minh hình ảnh.
- Regression mới: `SSICashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py`, kiểm tra 10 kỳ, nguồn/index VietstockFinance, so sánh mới hơn, chênh YTD/quý, hai lớp cầu nối, residual 0,01%, metadata dòng 102/104 và bảo đảm không có balancing plug.


## Lượt chuẩn hóa VDS — lưu chuyển tiền tệ (2026-10-29)

### Sửa ánh xạ dòng tổng và chuẩn hóa 10 kỳ
- Snapshot: `data/financials-VDS.json`, 2024-Q1 đến 2026-Q2. Nguồn duy nhất: báo cáo hợp nhất được lưu từ danh mục VietstockFinance của VDS. Tất cả giá trị snapshot là triệu VND; số nguồn nguyên bản giữ trong metadata và archive PDF/ZIP.
- Dùng đúng dòng tổng cuối mỗi nhóm: dòng 60 CFO thuần, dòng 70 CFI thuần, dòng 80 CFF thuần, dòng 90 biến động tiền thuần, dòng 101 tiền và tương đương tiền đầu năm, dòng 103 cuối kỳ. Không dùng riêng dòng 61 mua sắm TSCĐ làm toàn bộ CFI, cũng không dùng các cấu phần thu/chi vay làm CFF.
- Q1/Q2/Q3/FY2024 đã được so với các cột so sánh trong báo cáo Q1/Q2/Q3/Q4 năm 2025; Q1/2025 và H1/2025 đã so với cột so sánh trong Q1/Q2 năm 2026. Các nguồn mới hơn được ưu tiên khi có; lịch sử nguồn và số gốc cũ được bảo lưu trong `cashflow_audit_revision`.
- **Ngoại lệ nguồn cần rà soát:** cột H1/2024 so sánh trong BCTC Q2/2025 đổi cách phân loại CFI/CFF so với BCTC Q2/2024 gốc. CFI YTD chuyển từ -22.707.469.615 lên -9.707.469.615 VND (khác khoảng 57,25% theo mẫu số lớn hơn); CFF YTD chuyển từ 372.500.000.000 xuống 359.500.000.000 VND (khác khoảng 3,49%). Biến động tiền thuần YTD giữ nguyên -201.926.546.392 VND, và cầu nối số dư tiền vẫn đúng. Chọn cột so sánh mới hơn cho H1/2024 nhưng đánh dấu **NEEDS_MANUAL_REVIEW_SOURCE_RECLASS_GT_0_01_PERCENT** ở Q2/2024.
- Cột so sánh 9M/2024 trong Q3/2025 dùng cơ sở CFI/CFF khác với cơ sở H1/2024 trong Q2/2025. Q3/2024 standalone phải tính bằng YTD 9M đã chọn trừ H1/2024 đã chọn; trường Q3 vì vậy cũng được đánh dấu rà soát thủ công, dù tổng dòng tiền và cầu nối số dư vẫn trong ngưỡng. Không lấy một cột gốc cũ để âm thầm trộn với cột so sánh mới; không chèn khoản cân bằng.
- Q4/2024 FY YTD, Q1/2025 và H1/2025 comparatives từ báo cáo phát hành sau khớp các dòng tổng cốt lõi với báo cáo kỳ gốc. Nguồn được lưu trong metadata để lần rà soát sau có thể truy nguyên.
- Snapshot được chuẩn hóa lại đủ 10 kỳ: dòng tiền quý riêng bằng hiệu YTD liên tiếp; cầu nối tiền đầu/cuối kỳ; nguồn gốc và đơn vị; các trường dữ liệu được thêm vào `financial_line_items_extracted_fields` và gỡ khỏi danh sách bị loại. Các trường `foreign_exchange_effect` và `foreign_exchange_effect_ytd` để `null`, vì dòng FX 102/104 trống trong các trang nguồn LCTT được kiểm tra; không được tự suy diễn.
- Áp dụng ngưỡng tương đối **0,01%** cho residual số học sau khi quy đổi VND sang triệu VND. Residual 1–2 triệu VND tương đối nhỏ được giữ nguyên trong metadata và chấp nhận; số liệu nguồn không bị sửa và không có balancing plug.
- Regression class `VDSCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py` bao phủ 10 kỳ, tổng CFO/CFI/CFF, net cash change, cầu nối tiền YTD/quý, quarter=YTD delta, nguồn comparative mới hơn, ngoại lệ reclassification H1/2024 và dung sai 0,01%.
- Trạng thái cuối: **PASS về phép tính và ánh xạ dòng tổng; NEEDS_MANUAL_REVIEW** cho ngoại lệ reclassification H1/2024/9M2024 và xác minh hình ảnh PDF. Các trang đã trích xuất từ OCR, chưa tuyên bố là đã kiểm tra trực quan đầy đủ.


## Lượt chuẩn hóa KDH — lưu chuyển tiền tệ (2026-10-29)

### Chuẩn hóa đơn vị và dòng tổng
- Snapshot: `data/financials-KDH.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2. Nguồn duy nhất: PDF hợp nhất được liên kết từ danh mục [VietstockFinance KDH](https://finance.vietstock.vn/KDH/tai-tai-lieu.htm?doctype=1).
- Báo cáo gốc ghi đơn vị **Ngàn VND**; snapshot hiển thị **triệu VND**. Quy đổi đúng là chia số nguồn cho 1.000 rồi làm tròn đến triệu gần nhất. Số nguyên nguồn được lưu trong `cashflow_audit_revision.source_values_raw_thousand_vnd`; không nhân/chia theo nhận định cảm tính.
- Lưu chuyển tiền lấy đúng dòng tổng cuối mỗi nhóm: mã 20 (CFO thuần), 30 (CFI thuần), 40 (CFF thuần), 50 (biến động tiền thuần), 60 (tiền đầu kỳ), 70 (tiền cuối kỳ). Không dùng subtotal trước thay đổi vốn lưu động làm CFO.
- Các báo cáo Q2, Q3, Q4 thể hiện số lũy kế; số riêng quý được dẫn xuất bằng YTD hiện tại trừ YTD quý trước trên cùng cơ sở nguồn. Q1 bằng YTD. Trường YTD và quý riêng được đánh dấu trong metadata; không lấy dòng lũy kế làm số quý riêng.
- Khi có comparative mới hơn trong danh mục VietstockFinance, chọn cơ sở comparative mới hơn và giữ nguyên nguồn cũ trong metadata: Q1/2024 lấy cột so sánh Q1/2025; H1/2024 lấy Q2/2025; Q3/2024 lấy Q3/2025; FY2024 lấy Q4/2025; Q1/2025 lấy Q1/2026; H1/2025 lấy Q2/2026.

### Áp dụng ngưỡng tương đối 0,01%
- Dùng `abs(actual - expected) / max(abs(actual), abs(expected), 1) × 100`. Sai lệch số học không vượt **0,01%** được chấp nhận cho phép đối chiếu; residual và đơn vị vẫn lưu, nhưng không sửa số báo cáo và không chèn balancing plug.
- Ngưỡng dung sai **không** che lỗi ánh xạ dòng, khác đơn vị, khác phạm vi hoặc sự thay đổi đáng kể cách phân loại giữa hai báo cáo. Nếu một dòng thành phần được phân loại lại vượt 0,01% so với nguồn trước, chọn nguồn comparative mới hơn nếu đó là cơ sở ưu tiên, lưu cả hai bộ số và giữ cờ manual review dù tổng net/tiền cuối kỳ nằm trong dung sai.

### Ngoại lệ nguồn được lưu
- **H1/2024 (2024-Q2):** comparative Q2/2025 đổi đáng kể phân loại CFO/CFI so với báo cáo gốc Q2/2024; net cash change và tiền cuối kỳ chỉ chênh trong dung sai. Dùng comparative mới hơn nhưng giữ trạng thái manual review.
- **FY2024 (2024-Q4):** comparative Q4/2025 đổi CFO và CFI lớn hơn 0,01% so với báo cáo Q4/2024 gốc; net cash change và tiền cuối kỳ gần như không đổi. Dùng comparative mới hơn và không ép khớp bằng plug.
- **H1/2025 (2025-Q2):** comparative Q2/2026 thay đổi CFO/CFI/CFF/net cash/closing cash hơn 0,01% so với bản H1/2025 gốc. Dùng cơ sở mới hơn, ghi lại nguồn cũ và đánh dấu Q2/Q3/2025 để rà soát nguồn liên kết.
- **2026-Q1:** PDF báo cáo lưu chuyển tiền tệ, trang in 7, trực quan ghi tiền cuối kỳ **3.643.808.683 Ngàn VND**; bảng cân đối kế toán cùng báo cáo ghi tiền và tương đương tiền **3.613.808.683 Ngàn VND**. Sai lệch 30.000.000 Ngàn VND = 30.000 triệu VND, xấp xỉ 0,82%, vượt 0,01%. Giữ nguyên cả hai số và gắn manual review.
- **2026-Q2:** YTD cash bridge trong báo cáo tự cân đối. Cầu nối quý riêng chịu residual khoảng -30.001 triệu VND do khác biệt Q1 nói trên; tỷ lệ vượt 0,01%, không được chỉnh số để che lỗi nguồn. Tiền cuối kỳ tại Q2/2026 trong báo cáo là **2.605.261.249 Ngàn VND**.
- Với 2025-Q3, OCR dòng tiền cuối kỳ khó đọc; dùng số tiền và tương đương tiền 2.378.235.792 Ngàn VND từ dòng tài sản 110 trên bảng cân đối cùng báo cáo và ghi rõ bằng chứng này trong metadata. Cầu nối mở + net khớp.

### Kết quả rà soát
- Cả 10 kỳ: tổng ba dòng CFO+CFI+CFF được đối chiếu với dòng 50 trong ngưỡng tương đối 0,01%; mọi số quý riêng bằng chênh lệch YTD sau quy đổi/rounding.
- Residual do làm tròn 1 triệu VND hoặc ít hơn được chấp nhận khi tỷ lệ không vượt 0,01%; giữ giá trị nguyên nguồn để truy vết.
- Manual review còn lại cho comparative reclassification 2024-Q2, 2024-Q4, 2025-Q2/Q3 và chênh lệch nguồn tiền Q1/Q2-2026. Không có balancing plug hoặc số tự suy diễn.
- Regression class `KDHCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py` kiểm tra 10 kỳ, đơn vị nguồn, công thức YTD/quý, comparative mới hơn, dung sai tương đối 0,01% và hai mâu thuẫn nguồn năm 2026.


## Lượt chuẩn hóa NVL — lưu chuyển tiền tệ (2026-10-29)

### Phạm vi, đơn vị và quy tắc
- Snapshot: `data/financials-NVL.json`, 10 kỳ 2024-Q1 đến 2026-Q2; nguồn chỉ từ danh mục [VietstockFinance NVL](https://finance.vietstock.vn/NVL/tai-tai-lieu.htm?doctype=1) và PDF/ZIP liên kết trong danh mục.
- Đơn vị in trên các báo cáo NVL là **VND** (không phải ngàn VND). Quy đổi snapshot sang **triệu VND** bằng cách chia 1.000.000 và làm tròn gần nhất; số nguyên nguồn VND được lưu ở `cashflow_audit_revision.source_values_raw_vnd`.
- Ánh xạ theo dòng cuối mỗi nhóm: mã 20 CFO, 30 CFI, 40 CFF, 50 biến động tiền thuần, 60 tiền đầu kỳ, 61 ảnh hưởng tỷ giá và 70 tiền cuối kỳ. Không dùng subtotal trước biến động vốn lưu động.
- Quý I bằng YTD. Quý II–IV được tính từ chênh lệch YTD cùng năm; nếu YTD kỳ trước và kỳ này dùng nguồn comparative đã trình bày lại, phải dùng đúng một cơ sở được chọn và lưu cơ sở cũ trong metadata.
- Ngưỡng sai lệch số học: `abs(actual − expected) / max(abs(actual), abs(expected), 1) × 100`. Residual không quá **0,01%** được chấp nhận và vẫn ghi lại; không sửa số báo cáo, không thêm balancing plug. Ngưỡng này không áp dụng để bỏ qua việc phân loại dòng tiền khác nhau trên 0,01% hoặc thay đổi cơ sở số dư tiền giữa các báo cáo.

### Nguồn comparative được ưu tiên
- Q1/2024 dùng cột so sánh Q1/2025 trong BCTC Q1/2025; dòng tổng và số dư khớp với bản Q1/2024 ban đầu.
- H1/2024 dùng cột so sánh từ BCTC Q2/2025. CFO/CFI thay đổi đáng kể và net cash/tiền cuối kỳ chênh trên 0,01% so với bản Q2/2024; chọn comparative mới hơn để chuẩn hóa chuỗi, đồng thời lưu nguyên số cũ và giữ manual review.
- 9M/2024 dùng cột so sánh từ BCTC Q3/2025; các tổng tiền chủ yếu khớp với bản Q3/2024 cũ.
- FY2024 dùng cột so sánh từ BCTC Q4/2025. CFO/CFF được phân loại lại vượt 0,01% so với bản Q4/2024 cũ dù net cash/tiền cuối kỳ gần như không đổi; giữ manual review.
- H1/2025 dùng cột so sánh trong BCTC Q2/2026 thay vì giữ bộ số H1/2025 cũ: net cash và tiền cuối kỳ chênh trên 0,01%, CFO cũng vượt ngưỡng. Số quý riêng Q2/Q3/2025 được dẫn xuất theo chuỗi YTD đã chọn; giữ history của bản cũ.

### Ngoại lệ số dư tiền và cách xử lý
- **FY2025 (2025-Q4):** BCTC Q4/2025 ghi tiền cuối kỳ **4.395.320.969.838 VND**. BCTC Q2/2026 có số so sánh/“trình bày lại” cho tiền đầu năm 2026 là **4.208.770.020.478 VND**. Sai khác khoảng **186,551 tỷ VND**, vượt 0,01%. Không thay thế lặng lẽ số FY2025 đã công bố; giữ cả hai số và đánh dấu manual review.
- **Q4/2025 → Q1/2026:** tiền cuối Q4/2025 là 4.395.320.969.838 VND, tiền đầu Q1/2026 là 4.397.582.643.211 VND; sai khác 2.261.673.373 VND, khoảng 0,051% nên **vượt ngưỡng 0,01%** và cần manual review. Cầu nối nội bộ Q1/2026 vẫn khớp và cùng báo cáo cho tiền cuối kỳ bằng tổng tiền và tương đương tiền trên bảng cân đối.
- **Q2/2026:** BCTC Q2/2026 dùng tiền đầu năm 4.208.770.020.478 VND và tiền cuối kỳ 4.878.790.260.309 VND; cầu nối YTD trong chính báo cáo khớp. Tuy vậy số dư đầu năm được trình bày lại khác với báo cáo Q1/2026; nếu tính net cash Q2 bằng YTD hiện tại trừ YTD Q1, cầu nối quý riêng còn residual khoảng **-188.812 tỷ VND**, vượt 0,01%. Giữ manual review, không “cân” số. Các trang PDF Q1/2026 và Q2/2026 đã được kiểm tra trực quan; Q4/2025 sử dụng sidecar trích xuất từ ZIP và còn chờ kiểm tra ảnh PDF trực tiếp.
- Các sai lệch làm tròn trong snapshot (thường 1–2 triệu VND) ở những kỳ mà tỷ lệ tương đối không vượt 0,01% được chấp nhận; metadata vẫn lưu residual và tỷ lệ.

### Bộ kiểm thử và kết quả trước CI
- `tests/test_cashflow_bridge.py` có thêm `NVLCashFlowNormalizationTests`: 10 kỳ, nguồn VND và quy đổi triệu VND, tổng ba luồng tiền, YTD/quý riêng, cầu nối có ảnh hưởng tỷ giá, comparative đổi cơ sở, và các ngoại lệ tiền Q4/2025–Q2/2026.
- Kiểm tra trước khi ghi snapshot: tổng CFO+CFI+CFF khớp dòng 50 ở **10/10 kỳ trong số liệu nguồn chính xác**; cầu nối YTD ở nguồn gốc khớp; các tổng ở snapshot sau làm tròn nằm trong 0,01%; dữ liệu quý riêng được tính là hiệu YTD liên tiếp.
- Trạng thái NVL sau chuẩn hóa: **đã sửa phần tự động hóa dữ liệu**, còn **NEEDS_MANUAL_REVIEW** cho reclassification H1/2024, FY2024, H1/2025 và cơ sở số dư tiền FY2025/Q1–Q2 2026. Không có giá trị nào được điền bằng ước tính.


## Lượt chuẩn hóa HHV — lưu chuyển tiền tệ (2026-10-29)

### Quy tắc áp dụng
- Snapshot: `data/financials-HHV.json`, 10 kỳ từ 2024-Q1 đến 2026-Q2. Nguồn báo cáo theo quý: [danh mục tài liệu HHV trên VietstockFinance](https://finance.vietstock.vn/HHV/tai-tai-lieu.htm?doctype=1) và các PDF đã được lưu liên kết trực tiếp từ danh mục.
- Báo cáo ghi số tiền theo **VND**; snapshot thống nhất **triệu VND**. Mỗi số tiền YTD được tính bằng số nguồn VND / 1.000.000, làm tròn tới triệu gần nhất; giá trị VND nguồn được giữ nguyên trong `cashflow_audit_revision.source_values_raw_vnd`.
- Ánh xạ đúng dòng cuối nhóm của báo cáo lưu chuyển tiền tệ: mã 20 = CFO, mã 30 = CFI, mã 40 = CFF, mã 50 = biến động tiền thuần, mã 60 = tiền đầu kỳ, mã 61 = ảnh hưởng tỷ giá, mã 70 = tiền cuối kỳ. Không dùng subtotal “lợi nhuận từ hoạt động kinh doanh trước những thay đổi vốn lưu động” thay cho CFO.
- Quý I = YTD quý I. Các quý II–IV = YTD hiện tại trừ YTD quý trước trong cùng năm. Không tự thêm khoản cân bằng để làm khớp cầu nối.
- **Ngưỡng dung sai tương đối 0,01%** là `abs(actual - expected) / max(abs(actual), abs(expected), 1) × 100`. Residual không vượt ngưỡng được chấp nhận, không chặn trạng thái chỉ vì residual số học nhỏ; vẫn giữ residual gốc trong metadata. Quy tắc không cho phép bỏ qua thay đổi phân loại dòng tiền >0,01%, nguồn khác phạm vi hợp nhất, hoặc chênh lệch cơ sở tiền đầu/cuối kỳ >0,01%.

### Các cơ sở nguồn được chọn và ngoại lệ
- **H1/2024 (2024-Q2):** dùng số so sánh mới hơn trong BCTC H1/2025 của VietstockFinance. CFO và CFI thay đổi đáng kể so với báo cáo H1/2024 ban đầu; net cash và tiền cuối kỳ chỉ khác 2.440 VND. Chọn comparative mới hơn cho chuỗi chuẩn hóa nhưng giữ trạng thái manual review do tái phân loại vượt 0,01%.
- **9M/2024 (2024-Q3):** giữ bộ số của báo cáo Q3/2024 vì ba luồng tiền cộng đúng dòng net cash. Sidecar của comparative 9M/2024 ở báo cáo Q3/2025 có tổng thành phần lệch dòng net 10.010.000 VND, khoảng **0,0139%**, vượt 0,01%; giữ cả bộ comparative trong metadata để đối chiếu, không thay thế số đang chọn bằng OCR chưa xác minh.
- **FY2024 (2024-Q4):** dùng comparative FY2024 trong BCTC Q4/2025. Sidecar của báo cáo Q4/2024 gốc có sai lệch khoảng 30 tỷ VND ở tổng luồng tiền/cầu nối; comparative mới hơn có residual tổng CFO+CFI+CFF so với net là 100.000 VND (dưới 0,01%) và cầu nối tiền khớp. Chọn comparative mới hơn nhưng giữ manual review vì chênh lệch nguồn cũ rất lớn và chưa thể xem trực tiếp ảnh PDF qua trình xem nguồn.
- **H1/2025 (2025-Q2):** dùng comparative H1/2025 trong báo cáo Q2/2026. CFO/CFI/CFF khác đáng kể so với H1/2025 ban đầu, trong khi net/tiền cuối kỳ chỉ khác 43.973 VND. Residual thành phần so với net 30.030 VND tương đối dưới 0,01%, được chấp nhận mà không chỉnh số; việc tái phân loại thành phần vẫn mang manual-review flag.
- **Q1/2026 (2026-Q1):** OCR sidecar trang PDF 16–17 ghi line 20/30/40/50 = 415.266.432.734 / -17.037.407.288 / 217.218.045.306 / 615.447.070.752 VND; dòng mở/đóng tiền khớp với line 60/70 của cùng báo cáo và số tiền tương đương tiền trên bảng cân đối.
- **H1/2026 (2026-Q2):** các dòng YTD hiện tại có tổng luồng tiền và cầu nối theo số dư đầu năm của chính báo cáo khớp. Tuy nhiên báo cáo Q2 ghi tiền đầu năm 571.723.614.675 VND, trong khi FY2025 close là 586.763.461.560 VND; residual -15.039.846.885 VND, vượt 0,01%. Khi tính quý riêng từ YTD Q2 trừ YTD Q1, cầu nối Q2 giữa tiền cuối kỳ và tiền cuối Q1 còn residual -15.039.808.794 VND (khoảng 2,96%). Giữ trạng thái `NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS_GT_0_01_PERCENT`, bảo toàn số in trên từng báo cáo; không đồng bộ số đầu kỳ và không chèn plug.

### Giới hạn xác minh nguồn
- Workflow `.github/workflows/extract-hhv-cashflow-pages.yml` đã điền các trang nguồn còn thiếu cho Q1/Q2-2026 vào sidecar OCR. Run [40887648122](https://github.com/kiemtimem123/so-lieu/actions/runs/40887648122) thành công. Trình xem PDF trực tiếp không mở được các PDF này trong phiên làm việc, nên các dòng số HHV được ghi nhận là **OCR sidecar + đối chiếu số học**, không tuyên bố đã xác minh ảnh PDF trực tiếp.
- Regression `HHVCashFlowNormalizationTests` trong `tests/test_cashflow_bridge.py` kiểm tra 10 kỳ, dữ liệu nguồn VND, quy đổi đơn vị, tổng ba nhóm luồng tiền, YTD/quý riêng, cầu nối có tỷ giá, trường hiển thị, comparative history và ngoại lệ cơ sở tiền Q2/2026.
- Trạng thái: **đã chuẩn hóa tự động và kiểm thử số học cho cả 10 kỳ; cần rà soát thủ công các comparative/reclassification và cơ sở tiền đã ghi rõ**. Không có balancing plug.


## Quy tắc vận hành bắt buộc — dung sai 0,01% và checkpoint theo từng mã (2026-10-29)

1. **Dung sai số học:** với phép đối chiếu giữa hai số cùng đơn vị/phạm vi, tính `relative_error_percent = abs(actual - expected) / max(abs(actual), abs(expected), 1) * 100`. Nếu kết quả **≤ 0,01%**, coi là đạt kiểm tra số học; lưu residual và tỷ lệ vào metadata nhưng không chặn mã chỉ vì residual này. Không sửa số báo cáo và không tạo balancing plug.
2. **Không dùng dung sai để che lỗi ngữ nghĩa:** không được bỏ qua sai dòng báo cáo, khác phạm vi hợp nhất/đơn vị/kỳ, thiếu nguồn, số OCR chưa có bằng chứng, hoặc khác cơ sở tiền đầu/cuối kỳ vượt 0,01%. Tái phân loại CFO/CFI/CFF vượt 0,01% phải được ghi nhận riêng dù tổng net cash vẫn nằm trong dung sai.
3. **Checkpoint ngay khi mã đạt:** sau khi một mã đạt đủ kiểm tra bắt buộc của domain hiện tại, ghi trạng thái mã, phạm vi kỳ, nguồn/sidecar, kiểm thử đã chạy, residual còn lại, commit dữ liệu và CI run vào `reports/processing-checkpoint.json` trong cùng điểm lưu công việc. Không đợi hoàn tất cả danh sách mới lưu.
4. **Không nạp lại mã đã đạt:** lần tiếp tục đọc checkpoint trước, bỏ qua dữ liệu/mã đã có trạng thái PASS phù hợp với đúng domain và version quy trình. Chỉ đọc lại khi có yêu cầu sửa cụ thể, nguồn mới, thay đổi chuẩn có ảnh hưởng tới mã đó, hoặc kiểm thử hồi quy phát hiện lỗi. Không tải/parse lại PDF, OCR hoặc snapshot đã đạt chỉ để lặp lại công việc.
5. **Một mã mỗi lượt:** xử lý mã đang hoạt động đến khi đạt hoặc gắn trạng thái manual review có lý do và checkpoint bền vững; sau đó mới chuyển mã kế tiếp. Manual review không được báo là PASS hoàn toàn, nhưng có thể đóng phần tự động nếu dữ liệu và kiểm thử số học đạt.
6. **Trạng thái cần phân biệt:** `PASS` (đủ điều kiện), `PASS_WITHIN_TOLERANCE` (chỉ residual số học ≤0,01%), `NEEDS_MANUAL_REVIEW` (mâu thuẫn nguồn/semantic hoặc bằng chứng còn thiếu), và `FAILED` (lỗi số học vượt dung sai hoặc schema/test lỗi). Ghi rõ điều kiện nào đã đạt và điều kiện nào còn treo.

## Lượt kiểm tra IDC — lưu chuyển tiền tệ (2026-10-30)

- Snapshot: 10 kỳ 2024-Q1 đến 2026-Q2; nguồn duy nhất là danh mục VietstockFinance IDC và PDF/ZIP được liên kết.
- Comparative được ưu tiên theo báo cáo mới hơn: Q1/2024 từ Q1/2025; H1/2024 từ Q2/2025; 9T/2024 từ Q3/2025; FY2024 từ Q4/2025; H1/2025 từ comparative “As restated - Note 41” trong Q2/2026.
- Số nguồn chính xác (VND) lưu trong `cashflow_source_reconciliation.selected_values_raw_vnd`; dữ liệu hiển thị chuẩn hóa về triệu VND. Quý II–IV riêng = YTD kỳ hiện tại trừ YTD kỳ trước cùng năm; Q1 riêng bằng YTD Q1. Đặt `cashflow_period_basis=quarterly_normalized_from_ytd` để giao diện dùng số quý đã chuẩn hóa.
- H1/2025 thay đổi phân loại CFO/CFI: CFO YTD giảm 525.837.250.014 VND và CFI YTD tăng cùng lượng; CFF/net cash/FX không đổi. Giá trị cũ và cơ sở mới đều được lưu.
- Cầu nối FY2024 và FY2025 lệch 28.692.943 VND (dưới dung sai tương đối 0,01%); giữ nguyên residual, không thêm plug.
- Q2/2026 ghi tiền đầu năm 553.943.475.131 VND, trong khi cuối FY2025 là 553.052.678.239 VND; chênh 890.796.892 VND (~0,161%), vượt dung sai. Cầu nối YTD của báo cáo Q2/2026 tự khớp, cầu nối riêng Q2 chưa khớp do cơ sở tiền đầu năm khác FY2025; giữ cả hai số để rà soát.
- Sidecar OCR đã lưu được tái sử dụng; chưa xác minh trực tiếp bằng ảnh PDF. Snapshot hiện có dữ liệu đến Q2/2026. Đã tìm báo cáo Q3/2026 trên danh mục VietstockFinance nhưng trang nguồn không trả nội dung và chưa xác nhận được URL trực tiếp từ danh mục; không kết luận rằng báo cáo Q3 chưa công bố.

## Lượt chuẩn hóa KBC — lưu chuyển tiền tệ (2026-10-30)

- Snapshot có 11 kỳ từ 2024-Q1 đến 2026-Q3. Toàn bộ sidecar OCR được tái sử dụng từ `reports/raw/KBC/auto-kbc-20261021/`; không tải lại hoặc OCR lại.
- Ưu tiên comparative VietstockFinance mới hơn: Q1/2024 từ Q1/2025; H1/2024 từ Q2/2025; 9T/2024 từ Q3/2025; FY2024 từ Q4/2025; Q1/2025 từ Q1/2026; H1/2025 từ comparative Q2/2026; 9T/2025 từ comparative Q3/2026; FY2025 từ Q4/2025 hiện hành.
- Raw source amounts lưu theo VND trong `cashflow_source_reconciliation.selected_values_raw_vnd`; display values chuẩn hóa triệu VND và làm tròn đến 0,001 triệu. Quý II–IV riêng = YTD hiện tại trừ YTD kỳ trước cùng năm. `cashflow_period_basis` tránh để giao diện tính đè các giá trị quý đã chuẩn hóa.
- BCTC KBC không trình bày một dòng FX riêng trong bảng lưu chuyển tiền tệ được đọc từ sidecar; FX fields để null và công thức bridge không cộng FX giả định.
- Q3/2026: dòng 30 CFI OCR đọc thành -518.402.271.256 VND, nhưng dòng chi tiết 21–27 cộng lại -515.402.271.256 VND và khớp dòng 50. Chọn tổng dòng chi tiết, giữ candidate OCR +3.000.000.000 VND sai khác để rà soát ảnh.
- Q4/2025: OCR dòng 70 bị cắt; giữ candidate cuối kỳ 8.386.548,063 triệu VND từ snapshot hiện có, cầu nối FY khớp. Cần xác minh ảnh trực tiếp.
- Q1/2026: tiền đầu kỳ báo cáo 8.368.534,552 triệu VND khác số cuối FY2025 8.386.548,063 triệu VND khoảng -0,2148%, vượt ngưỡng 0,01%. Giữ hai số, không thêm balancing plug.
- Q3/2025: số tiền và tương đương tiền trên Bảng cân đối kế toán lệch số cuối trên BCTT khoảng 299,864 triệu VND (~0,00318%), trong dung sai. Giữ nguyên hai giá trị nguồn.
- Kiểm thử raw-flow sums, cầu nối quý/YTD và quarter=YTD delta được thêm vào `tests/test_cashflow_bridge.py`. Ảnh PDF trực tiếp vẫn pending; các ngoại lệ nêu trên không được xem là đã xác minh trực quan.

## Lượt chuẩn hóa GEG — lưu chuyển tiền tệ (2026-10-30)

- Đã dùng lại sidecar OCR đã lưu trong `reports/raw/GEG/auto-geg-20261021/`; không tải lại hoặc OCR lại.
- Snapshot có 10 kỳ 2024-Q1 đến 2026-Q2. Comparative được chọn theo báo cáo VietstockFinance hiện có: Q1/2024 từ Q1/2025; H1/2024 từ Q2/2025; 9T/2024 từ Q3/2025; FY2024 từ Q4/2025; Q1/2025 từ Q1/2026; H1/2025 từ Q2/2026; các kỳ còn lại từ báo cáo tương ứng.
- Raw source VND được giữ trong `cashflow_source_reconciliation.selected_values_raw_vnd`; display fields chuẩn hóa triệu VND. Quý II–IV riêng được tính từ chênh lệch YTD giữa hai kỳ liền nhau cùng năm. FX lấy từ dòng tỷ giá nguồn.
- H1/2025 dùng báo cáo hợp nhất gốc Q2/2025: CFO 555.421.075.993 VND; CFI 476.067.298.075 VND; CFF -721.712.954.268 VND; net cash +309.775.419.800 VND; FX +56.223.158 VND; đầu kỳ 163.717.707.072 VND; cuối kỳ 473.549.350.030 VND. Báo cáo Q3/2025 và FY2025 cùng chuỗi cơ sở tiền. Comparative H1/2025 trong Q2/2026 có số đầu/cuối và phân loại dòng tiền khác nên được lưu riêng làm nguồn thay thế, không trộn vào chuỗi quý 2025.
- Sau khi thống nhất cơ sở H1/2025 gốc, cầu nối quý Q2/2025 và Q3/2025 đều khớp chính xác trước làm tròn; tổng ba luồng và chênh YTD đều đạt. Q2/2026 là ngoại lệ còn lại: đầu YTD 74.942.444.345 VND khác số cuối Q1/2026 105.856.793.049 VND; YTD bridge khớp nhưng cầu nối quý riêng lệch -11.422.219.803 VND. Giữ cả hai số, không balancing plug.
- Q4/2025: OCR dòng 70 cuối kỳ bị cắt; candidate snapshot được giữ để xem ảnh. Q1/2026 residual bridge +900 VND nằm trong dung sai và được lưu.
- Đã kiểm tra trực tiếp ảnh trang in 4-5 của BCTC Q1/2026 (bao gồm comparative Q1/2025), Q2/2025, Q3/2025 và Q4/2025. Các kỳ 2024 và Q2/2026 vẫn cần rà soát trực quan. Snapshot có dữ liệu đến Q2/2026; chưa xác nhận được URL BCTC Q3/2026 hợp nhất từ danh mục VietstockFinance, không kết luận rằng Q3 chưa công bố.

## Bảo toàn dòng tiền đã kiểm toán nguồn khi enrichment

- Sau khi OCR/enrichment chung và `reconcile_detail_items` hoàn tất, gọi `restore_source_audited_cashflow_fields` cho các kỳ có audit nguồn đầy đủ: catalog VietstockFinance, PDF/sidecar được liên kết, raw VND, `selected_values_not_adjusted_for_tolerance=true` và `no_balancing_plug=true`.
- Khôi phục trường quý, YTD, FX, tiền đầu/cuối theo raw VND; dùng `display_precision` và `display_period_basis` đã lưu. Đưa các trường hợp lệ vào allowlist, gỡ cờ rejected tương ứng, không sửa raw source audit.
- Cầu nối quý vượt 0,01% vẫn hiển thị số nguồn và residual với trạng thái rà soát thủ công; không để quy tắc OCR chung ẩn số dư tiền. Việc khôi phục không đồng nghĩa cầu nối đã đạt.
- Trạng thái xem ảnh PDF độc lập: chỉ kỳ có `visual_review` xác nhận trực quan mới giữ trạng thái đã xác minh ảnh; các kỳ còn lại tiếp tục pending.

## Xác minh trực quan FPT Q4/2024 và bảo vệ chỉ tiêu lõi đã xác minh

- Ảnh PDF BCTC hợp nhất FPT Q4/2024, bảng B02-DN/HN, PDF page 8 (trang in 6), cho thấy PBT cột Quý IV là 2.959.667,491092 triệu VND và LNST là 2.493.502,474938 triệu VND. Snapshot cũ 2.958.495 và 2.500.840 không khớp ảnh nguồn; đã sửa về 2.959.667 và 2.493.502.
- Các trường B02-DN/HN cùng cột Quý IV được điều chỉnh theo ảnh: doanh thu 17.607.818; giá vốn 11.128.844; lãi gộp 6.478.973; doanh thu tài chính 576.398; chi phí tài chính 831.375; chi phí lãi vay 134.854; bán hàng 1.684.354; quản lý 1.735.410; lợi nhuận hoạt động 2.922.047; thuế hiện hành 536.404; thuế hoãn lại -70.239; thuế tổng 466.165; lợi nhuận thuộc cổ đông công ty mẹ 2.086.993; EPS và diluted EPS 994 (đơn vị triệu VND, trừ EPS).
- Tổng thuế khớp PBT-LNST; ROA/ROE tính lại theo LNST riêng quý và bình quân số dư đầu/cuối quý là 14,29% và 28,03%. Giá trị trước sửa được lưu riêng trong `financial_line_items_prior_values` / `financial_line_items_value_corrections`; trường lõi được đánh dấu manual visual và allowlisted.
- Bổ sung safeguard: snapshot các trường lõi đã có `verification_status=verified_manual_visual_reconciliation` trước parser migration; sau enrichment phục hồi nguyên giá trị, source URL, allowlist và trạng thái xác minh nếu parser làm mất/ghi đè. Chỉ phục hồi khi URL nguồn và catalog vẫn y nguyên; không áp lên báo cáo nguồn mới.
- Đã chuyển `unittest.main()` xuống cuối `tests/test_cashflow_bridge.py` để mọi class kiểm thử được đăng ký trước khi runner thực thi.

### Rà soát nguồn bổ sung và thống nhất cơ sở H1/2025 (2026-10-30)

- Ảnh trực tiếp Q2/2025 (trang in 4-5) xác nhận H1/2025 CFO 555.421.075.993; CFI 476.067.298.075; CFF -721.712.954.268; net cash +309.775.419.800; FX +56.223.158; tiền đầu kỳ 163.717.707.072; tiền cuối kỳ 473.549.350.030 VND.
- Ảnh trực tiếp Q3/2025 (trang in 4-5) xác nhận 9T/2025 CFO 856.209.015.015; CFI 244.031.897.120; CFF -857.979.656.903; net cash +242.261.255.232; FX +74.334.749; tiền đầu năm 163.717.707.072; tiền cuối kỳ 406.053.297.053 VND.
- Q2/2025 riêng = H1 gốc trừ Q1/2025; Q3/2025 riêng = 9T/2025 trừ H1 gốc Q2/2025. Cả hai quý có tổng luồng tiền và cầu nối tiền khớp chính xác theo VND trước làm tròn. Comparative H1/2025 trong Q2/2026 vẫn được giữ trong `source_revision.later_comparative_alternative`, không xóa và không dùng trộn vào chuỗi báo cáo gốc 2025.
- Q2/2025 cash trên Bảng cân đối kế toán (473.549 triệu VND) và tiền cuối kỳ BCTT (473.549.350.030 VND) chênh khoảng 350.030 VND, thấp hơn 0,01%; giữ hai giá trị nguồn.
- Đã xem trực tiếp ảnh trang in 4-5 của Q1/2026, Q2/2025, Q3/2025 và Q4/2025. Q2/2026 vẫn cần xác nhận ảnh dòng tiền đầu kỳ; snapshot đã lưu hiện chỉ có đến Q2/2026.

