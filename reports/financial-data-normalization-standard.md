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
