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
