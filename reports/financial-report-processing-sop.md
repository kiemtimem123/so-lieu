# SOP xử lý báo cáo tài chính doanh nghiệp niêm yết

- Phiên bản: 1.18
- Ngày ban hành: 03/11/2026
- Phạm vi: thu thập, đối chiếu, trích xuất, chuẩn hóa, kiểm định và checkpoint dữ liệu BCTC theo mã chứng khoán và kỳ báo cáo.
- Nguyên tắc ưu tiên: đúng nguồn, đúng kỳ, đúng phạm vi hợp nhất/riêng lẻ, giữ dấu và đơn vị gốc, truy vết được mọi giá trị.

## 1. Thứ tự nguồn được phép

1. **Nguồn ưu tiên 1 — VietstockFinance**: trang tài liệu của mã, dạng `https://finance.vietstock.vn/{TICKER}/tai-tai-lieu.htm?doctype=1`, và các PDF được liên kết trực tiếp từ trang đó.
2. **Nguồn ưu tiên 2 — WiData**: trang tài liệu của đúng mã, ví dụ `https://widata.vn/{TICKER}?tab=documents`. Chỉ dùng để đối chiếu hoặc bổ sung trường hợp nguồn 1 thiếu, PDF nguồn 1 không truy xuất được, hoặc trích xuất không rõ.
3. Không sử dụng nguồn thứ ba nếu chưa có chấp thuận rõ ràng của người dùng.

Quy tắc chọn nguồn:
- Ghi lại URL trang danh mục, URL PDF, mã tài liệu, ngày công bố (nếu có), tên file, loại báo cáo, kỳ báo cáo, trạng thái hợp nhất/riêng lẻ, đơn vị và thời điểm tải.
- Không coi hai bản PDF là cùng một tài liệu chỉ vì cùng tên. So sánh tiêu đề, kỳ, loại báo cáo, trang, chữ ký/số hiệu và nội dung.
- Nếu nguồn 1 và nguồn 2 khác nhau: không tự động chọn số lớn hơn/mới hơn. So sánh kỳ, phiên bản/đính chính, phạm vi, đơn vị, cột số liệu, phân loại và dấu. Ghi cả hai giá trị cùng provenance; chọn giá trị chuẩn chỉ khi giải thích được khác biệt. Nếu không phân xử được, đặt PENDING.
- Nguồn 2 không được dùng để âm thầm thay toàn bộ nguồn 1; phải ghi rõ trường nào được đối chiếu/bổ sung và lý do.

## 2. Khóa phạm vi trước khi trích xuất

Với mỗi tài liệu phải xác định:
- Mã chứng khoán và pháp nhân.
- Kỳ: quý riêng lẻ hay năm tài chính; số liệu quý hay lũy kế từ đầu năm (YTD).
- Báo cáo hợp nhất (HN) hay riêng lẻ (RI). Không trộn hai phạm vi trong cùng chuỗi.
- Bộ báo cáo và mã biểu: B01 (tình hình tài chính), B02 (kết quả hoạt động), B03 (lưu chuyển tiền tệ) và thuyết minh khi có.
- Đơn vị nguồn: VND, nghìn VND, triệu VND hoặc đơn vị khác. Không mặc định đơn vị.
- Cột số cuối kỳ/đầu năm; quý hiện tại/quý trước; kỳ này/kỳ trước; lũy kế/kỳ riêng.

Nếu tài liệu không khớp đúng mã, kỳ, loại báo cáo hoặc phạm vi thì dừng, không trích số vào chuỗi chính.

## 3. Lưu trữ nguồn và bằng chứng

Mỗi PDF gốc phải được lưu nguyên trạng, không ghi đè. Lưu thêm:
- URL nguồn và metadata tài liệu.
- Tên file lưu trữ, kích thước và SHA-256 nếu công cụ hiện có hỗ trợ.
- Sidecar trích xuất văn bản/OCR nếu quy trình hiện hành tạo ra; không coi OCR là bằng chứng cuối cùng.
- Số trang PDF và số trang in trên báo cáo (hai số có thể khác nhau).
- Ảnh chụp/render trang cho các dòng trọng yếu, số mờ, số OCR nghi vấn và mọi điểm bất đồng.
- Nhật ký trường dữ liệu: nhãn dòng, mã dòng, số đọc được, cột được chọn, giá trị VND gốc, giá trị chuẩn hóa, trang, nguồn và trạng thái xác minh.

Không tuyên bố đã xem trực quan nếu chỉ có text extraction/OCR. Không tự tạo đường dẫn file, checksum hoặc thông tin chữ ký nếu chưa thực sự đo/kiểm tra.

## 4. Trích xuất và chuẩn hóa

- Trích đúng nhãn và mã dòng trên biểu mẫu; ưu tiên mã dòng và tiêu đề cột, không chỉ dựa vào vị trí OCR.
- Giữ nguyên giá trị VND gốc và dấu âm/dương. Dữ liệu chuẩn hóa sang triệu VND bằng phép chia 1.000.000 khi nguồn là VND.
- Không làm tròn giá trị gốc. Chỉ làm tròn trường chuẩn hóa theo độ chính xác schema hiện hành.
- Không thay số âm bằng trị tuyệt đối; không biến khoản dự phòng âm thành dương.
- Không tự điền số 0 cho ô trống, dấu gạch ngang hoặc dòng không phát sinh nếu chưa xác định quy ước biểu mẫu.
- Không tính ngược một dòng thiếu từ tổng để giả làm số liệu nguồn. Có thể dùng phép tính để kiểm tra, không dùng để bịa giá trị.
- Không gộp số liệu hợp nhất và riêng lẻ; không thay cột đầu năm bằng cột cuối kỳ.
- Giữ provenance của số liệu so sánh được trình bày lại/reclassified trong báo cáo kỳ sau.

## 5. Quy tắc YTD và số liệu quý riêng

BCTC quý thường trình bày cả số quý và số lũy kế; phải xác định đúng cột theo tiêu đề biểu mẫu.
- Nếu cần chuỗi quý riêng mà B03 chỉ có YTD: quý hiện tại = YTD kỳ hiện tại trừ YTD kỳ liền trước, cùng năm tài chính, cùng phạm vi và cùng cơ sở phân loại.
- Không trừ hai số YTD khác cơ sở phân loại. Nếu báo cáo kỳ sau phân loại lại dòng tiền, lưu bản trình bày lại như một basis riêng; không trộn với số YTD của báo cáo kỳ trước.
- Kiểm tra CFO + CFI + CFF = biến động tiền thuần; kiểm tra tiền đầu kỳ + biến động tiền thuần = tiền cuối kỳ, xét đúng phạm vi tiền và tương đương tiền theo biểu mẫu.
- Với Q1, YTD chính là số quý. Với Q4, YTD năm trừ YTD 9 tháng để có Q4 riêng, chỉ khi cùng basis.

## 6. Kiểm định bắt buộc

### 6.1 B01 — tình hình tài chính
- Tổng tài sản = tổng nợ phải trả + vốn chủ sở hữu.
- Tổng tài sản = tài sản ngắn hạn + tài sản dài hạn.
- Kiểm tra các tổng phụ trọng yếu với các dòng thành phần khi có đủ dòng.
- Kiểm tra số cuối kỳ/đầu năm đúng cột và đúng dấu.

### 6.2 B02 — kết quả hoạt động
- Lợi nhuận trước thuế, chi phí thuế và lợi nhuận sau thuế phải khớp theo đúng dấu và cách trình bày của biểu mẫu.
- LNST hợp nhất = LNST thuộc cổ đông công ty mẹ + lợi ích cổ đông không kiểm soát.
- Tổng doanh thu/chi phí chi tiết chỉ PASS khi các dòng thành phần được xác định đủ và cùng cột.
- Không gán một số OCR vào cột quý chỉ vì nó làm tổng khớp. Nếu cột không rõ, để PENDING.

### 6.3 B03 — lưu chuyển tiền tệ
- Kiểm tra tổng CFO, CFI, CFF, biến động tiền thuần và tiền đầu/cuối kỳ.
- Kiểm tra số lũy kế và phép trừ ra quý riêng.
- Ghi nhận phân loại lại giữa các kỳ; chỉ so sánh cùng basis.

### 6.4 Dung sai
- Dung sai tối đa 0,01% chỉ dùng cho chênh lệch làm tròn có thể giải thích, không dùng để bỏ qua sai lệch thực chất.
- Ưu tiên kiểm tra số VND nguyên trước khi xem số đã chuẩn hóa.
- Chênh lệch 1 VND có thể ghi nhận là làm tròn nếu các phép tính và trình bày nguồn chứng minh điều đó.
- Nếu vượt dung sai hoặc không giải thích được: PENDING hoặc FAIL, không tự cân chỉnh.

## 7. Trạng thái xác minh

- **PASS**: nguồn đúng; dòng/cột/đơn vị xác định; giá trị có bằng chứng; các kiểm tra bắt buộc đạt hoặc sai lệch nằm trong dung sai có giải thích.
- **PENDING**: thiếu trang/ảnh, OCR không rõ, chưa xác định cột, nguồn phụ chưa truy xuất được, phân loại dòng tiền chưa đồng nhất, hoặc còn bất kỳ điểm trọng yếu chưa phân xử.
- **FAIL**: sai mã/kỳ/phạm vi, số liệu mâu thuẫn không thể hòa giải, tổng không cân đối vượt dung sai, hoặc provenance không đủ để xác định nguồn.
- Một kỳ chỉ **COMPLETE** khi B01/B02/B03 trọng yếu đã PASS, các trường bắt buộc trong schema có nguồn rõ, các dòng chi tiết được yêu cầu đã kiểm tra, và không còn PENDING trọng yếu.
- Không dùng trạng thái “đã xử lý” thay cho “đã xác minh”. Không đánh dấu hoàn tất tự động khi còn PENDING.

## 8. Quy trình làm việc tuần tự

1. Đọc checkpoint và xác định mã/kỳ tiếp tục; không chạy lại kỳ đã hoàn tất nếu không có mâu thuẫn mới.
2. Mở trang VietstockFinance của mã, lập danh sách PDF đúng kỳ; tải PDF hợp nhất/riêng lẻ riêng biệt theo phạm vi dự án.
3. Nếu PDF nguồn 1 thiếu/không truy xuất/không đọc được, thử đúng tài liệu tương ứng trên WiData. Ghi lý do sử dụng nguồn 2.
4. Xác nhận tiêu đề, kỳ, phạm vi, đơn vị và trang trước khi trích xuất.
5. Trích B01, B02, B03; lưu số VND gốc, số chuẩn hóa và provenance từng trường.
6. Đối chiếu OCR/text với ảnh trang. Bắt buộc xem ảnh trực tiếp khi OCR không chắc, cột gần nhau, số âm, số có dấu chấm/phẩy khó đọc hoặc kiểm tra tổng bị lệch.
7. Chạy kiểm định B01/B02/B03 và phép tính YTD→quý trên cùng basis.
8. Ghi mọi chênh lệch và phương án xử lý. Không sửa số nguồn để làm đẹp phép cân đối.
9. Khi kỳ đạt COMPLETE, cập nhật dữ liệu và checkpoint ngay, commit và xác nhận commit; sau đó chuyển kỳ kế tiếp.
10. Nếu PENDING/FAIL, lưu checkpoint ngay tại kỳ đó, liệt kê chính xác bằng chứng cần bổ sung, không chuyển sang kỳ tiếp theo.
11. Chỉ chuyển mã tiếp theo sau khi các kỳ yêu cầu của mã hiện tại đạt tiêu chí hoàn tất theo thứ tự đã giao.

## 9. Nội dung checkpoint tối thiểu

Mỗi mã/kỳ cần lưu:
- status, period, ticker, source priority, document ID, index URL, PDF URL, archive path.
- report scope (HN/RI), unit, report period, YTD/quarter basis.
- các statement đã trích và đã xem ảnh; số trang PDF và trang in.
- trạng thái kiểm định B01/B02/B03, doanh thu/chi phí chi tiết, dòng tiền và các phép cầu nối.
- danh sách trường sửa, giá trị cũ/mới, lý do, nguồn, trang và bằng chứng.
- các issue PENDING/FAIL; bước tiếp theo cụ thể.
- data commit và checkpoint commit gần nhất.
- cờ doNotRepeatCoreExtraction chỉ bật khi dữ liệu cốt lõi đã trích đầy đủ; cờ này không có nghĩa là visual review đã xong.

## 10. Trạng thái hiện tại: VDS đã qua Q4/2025, tiếp tục GAS

Người dùng đã chỉ đạo **tiếp tục, không dừng toàn bộ tiến độ vì các ngoại lệ PENDING**. Do đó, ghi nhận từng ngoại lệ riêng và tiếp tục sang kỳ/mã kế tiếp; không đổi trạng thái PENDING thành PASS, không đưa số chưa xác minh vào chuỗi được gắn verified, và không sửa các giá trị nguồn đã lưu.

### 10.1 VDS Q1–Q4/2024 và Q1/2025
- Q1–Q4/2024 đã đóng; không trích xuất lại hoặc xem lại ảnh nếu không có mâu thuẫn mới.
- Q1/2025: VietstockFinance document ID 504544, PDF hợp nhất gốc, B01 PDF trang 6–8 (trang in 1–3), B02 PDF trang 11–13 (trang in 6–8), B03 PDF trang 14–16 (trang in 9–11). Các kiểm tra cốt lõi PASS. Data commit `1ed4ef951122aa1b2060d0b795462c2be9521345`. Không lặp lại trích xuất lõi/visual review.

### 10.2 VDS Q2/2025 — ngoại lệ phân bổ LNST mẹ/NCI được giữ riêng
- Nguồn VietstockFinance document ID **513947**, báo cáo hợp nhất, đơn vị VND; PDF gốc lưu `reports/raw/VDS/auto-vds-20261021/69d4862950596830.pdf`. B01/B02/B03 đã xem trực tiếp.
- Q2 riêng: doanh thu **180.998.605.171 VND**; chi phí hoạt động **160.666.996.283 VND**; PBT **-17.442.687.286 VND**; thuế **-6.248.781.619 VND**; PAT **-11.193.905.667 VND**; parent PAT **-9.900.252.664 VND**; NCI **-1.293.653.003 VND**; EPS **-41**.
- B03 H1 YTD gốc: CFO **423.813.880.703 VND**; CFI **-766.006.221.613 VND**; CFF **424.400.000.000 VND**; net change **82.207.659.090 VND**; opening cash **1.207.137.419.234 VND**; closing cash **1.289.345.078.324 VND**. Q2 riêng sau khi trừ Q1 YTD: CFO **977.015.279.251 VND**; CFI **-844.021.190.816 VND**; CFF **492.600.000.000 VND**; net change **625.594.088.435 VND**; cash bridge exact.
- Ngoại lệ: Q2 H1 YTD parent **8.071.151.977 VND**, NCI **-252.715.388 VND**, PAT **7.818.436.589 VND**. Trừ Q2 riêng ra Q1 implied parent **17.971.404.641 VND**, NCI **1.040.937.615 VND**. So với Q1 PDF gốc parent **19.089.097.924 VND**, NCI **-76.755.668 VND**, chênh phân bổ **1.117.693.283 VND** từ parent sang NCI; PAT không đổi.
- Q3/2025 9M YTD trừ Q3 riêng xác nhận chính xác Q2 H1 allocation. Ngoại lệ chỉ còn Q1 original B02 so với H1 basis; không sửa Q1 gốc, không tạo plug.

### 10.3 VDS Q3/2025 — core PASS, chi tiết doanh thu còn PENDING
- Nguồn VietstockFinance document ID **523128**, PDF hợp nhất `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%203/VDS_Baocaotaichinh_Q3_2025_Hopnhat.pdf`, lưu tại `reports/raw/VDS/auto-vds-20261021/bd7db8914d33e414.pdf` (50 trang).
- B01 trang in 1–3; B02 trang in 6–8; B03 trang in 9–11 đã được xem trực tiếp.
- B01 tổng tài sản **7.732.966.527.561 VND** = nợ **4.578.708.861.227 VND** + vốn chủ **3.154.257.666.334 VND**; current assets **6.530.500.802.868 VND** + non-current **1.202.465.724.693 VND**.
- B02: revenue row20 **469.935.413.540 VND**; expense row40 **106.328.748.769 VND**; PBT **325.846.951.359 VND**; tax **61.589.855.072 VND**; PAT **264.257.096.287 VND**; parent **261.233.437.741 VND**; NCI **3.023.658.546 VND**; EPS **960**. Expense row23.3 AFS fair-value loss **45.714.000 VND** đã bổ sung; expense detail sum exact.
- Revenue row 1.8 candidate OCR **881.819.860 VND** không khớp tổng khi ghép với các cấu phần còn lại. Nếu để null, known components còn thiếu **90.000.000 VND**, residual **0,01915%** > 0,01%. Vì vậy giữ `broker_advisory_revenue=null`; không gán OCR candidate, không plug.
- B03 9M YTD: CFO **-790.384.880.004 VND**; CFI **-864.912.269.435 VND**; CFF **1.036.412.000.000 VND**; net change **-618.885.149.439 VND**; opening **1.207.137.419.234 VND**, closing **588.252.269.795 VND**. Q3 riêng: CFO **-1.214.198.760.707 VND**, CFI **-98.906.047.822 VND**, CFF **612.012.000.000 VND**, net change **-701.092.808.529 VND**; opening **1.289.345.078.324 VND**, closing **588.252.269.795 VND**. Flow and cash bridge exact.
- Q3 YTD less Q3 quarter confirms Q2 H1 parent/NCI/PAT exactly. Q1 original allocation difference remains a separate PENDING issue. Data commit `9aff12e4dda7c4e2b83c2652e432d93307e07070`.

### 10.4 VDS Q4/2025 — số lõi/text bridge đã đối chiếu, visual và expense detail còn PENDING
- Nguồn: VietstockFinance document ID **530626**, PDF hợp nhất, công bố **30/01/2026**; PDF gốc `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%204/VDS_Baocaotaichinh_Q4_2025_Hopnhat.pdf`, archive `reports/raw/VDS/auto-vds-20261021/d2252c9c1aaafbaf.pdf`, sidecar `.pdf.extracted.json`; 50 trang.
- Lưu ý: endpoint PDF gốc và bản archive không render được ảnh trong phiên xử lý; đã dùng text/OCR sidecar và cross-check với Q3/2025 YTD. **Không đánh dấu đã visual verified.**
- B01 raw VND: total assets **8.121.452.969.623** = current assets **6.925.802.937.636** + noncurrent **1.195.650.031.987**; liabilities **5.022.323.459.557** = current **4.998.480.395.596** + long-term **23.843.063.961**; equity **3.099.129.510.066**. Assets = liabilities + equity; residuals 0.
- B02 Q4 riêng: revenue row20 **221.975.460.374 VND**; total operating expenses row40 **162.390.566.550 VND**; PBT **15.744.157.121 VND**; income tax **5.651.950.112 VND**; PAT **10.092.207.009 VND**; parent PAT **13.821.476.572 VND**; NCI **-3.729.269.563 VND**; EPS **51**.
- Các tổng B02 trên khớp chính xác khi tính từ FY2025 YTD trừ 9M/2025 YTD trong báo cáo Q3: revenue **221.975.460.374**, expenses **162.390.566.550**, PBT **15.744.157.121**, tax **5.651.950.112**, PAT **10.092.207.009**, parent **13.821.476.572**, NCI **-3.729.269.563**; residuals 0. Revenue identifiable components current Q4 sum đúng row20 khi row 1.8 current Q4 để null; các giá trị 642.692.824 và 881.819.860 trong OCR là các cột comparative/YTD, không gán vào current Q4.
- Expense components chưa đủ rõ trong OCR: row24, row29, row30, row23.3 còn PENDING. Không sử dụng phần chênh tổng để tự điền. Total expenses vẫn được lưu theo row40 gốc; các detail field không chắc giữ null.
- B03 FY2025 YTD raw VND: CFO **-850.325.354.079**; CFI **-824.472.465.903**; CFF **1.464.636.000.000**; net change **-210.161.819.982**; opening cash **1.207.137.419.234**; closing cash **996.975.599.252**. Q4 riêng = FY2025 YTD less Q3 YTD: CFO **-59.940.474.075**; CFI **40.439.803.532**; CFF **428.224.000.000**; net change **408.723.329.457**; opening **588.252.269.795**; closing **996.975.599.252**. Flow and cash bridge residuals 0. B03 row 76 blank → dividends paid null. FX bridge blank → null.
- ROA **0,51%**, ROE **1,29%**, theo PAT quý riêng / bình quân đầu-cuối kỳ × 4 × 100.
- Data commit `4019e204adc2a4c2a18a74d5252436c1fa4cce88`; status `pending_visual_source_review_and_expense_detail`.

### 10.5 Quy tắc tiếp tục
- Các PENDING Q2/2025 parent/NCI, Q3/2025 row1.8 và Q4/2025 visual/expense details được giữ nguyên, có số liệu/nguồn/trạng thái riêng. Không dùng chúng làm số verified/complete.
- Người dùng đã yêu cầu tiếp tục; vì vậy sau khi lưu Q4/2025 ở trạng thái PENDING, chuyển sang mã tiếp theo **GAS** để xử lý các kỳ terminal/manual review từ archive VietstockFinance. Không chạy lại OCR đại trà cho 10 kỳ GAS; xử lý từng ngoại lệ đã được ghi trong checkpoint.
- Ưu tiên GAS Q4/2024 (thiếu tổng nợ), GAS Q4/2025 (thiếu tổng nợ/vốn), GAS Q1/2026 (thiếu tổng B01 và các dòng cashflow); các kỳ còn lại chỉ mở lại khi có lý do cụ thể.

### 10.6 GAS Q4/2024 — total liabilities giữ PENDING, tiếp tục Q4/2025

- Nguồn: VietstockFinance document ID **490581**, BCTC hợp nhất, đơn vị VND; PDF gốc `https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%204/GAS_Baocaotaichinh_Q4_2024_Hopnhat.pdf`; archive `reports/raw/GAS/auto-gas-20261021/7fa3b1653ff606d1.pdf`; sidecar `.pdf.extracted.json`; 75 trang.
- PDF gốc không render được trong phiên do endpoint trả lỗi Content-Length quá lớn; không có trang ảnh B01 để kiểm tra trực quan. Chỉ dùng text/OCR sidecar; không đánh dấu visual verified.
- B01 sidecar trang PDF 4–5 (trang in 1–2): tổng tài sản **81.893.564.503.501 VND**; vốn chủ **61.570.995.265.636 VND**. Dòng row300 “Nợ phải trả” OCR bị cắt sau chuỗi `2032256923781`, không có đủ chữ số để xác định số chính xác; `total_liabilities` giữ `null`. Không tính ngược từ tổng tài sản trừ vốn chủ.
- B02 sidecar trang PDF 6 (trang in 5): doanh thu **34.960.846.410.089 VND**; PBT **2.558.297.020.087 VND**; thuế hiện hành **498.141.880.056 VND**; thuế hoãn lại **7.816.140.590 VND**; tổng thuế **505.958.020.646 VND**; PAT **2.052.338.999.441 VND**; parent PAT **2.044.102.438.055 VND**; NCI **8.236.561.386 VND**; EPS **408**. PBT−thuế=PAT và parent+NCI=PAT, residual 0.
- Các trường chi phí tài chính **419.753.041.491 VND**, chi phí tài chính **140.949.317.288 VND**, lãi vay **5.722.032.723 VND**, chi phí bán hàng **668.833.753.996 VND**, chi phí quản lý **1.097.693.949.210 VND** đã được giữ theo OCR rõ trong sidecar; vẫn chờ visual review.
- B03 sidecar page 7 (trang in 6) OCR quá méo, các cấu phần CFO/CFI/CFF không đủ tin cậy; giữ null.
- Cross-check được phép từ VietstockFinance Q1/2025 document ID **504411**, B01 printed page 2, cột đầu năm 31/12/2024: total assets **81.854.881.408.158 VND**, total liabilities **20.283.886.142.528 VND**, equity **61.570.995.265.630 VND**. Đây là số comparative được trình bày trong báo cáo sau, không giống số gốc Q4/2024: tổng tài sản khác **-38.683.095.343 VND**, vốn chủ khác **-6 VND**; vì vậy không tự động ghi đè Q4/2024 hoặc dùng cột comparative để lấp total liabilities Q4. Ghi nhận đây là khác biệt comparative/re-presentation chờ giải thích.
- Đã thử nguồn phụ được duyệt WiData `https://widata.vn/GAS?tab=documents`, nhưng trang không truy cập được qua bộ đọc hiện tại; không sao chép giá trị WiData.
- Trạng thái Q4/2024: B02 profit bridge PASS; B01 total assets/equity có source text; total liabilities PENDING do row300 truncated; visual B01/B02/B03 PENDING; cashflow components PENDING. Data commit `a996f3fa119e9ecc98ac29c35f66bbc1c0cb790c`.
- Theo chỉ đạo tiếp tục của người dùng, không dừng tiến độ tại Q4/2024. Kỳ tiếp theo: **GAS Q4/2025**, tiếp tục kiểm tra nợ/vốn từ báo cáo gốc và sidecar; bảo toàn ngoại lệ Q4/2024.

### 10.7 GAS Q4/2025 — B02 PASS theo source text; B01 liability/equity và visual PENDING

- Nguồn: VietstockFinance document ID **531505**, PDF hợp nhất `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%204/GAS_Baocaotaichinh_Q4_2025_Hopnhat.pdf`; archive `reports/raw/GAS/auto-gas-20261021/d93ac1474c125a66.pdf`; sidecar `.pdf.extracted.json`; 76 trang.
- PDF gốc chưa render được ảnh; B01/B02/B03 hiện chỉ đối chiếu text/OCR sidecar. Không gắn cờ visual verified.
- B01 trang in 1 (sidecar page 4): total assets **93.531.511.866.676 VND**; current assets **69.861.417.011.215 VND**. B01 trang in 2 (sidecar page 5) OCR được các cấu phần tài sản/nợ/vốn nhưng dòng tổng nợ row300 và tổng vốn row400 bị lệch nhãn/cột; không thể xác định dứt khoát. `total_liabilities=null`, `equity=null`. Không suy ngược từ tổng tài sản hoặc tổng nguồn vốn.
- B02 source text Q4 riêng: revenue **43.683.070.609.001 VND**, COGS **39.890.266.518.331**, gross profit **3.792.804.090.670**, financial income **428.311.439.319**, financial expense **82.785.588.700**, associate profit **19.038.436.670**, selling expense **630.754.891.701**, admin expense **1.763.015.602.591**, operating profit **1.763.597.883.667**, other income **16.961.158.939**, other expense **37.586.153.493**, PBT **1.742.972.889.113**, current tax **360.741.782.309**, deferred tax **-5.198.868.677**, total tax **355.542.913.632**, PAT **1.387.429.975.481**, parent PAT **1.361.084.899.485**, NCI **26.345.075.996**, EPS **435**. Profit/tax/attribution and revenue/COGS bridges exact.
- B03 source text: FY2025 YTD CFO **13.378.374.377.362 VND**, CFF **-3.352.162.410.986 VND**, capex YTD **-2.330.869.042.369 VND**. CFI, net cash change and closing cash not read sufficiently; remain null. CFO/CFF standalone Q4 only if the Q3 baseline has been source-backed and the YTD fields are preserved; never fill CFI/net cash/closing cash by plug.
- Q1/2026 VietstockFinance document ID **543696** B01 opening comparative (sidecar page 4–5) gives 31/12/2025 total assets **93.568.198.109.790 VND** and total equity **67.653.389.117.997 VND**. This comparative total assets differs from original Q4/2025 source by **36.686.243.114 VND**. Q1/2026 comparative liabilities are not legible. Preserve as subsequent comparative evidence; do not overwrite Q4/2025 values or use it to back-calculate total liabilities.
- Data commit after recording the comparative: `2104638b013abe3cdd3d6adc793adcf0df4f6b02`.
- Status: Q4/2025 P&L/source-text checks PASS; B01 liabilities/equity PENDING; B03 CFI/net change/closing cash PENDING; all visual review PENDING. The user directed continuing, so proceed to **GAS Q1/2026**.

### 10.8 GAS Q1/2026 — continue B01 and B03 exception review
- Nguồn: VietstockFinance document ID **543696**, PDF hợp nhất `https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/GAS_Baocaotaichinh_Q1_2026_Hopnhat.pdf`; archive `reports/raw/GAS/auto-gas-20261021/853ad22dfe045d24.pdf`; sidecar `.pdf.extracted.json`.
- B02 source text is already reconciled: revenue **38.019.609.031.268 VND**, COGS **33.511.417.706.493**, gross profit **4.508.191.324.775**, financial income **384.755.468.683**, financial expense **118.408.271.484**, interest expense **53.307.964.713**, selling expense **623.721.077.879**, admin expense **396.928.650.943**, operating profit **3.754.223.754.396**, other income **862.001.024**, other expense **402.099.569**, PBT **3.754.683.655.851**, current tax **764.142.169.569**, deferred tax **-3.573.786.295**, total tax **760.568.383.274**, PAT **2.994.115.272.577**, parent PAT **2.944.603.136.328**, NCI **49.512.136.249**. Keep the P&L fields already source-backed; do not re-extract unless a discrepancy appears.
- B01 sidecar pages 4–5 have unreadable/misaligned current and comparative totals; previous parser explicitly held total assets/liabilities/equity as null because total asset and total source did not reconcile. Do not infer/force them.
- B03 source text page 4 gives CFI **509.484.606.752 VND**, opening cash **5.567.998.965.715 VND**, FX effect **367.185.405 VND**. CFO/CFF/net cash movement remain null because OCR does not give a trustworthy bridge. Do not infer other flow lines from cash balance.
- Current status: P&L source text PASS; B01/remaining B03 PENDING; visual review PENDING. Continue source-only text analysis and store only clear rows; no forced balance.
### 10.9 GAS Q1/2026 — B02 PASS, B01/B03 PENDING, tiếp tục sang PLX

- Nguồn: VietstockFinance document ID **543696**, PDF hợp nhất `https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/GAS_Baocaotaichinh_Q1_2026_Hopnhat.pdf`; archive `reports/raw/GAS/auto-gas-20261021/853ad22dfe045d24.pdf`; sidecar `.pdf.extracted.json`.
- PDF page images chưa render được; chỉ kiểm tra text/OCR sidecar, không gắn cờ visual verified.
- B02 page PDF 6 (trang in 3): revenue **38.019.609.031.268 VND**; COGS **33.511.417.706.493**; gross profit **4.508.191.324.775**; financial income **384.755.468.683**; financial expenses **118.408.271.484**; interest expense **53.307.964.713**; selling expense **623.721.077.879**; admin expense **396.928.650.943**; operating profit **3.754.223.754.396**; other income **862.001.024**; other expense **402.099.569**; PBT **3.754.683.655.851**; current tax **764.142.169.569**; deferred tax **-3.573.786.295**; total tax **760.568.383.274**; PAT **2.994.115.272.577**; parent PAT **2.944.603.136.328**; NCI **49.512.136.249**; EPS **1.177**.
- B02 checks: revenue−COGS−gross profit = 0; operating profit + other income − other expense = PBT; PBT−tax=PAT; parent+NCI=PAT. The identified gross/financial income/financial expense/selling/admin components leave **334.961.244 VND** (0,00892%) between their sum and reported operating profit; source OCR does not identify a reliable additional line. Keep missing detail null and residual metadata; do not force a value or call the detail bridge fully verified.
- B01 page in 1–2: OCR total assets current-year row270 is clipped/misaligned; total liabilities and total equity current-year row400 are not readable. Keep all three totals null. Row310 “Nợ ngắn hạn” appears as **16.867.209.085.764 VND** and is stored as a partial source-text field (visual confirmation pending). Q1/2026 opening comparative separately shows total assets **93.568.198.109.790 VND**, total equity **67.653.389.117.997 VND** and current liabilities **20.573.719.383.413 VND**; do not substitute those prior-year comparative values into Q1/2026 current-year totals or use total assets/equity to back-calculate total liabilities.
- B03 page PDF 7 (trang in 4): CFI **509.484.606.752 VND**; opening cash **5.567.998.965.715 VND**; FX effect **367.185.405 VND**. OCR row40 appears to contain a candidate CFF **314.542.385.295 VND**, but the cashflow bridge is incomplete; keep only in candidate metadata, not the top-level verified cashflow field. CFO, net cash movement and closing cash remain null.
- Trạng thái Q1/2026: B02 core values source-text PASS; B01 totals PENDING; B03 partial, with only CFI/opening cash/FX promoted and CFF candidate held; direct visual review PENDING. Data commit `b7588eaf2143156577e604153289411605eb6606`.
- Q4/2024 total liabilities and Q4/2025 liabilities/equity/cashflow details also remain PENDING. Per user direction to continue, mark GAS exception work as processed to this checkpoint and advance the active ticker to **PLX**, preserving all GAS pending fields and not re-running finished text extraction.

### 10.10 Cập nhật bổ sung GAS Q4/2025 — 03/11/2026

Mục này bổ sung kết quả kiểm tra sau khi đã ghi nhận GAS Q1/2026 và xác định PLX là mã tiếp theo. Không mở lại trích xuất B02 của GAS Q4/2025; chỉ cập nhật phép đối chiếu và provenance mới.

#### B02 — toàn bộ cầu nối tổng số PASS

Nguồn gốc: VietstockFinance document ID **531505**, BCTC hợp nhất Q4/2025, PDF `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%204/GAS_Baocaotaichinh_Q4_2025_Hopnhat.pdf`, archive `reports/raw/GAS/auto-gas-20261021/d93ac1474c125a66.pdf`, sidecar `.pdf.extracted.json`. PDF gốc 17.488.205 byte không mở được qua trình đọc web (lỗi giới hạn Content-Length); không tuyên bố đã xem trực quan PDF gốc Q4.

Raw VND từ B02:
- Revenue **43.683.070.609.001**; COGS **39.890.266.518.331**; gross profit **3.792.804.090.670**.
- Financial income **428.311.439.319**; financial expense **82.785.588.700**; share of profit associates **19.038.436.670**; selling expense **630.754.891.701**; admin expense **1.763.015.602.591**.
- Operating profit **1.763.597.883.667**; other income **16.961.158.939**; other expense **37.586.153.493**; PBT **1.742.972.889.113**.
- Current tax **360.741.782.309**; deferred tax **-5.198.868.677**; total tax **355.542.913.632**; PAT **1.387.429.975.481**; parent PAT **1.361.084.899.485**; NCI **26.345.075.996**; EPS **435**.

Bridge results are exact, all residuals **0 VND**:
- Revenue − COGS = gross profit.
- Gross profit + financial income − financial expense + share of profit associates − selling expense − admin expense = operating profit **1.763.597.883.667 VND**.
- Operating profit + other income − other expense = PBT.
- Current tax + deferred tax = total tax; PBT − total tax = PAT.
- Parent PAT + NCI = consolidated PAT.

#### B03 — đã bổ sung dòng tiền quý IV được hỗ trợ bởi hai nguồn YTD cùng phạm vi

Q4 report FY2025 YTD raw VND: CFO **13.378.374.377.362**; CFF **-3.352.162.410.986**; capex YTD **-2.330.869.042.369**. Q3/2025 report VietstockFinance document ID **523927**, archive `reports/raw/GAS/auto-gas-20261021/e43210f30cce593e.pdf`, same consolidated scope, 9M YTD raw VND: CFO **12.549.166.835.674**; CFF **-904.798.734.792**.

Standalone Q4, calculated using same-year/same-scope YTD subtraction:
- CFO = 13.378.374.377.362 − 12.549.166.835.674 = **829.207.541.688 VND** = **829.207,541688 triệu VND**.
- CFF = -3.352.162.410.986 − (-904.798.734.792) = **-2.447.363.676.194 VND** = **-2.447.363,676194 triệu VND**.
- These quarter values are promoted to the corresponding standalone `operating_cash_flow` and `financing_cash_flow` fields, with raw YTD values retained in `*_ytd` and the derivation metadata. No balancing plug.
- CFI YTD/quarter, net cash change, opening cash, closing cash remain PENDING because the Q4 source text does not provide sufficiently reliable values. Capex remains YTD only until a valid 9M baseline is available.

#### B01 — later comparative is now directly visually verified but must remain separate from original Q4/2025

VietstockFinance Q2/2026 consolidated report document ID **555857**, URL `https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%202/GAS_Baocaotaichinh_Q2_2026_Hopnhat.pdf`; B01 page image directly reviewed (zero-based PDF page index 3, printed page 1; screenshot evidence in conversation `turn168010view0`). Its comparative column for opening 2026 / 31-12-2025 shows:
- Total liabilities **25.914.808.991.853 VND**, comprising current liabilities **20.573.719.389.418** + long-term liabilities **5.341.089.602.435**.
- Equity **67.653.389.117.937 VND**.
- Total assets **93.568.198.109.790 VND**.
- Comparative balance equation is exact: liabilities + equity = assets, residual **0 VND**.

This later comparative total assets is **36.686.243.114 VND greater** than total assets in the original Q4/2025 report (**93.531.511.866.676 VND**). The Q2/2026 comparative equity is also **60 VND below** the prior Q1/2026 opening comparative equity (**67.653.389.117.997 VND**). Therefore, preserve the Q2/2026 comparative as a separate later-presentation basis under `source_validation.subsequent_comparative_q2_2026`; do not populate original Q4/2025 `total_liabilities` or `equity` from this comparison, and do not overwrite its original reported `total_assets`. Q4/2025 canonical B01 still has total liabilities/equity PENDING; visual review of original Q4 PDF remains pending.

Data commit for this update: `7d24584481eb2b6a962c323b862a3389df7bfb55`.

#### Resume position after GAS

GAS has been reviewed through Q1/2026. Remaining manual exceptions are retained:
- Q4/2024: original B01 row300 total liabilities OCR truncated; B03 unreadable.
- Q4/2025: original B01 total liabilities/equity and visual review pending; B03 CFI/net cash/opening/closing pending. CFO and CFF Q4 standalone have now been derived and saved.
- Q1/2026: B01 totals and B03 bridge pending; B02 detail residual **334.961.244 VND (0,00892%)** remains unattributed; do not plug.
The active next item is **PLX Q1/2025**, specifically the cross-year opening-cash bridge. Do not restart GAS or repeat the already reconciled GAS P&L extraction.

### 10.11 PLX Q1/2025 — đã đối chiếu B01/B03 trong kỳ, ngoại lệ số dư chuyển năm vẫn PENDING

Nguồn ưu tiên 1: VietstockFinance document ID **504658**, BCTC hợp nhất Q1/2025:
`https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%201/PLX_Baocaotaichinh_Q1_2025_Hopnhat.pdf`
Archive: `reports/raw/PLX/auto-plx-20261021/8ebe33f1a2757507.pdf`; sidecar `.pdf.extracted.json`.

Nguồn Q4/2024 cùng mã và cùng phạm vi:
`https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%204/PLX_Baocaotaichinh_Q4_2024_Hopnhat.pdf`
Archive: `reports/raw/PLX/auto-plx-20261021/b80662485ac3e19f.pdf`; sidecar `.pdf.extracted.json`.

#### Số gốc Q4/2024
- B01 printed page 1, dòng tiền và tương đương tiền (row110): **15.062.135.832.746 VND**; tiền (row111) **5.329.069.053.043 VND**; tương đương tiền (row112) **9.733.066.779.703 VND**. Ba số cộng khớp row110.
- B03 closing cash row70: **15.062.135.832.746 VND**. B01 row110 và B03 row70 trùng chính xác.
- B03 screenshot của PDF Q4 không mở được trong phiên (endpoint trả lỗi Content-Length too large); kết luận hiện dựa trên text/sidecar đã lưu, visual review Q4 vẫn PENDING.

#### Số gốc Q1/2025
- B01 printed page 1, cột số đầu năm: total cash **14.933.068.792.315 VND**; tiền **5.329.158.367.088 VND**; tương đương tiền **9.603.910.425.227 VND**.
- Note 1 cash table của Q1/2025 (PDF page index 22, printed note page 13) xác nhận tiền đầu năm gồm: tiền mặt **48.317.246.431 VND** + tiền gửi ngân hàng không kỳ hạn **5.046.965.955.718 VND** + tiền đang chuyển **233.875.164.939 VND** = tiền **5.329.158.367.088 VND**. Cộng tương đương tiền **9.603.910.425.227 VND** = tổng **14.933.068.792.315 VND**.
- B03 row60 opening cash: **14.933.068.792.315 VND**. B01 opening and B03 opening trùng chính xác. Q1 B03 quarter/YTD flows and cash bridge have within-period residuals 1 VND (0,0000223%) for flow sum and 0 VND for cash bridge; both within tolerance. Q1 B01/B03 pages were directly inspected via web screenshots (B01 Q1, B03 page images).

#### Chênh lệch liên kỳ và kết luận
- Q1 opening minus Q4 closing = **-129.067.040.431 VND** = **-129.067,040431 triệu VND** (relative difference **-0,856897%**, exceeds 0,01% tolerance).
- Composition change: cash row111 increased **89.314.045 VND**, while cash equivalents row112 decreased **129.156.354.476 VND**; net difference **-129.067.040.431 VND**.
- Q4 B01/B03 agree internally and Q1 B01/B03 agree internally. Q1 Note 1 confirms the Q1 opening components but does not explain why they differ from Q4 closing. Text/sidecar reviewed so far contains no explicit correction/restatement or reclassification explanation. The Q4 source's relevant note text is partially OCR-truncated, so absence of an explanation is not proof that none exists.
- Status remains `PENDING_UNEXPLAINED_CROSS_YEAR_CASH_BASIS`. Preserve Q4 closing and Q1 opening source values, no balancing plug, no overwrite. Revisit only if direct Q4 note image or clearer source evidence explains it.
- Data commit with full cross-period breakdown: `d2f36ef258165355167686a26ff057884bdeedbf`.

#### Resume
PLX Q1/2025 core extraction is already complete; do not repeat it. Since user has directed continuing through pending exceptions, keep this discrepancy PENDING and move to **PLX Q1/2026** next. Q1/2026 already has source-text core values but its cross-year cash mismatch (Q4/2025 closing **10.803.153.849.383 VND** vs Q1/2026 opening **7.588.239.730.231 VND**) is **-3.214.914.119.152 VND** (**-29,75903%**) and must be audited separately without changing either reported value. After that, review Q2/2026 unreadable cashflow/visual hold.

### 10.12 PLX Q1/2026 — chênh lệch số dư đầu kỳ được giải thích là số comparative phân loại lại

Nguồn: VietstockFinance document ID **545469**, BCTC hợp nhất Q1/2026:
`https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/PLX_Baocaotaichinh_Q1_2026_Hopnhat.pdf`
Archive: `reports/raw/PLX/auto-plx-20261021/158547073d7cd10f.pdf`; sidecar `.pdf.extracted.json`.

#### Dấu hiệu về cơ sở số dư đầu kỳ
- B01 printed page 1, PDF page index 1: tiêu đề cột đầu kỳ ghi rõ **“Số đầu năm (phân loại lại)”**.
- B01 row110 và B03 row60 đều ghi tiền và tương đương tiền đầu kỳ **7.588.239.730.231 VND**.
- So với số cuối Q4/2025 gốc **10.803.153.849.383 VND**, chênh lệch là **-3.214.914.119.152 VND** (**-29,759033%**). Do cột so sánh của Q1/2026 ghi rõ “phân loại lại”, đây là khác biệt của comparative opening basis; không coi là lỗi cầu nối nội kỳ và không điều chỉnh số Q4 hoặc Q1. Các trang đã xem không công bố bút toán/chi tiết từng dòng phân loại lại, nên chỉ kết luận được là số comparative đã phân loại lại, không suy đoán bút toán cụ thể.

#### Note 1 — đối chiếu cơ cấu tiền đầu kỳ và cuối kỳ
Opening cash:
- Tiền mặt **62.364.956.985 VND** + tiền gửi ngân hàng không kỳ hạn **4.323.618.323.442 VND** + tiền đang chuyển **227.182.532.474 VND** = tiền **4.613.165.812.901 VND**.
- Tiền tương đương **2.975.073.917.330 VND**.
- Tổng tiền và tương đương tiền đầu kỳ **7.588.239.730.231 VND**.

Closing cash:
- Tiền mặt **64.263.633.540 VND** + tiền gửi ngân hàng không kỳ hạn **7.214.983.868.036 VND** + tiền đang chuyển **346.315.152.556 VND** = tiền **7.625.562.654.132 VND**.
- Tiền tương đương **2.408.843.681.628 VND**.
- Tổng tiền và tương đương tiền cuối kỳ **10.034.406.335.760 VND**.
- Các tổng thành phần Note 1 khớp chính xác, residual 0 VND.

#### B03 — cầu nối Q1/2026 PASS
Raw VND:
- CFO **9.375.725.757.265**.
- CFI **764.690.442.359**.
- CFF **-7.689.092.776.722**.
- Net cash change **2.451.323.422.902**. Tổng CFO+CFI+CFF khớp chính xác, residual 0 VND.
- Opening cash **7.588.239.730.231** + net cash change **2.451.323.422.902** + FX effect **-5.156.817.373** = closing cash **10.034.406.335.760**, residual 0 VND.
- B01/B03/Note 1 opening và closing balances khớp chính xác trên cùng Q1/2026 reclassified comparative basis. Không plug và không thay đổi số Q4/2025 gốc.

Visual evidence đã xem qua screenshot: B01 `turn381601view0`; B03 trang đầu `turn381601view1`; B03 trang cuối/cash bridge `turn381601view2`; Note 1 `turn919705view0`; policy định nghĩa tiền `turn734794view2`.
Data commit: `2820b036e70ca84e15ca6cd6d03b66a4aba448d5`.

### 10.13 PLX Q2/2026 — B03 LCTT còn PENDING, không suy diễn
- Nguồn: VietstockFinance document ID **556113**, BCTC hợp nhất Q2/2026:
  `https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%202/PLX_Baocaotaichinh_Q2_2026_Hopnhat.pdf`
  Archive `reports/raw/PLX/auto-plx-20261021/925339daf7038fe2.pdf`; sidecar `.pdf.extracted.json`; 36 trang.
- B01 và B02 đã được OCR/source-text kiểm tra trước đây. Doanh thu thuần, giá vốn, lợi nhuận gộp, LNTT, LNST và LNST cổ đông mẹ đã được lưu theo basis hiện có. Không chạy lại B02 nếu không phát hiện mâu thuẫn.
- B03 source sidecar PDF page indices 5–6 (trang in 6–7) mất hầu hết bảng dòng tiền, không có cấu phần đáng tin cậy để nhập. Tiền đầu kỳ **10.034.406.335.760 VND** khớp số cuối Q1/2026; tiền cuối kỳ **6.323.957 triệu VND** chỉ đọc từ B01. Giữ CFO/CFI/CFF/net cash/FX ở null; tuyệt đối không dùng tiền đầu-cuối để suy ra các dòng lưu chuyển.
- Endpoint PDF gốc dung lượng khoảng 15,9 MB chưa mở được bằng bộ đọc hiện có; vì thế visual review B03 PENDING. WiData không được dùng để bổ sung nếu chưa cần thiết theo quy tắc nguồn đã xác lập.
- Trạng thái: B03 `NEEDS_MANUAL_REVIEW_CASHFLOW_OCR_INCOMPLETE`; no balancing plug. Người dùng đã chỉ đạo tiếp tục nên giữ Q2/2026 pending và chuyển tới mã kế tiếp theo checkpoint.

### 10.14 GEG Q1/2024 — trực quan hóa và đóng kỳ gốc

Nguồn: VietstockFinance document ID **460145**, BCTC hợp nhất Q1/2024:
`https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%201/GEG_Baocaotaichinh_Q1_2024_Hopnhat.pdf`
Archive: `reports/raw/GEG/auto-geg-20261021/51f06da4fc1935f2.pdf`; sidecar `.pdf.extracted.json`.

Đã xem trực tiếp ảnh PDF gốc:
- B01 printed pages 1–2 (PDF page indices 2–3).
- B02 printed page 3 (PDF page index 4).
- B03 printed pages 4–5 (PDF page indices 5–6).
Evidence refs: `turn265283view0`, `turn346148view1`, `turn346148view2`, `turn346148view0`, `turn347739view0`.

#### B01 — raw VND, residuals 0
- Total assets **16.152.857.699.551 VND** = current assets **1.690.854.386.569** + non-current assets **14.462.003.312.982**.
- Total liabilities **10.259.620.128.232 VND** = current liabilities **1.692.725.940.150** + long-term liabilities **8.566.894.188.082**.
- Equity **5.893.237.571.319 VND**; liabilities + equity = total assets exactly.
- Cash/equivalents closing **214.930.981.659 VND**; cash **93.225.403.279**, cash equivalents **121.705.578.380**. Opening B01 cash/equivalents **229.105.088.949 VND**.

#### B02 — raw VND, all bridges 0
- Revenue **739.214.916.619**; COGS **321.118.871.630**; gross profit **418.096.044.989**.
- Financial income **9.379.344.534**; financial expense **245.541.068.704**; interest expense **241.715.610.003**; share of profit associates **-554.693.467**; selling expense **135.147.589**; admin expense **43.849.062.574**; operating profit **137.395.417.189**.
- Other income **547.221.018**; other expense **1.299.685.240**; other result **-752.464.222**; PBT **136.642.952.967**.
- Current tax **11.367.030.590**; deferred tax **-1.000.617.024**; total tax **10.366.413.566**; PAT **126.276.539.401**; parent PAT **89.662.202.743**; NCI **36.614.336.658**; EPS **262**.
- Revenue−COGS=gross profit; operating-profit bridge; other profit; PBT; tax; PAT and parent+NCI bridges all exact.

#### B03 — original source corrected for adjacent-year OCR column
- CFO **134.488.003.107 VND**; CFI **11.861.771.247**; CFF **-160.548.389.615**; net cash change **-14.198.615.261**.
- Opening cash **229.105.088.949**; FX effect **24.507.971**; closing cash **214.930.981.659**.
- Flow sum and opening + net change + FX = closing residuals are both **0 VND**.
- Capex **-4.743.605.709 VND**; dividends paid **-4.706.100 VND**.
- Direct visual check of B03 printed page 5 establishes the two cash columns: 2024 closing row70 is **214.930.981.659 VND**; **321.665.888.215 VND** is the 2023 comparative figure in the adjacent column. Prior OCR had copied the comparative number into current-period closing and caused a false residual; corrected current-period record uses the 2024 value. Dividends row36 is **-4.706.100 VND** (not prior OCR candidate -1,024 million VND); source negative sign retained.
- This source is sufficient; the previous Q1/2025 comparative cashflow record remains provenance history only, not the selected primary basis.

Data commit: `4e05d9bf8d280f827d0d40e7b24573110f974e78`.
Status: `verified_manual_visual_reconciliation`, B01/B02/B03 PASS, no open core/detail exception for GEG Q1/2024. Do not re-extract or re-review this period unless a future contradiction occurs.

#### Resume
Continue to **GEG Q2/2024**. Its existing Q2 record has B03 selected from the later Q2/2025 comparative while original Q2/2024 source sidecar is archived; inspect original source before changing values. Preserve prior/current comparative differences as separate evidence and do not force balance.

### 10.15 GEG Q2/2024 — original VietstockFinance source reconciled; image review pending

- Nguồn chính: VietstockFinance document ID **471941**, BCTC hợp nhất Q2/2024; URL `https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%202/GEG_Baocaotaichinh_Q2_2024_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/55c5b7c66cb1a05b.pdf`; sidecar `.pdf.extracted.json`; 41 trang.
- Sidecar gốc lưu text B01 trang in 1–2 (sidecar pages 3–4), B02 trang in 3 (sidecar page 5), B03 trang in 4–5 (sidecar pages 6–7). PDF gốc trực tiếp không mở được qua web PDF reader trong phiên này; do đó **visual review vẫn PENDING** và không đánh dấu `manually_visual_reviewed=true`.
- B01 raw VND:
  - Tài sản ngắn hạn **1.806.189.691.416** + tài sản dài hạn **14.257.515.053.426** = tổng tài sản **16.063.704.744.842**.
  - Nợ ngắn hạn **1.563.146.348.902** + nợ dài hạn **8.630.255.956.975** = tổng nợ **10.193.402.305.877**.
  - Vốn chủ **5.870.302.438.965**; tổng nợ + vốn chủ = tổng tài sản **16.063.704.744.842**.
  - Tiền và tương đương tiền **580.960.136.162 VND**. Các phương trình B01 đều residual **0 VND**.
- B02 quý riêng Q2:
  - Doanh thu **487.632.741.698** − giá vốn **275.644.401.105** = lợi nhuận gộp **211.988.340.593 VND**.
  - Doanh thu tài chính **9.116.502.070**; chi phí tài chính **168.916.588.684**; lãi vay **163.438.254.030**; lãi/lỗ công ty liên kết **-2.098.990.934**; chi phí bán hàng **-135.147.589** (giữ nguyên dấu âm in trên báo cáo); chi phí quản lý **28.784.114.212**; lợi nhuận thuần hoạt động **21.440.296.422**.
  - Thu nhập khác **1.197.591.199** − chi phí khác **1.335.917.189** = lỗ khác **-138.325.990**; PBT **21.301.970.432**.
  - Thuế hiện hành **15.977.874.103** + thuế hoãn lại **4.097.192.500** = tổng thuế **20.075.066.603**; PAT hợp nhất **1.226.903.829 VND**.
  - PAT công ty mẹ **21.460.036.310** + NCI **-20.233.132.481** = PAT hợp nhất **1.226.903.829 VND**; EPS **52**. Các cầu nối B02 residual **0 VND**.
- B03 original Q2 report H1 YTD raw VND:
  - CFO **495.388.370.938**; CFI **12.532.140.011**; CFF **-156.094.358.264**; net cash change **351.826.152.685**.
  - FX **28.894.528**; opening cash **229.105.088.949**; closing cash **580.960.136.162**. Flow sum và cash bridge residual đều **0 VND**.
  - Q1/2024 original B03 (document ID 460145) is the same-year baseline: CFO **134.488.003.107**, CFI **11.861.771.247**, CFF **-160.548.389.615**, net change **-14.198.615.261**, FX **24.507.971**, opening cash **229.105.088.949**, closing cash **214.930.981.659**.
  - Standalone Q2 = original H1 YTD less original Q1 YTD: CFO **360.900.367.831**, CFI **670.368.764**, CFF **4.454.031.351**, net cash change **366.024.767.946**, FX **4.386.557**, opening cash **214.930.981.659**, closing cash **580.960.136.162**. All Q2 standalone flow and cash bridge residuals **0 VND**. Capex H1 YTD **-2.739.497.026** less Q1 capex **-4.743.605.709** gives Q2 **+2.004.108.683 VND**.
  - B03 row36 current H1 value is a dash; dividends paid remains `null`, not imputed.
- Important source-basis correction: the prior Q2/2024 cashflow fields used H1/2024 comparative values from the later Q2/2025 report. Those later comparative YTD values were CFO **542.515.588.853**, CFI **4.654.341.202**, CFF **-195.358.003.939**, net **351.811.926.116**, FX **43.121.097 VND**. They differ materially from the Q2/2024 original report in CFO/CFI/CFF and by **14.226.569 VND** between net change and FX, while beginning/ending cash match. The original Q2/2024 report is now canonical for Q2/2024; later comparative values remain stored as superseded audit evidence and are not deleted.
- ROA **0,0305%**, ROE **0,0834%**, computed using consolidated quarter PAT divided by average opening/closing assets or equity × 4 × 100.
- Data commit: `27c237713c4cdb847ef4544201fb5e4806bcf033`.
- Status: **source-text reconciled; visual review pending**. All arithmetic checks on B01/B02/B03 pass at raw VND precision. Do not repeat core extraction or reselect comparative cashflow source; proceed with GEG **Q3/2024** as requested, while retaining Q2's visual-review marker.

### 10.16 GEG Q3/2024 — original source text reconciled; visual pending

- Nguồn: VietstockFinance document ID **483862**, báo cáo hợp nhất Q3/2024; URL `https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%203/GEG_Baocaotaichinh_Q3_2024_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/92f6d2a0ac2dccae.pdf`; sidecar `.pdf.extracted.json`; 41 trang.
- Sidecar nguồn lưu B01 trang in 1–2 (sidecar pages 3–4), B02 trang in 3 (page 5), B03 trang in 4–5 (pages 6–7). PDF ảnh không mở được qua web PDF reader trong phiên; không đánh dấu visual verified.
- B01 raw VND: current assets **2.059.775.715.054** + non-current assets **13.965.673.513.060** = total assets **16.025.449.228.114**; current liabilities **1.278.205.547.821** + long-term liabilities **8.924.999.693.534** = total liabilities **10.203.205.241.355**. Equity OCR row begins `ã.822.243.986.759`, first digit is blurred; value candidate **5.822.243.986.759 VND** matches assets less liabilities exactly. Keep the candidate and its source-basis note; do not claim independently visually confirmed.
- B02 Q3 riêng: revenue **543.139.233.330** − COGS **305.803.618.965** = gross profit **237.335.614.365 VND**; financial income **10.192.254.821**; financial expense **230.597.066.787**; interest expense **224.016.050.556**; associate loss **-4.728.790.117**; selling expense cell is a dash (current quarter nil); admin expense **33.082.865.448**; operating loss **-20.880.853.166**; other income **2.301.079.814** − other expense **1.329.573.447** = other profit **971.506.367**; PBT **-19.909.346.709 VND**.
- Tax current **13.175.931.414** + deferred **14.717.521.128** = total tax **27.893.452.542**; PAT **-47.802.799.341**; parent PAT **-27.338.001.098** + NCI **-20.464.798.243** = PAT exactly. PBT − tax differs from reported PAT by **90 VND** (relative **0,000000188%**); this is a tiny OCR/source rounding residual well below 0,01%. Keep the three printed values unchanged; do not insert a plug. EPS **-81**.
- B03 original 9M YTD raw VND: CFO **759.517.327.189**; CFI **85.031.541.367**; CFF **-213.156.993.585**; net cash change **631.391.874.971**; FX **32.078.475**; opening cash **229.105.088.949**; closing cash **860.529.042.395**; capex YTD **-74.137.239.651**; dividends YTD **-39.812.400**.
- Same-year baseline is now original Q2/2024 B03 document **471941**, not the later Q3/2025 comparative: H1 CFO **495.388.370.938**, CFI **12.532.140.011**, CFF **-156.094.358.264**, net change **351.826.152.685**, FX **28.894.528**, opening cash **229.105.088.949**, closing cash **580.960.136.162**, capex **-2.739.497.026**.
- Standalone Q3 = original Q3 YTD less original Q2 H1 YTD: CFO **264.128.956.251**; CFI **72.499.401.356**; CFF **-57.062.635.321**; net cash change **279.565.722.286**; FX **3.183.947**; opening cash **580.960.136.162**; closing cash **860.529.042.395**; capex **-71.397.742.625**. B03 row36 Q3 YTD is **-39.812.400 VND** and Q2 H1 row36 is a dash; Q3 row36 value remains as printed in YTD, and standalone Q3 cash dividend amount follows the report's dash-as-no-payment basis.
- YTD flow sum, YTD cash bridge, Q3 standalone flow sum and Q3 standalone cash bridge residuals are all **0 VND**. ROA **-1,1917%**, ROE **-3,2707%**, calculated from quarter consolidated PAT divided by average opening/closing assets or equity × 4 × 100.
- Source-revision: earlier Q3 data used Q3/2025 comparative 9M/2024 for YTD cashflow and H1 basis. Original Q3/2024 B03 now canonical; same-year original Q2/2024 baseline also supersedes the Q2/2025 comparison. Preserve later comparative values as audit-only, not canonical.
- Data commit: `9ca3f8f8cbae3810400872d5f34dad02f002fdd2`.
- Status: source text reconciled, visual review pending. Continue GEG **Q4/2024**; do not repeat Q1/Q2/Q3 core extraction or reselect B03 source basis. Preserve Q2/Q3 visual-pending markers and Q3's 90 VND PBT/tax/PAT residual.

### 10.17 GEG Q4/2024 — original PDF B01/B02/B03 visually verified

- Nguồn: VietstockFinance document ID **490218**, BCTC hợp nhất; PDF `https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%204/GEG_Baocaotaichinh_Q4_2024_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/cfe0d5be553d8698.pdf`; sidecar `reports/raw/GEG/auto-geg-20261021/a5dc3fd9e734420f.pdf.extracted.json`. PDF reader reports 81 pages. The consolidated portion starts after the separate statements; original consolidated report pages were visually inspected at PDF indices 42–46.
- B01 printed page 1 (PDF index 42): current assets **1.381.711.542.204 VND**, non-current assets **13.790.652.181.814 VND**, total assets **15.172.363.724.018 VND**. Cash and equivalents **163.717.707.072 VND**, including cash **99.909.204.892** and equivalents **63.808.502.180**.
- B01 printed page 2 (PDF index 43): current liabilities **785.159.808.730 VND**, long-term liabilities **8.623.907.509.228 VND**, total liabilities **9.409.067.317.958 VND**; equity **5.763.296.406.060 VND**. Assets = current + non-current; liabilities = current + long-term; assets = liabilities + equity, all residual **0 VND**.
- B02 printed page 3 (PDF index 44), Q4-only column:
  - Revenue **555.327.531.103 VND**; COGS **349.563.904.310**; gross profit **205.763.626.793**.
  - Financial income **9.347.533.906**; financial expenses **156.053.657.470**; including interest expense **156.555.108.658** (the source shows interest amount slightly greater due other negative finance cost line).
  - Share of profit in associates **12.749.592.517**; selling expenses **25.000.000**; admin expenses **29.773.611.792**; operating profit **42.008.483.954**.
  - Other income **1.497.146.411**; other expense **10.610.793**; other profit **1.486.535.618**; PBT **43.495.019.572**.
  - Current income tax **14.850.552.832**; deferred income tax **16.271.720.547**; total income tax **31.122.273.379**; PAT **12.372.746.193**; parent PAT **31.038.790.590**; NCI **-18.666.044.397**; EPS **52**.
  - Revenue−COGS=gross profit; gross profit plus finance/associate less selling/admin=operating profit; other income−other expense=other profit; operating+other=PBT; current+deferred tax=total tax; PBT−tax=PAT; parent+NCI=PAT. Every residual **0 VND**.
- B03 printed page 4 (PDF index 45) and page 5 (PDF index 46), FY2024 YTD source:
  - CFO **879.398.089.294 VND**; CFI **38.466.134.014**; CFF **-983.287.237.113**; net cash change **-65.423.013.805**.
  - Opening cash **229.105.088.949**; FX **35.631.928**; closing cash **163.717.707.072**.
  - Capex YTD **-121.558.921.796**; dividends paid YTD **-76.197.803.000**.
- Original Q3/2024 B03 same-year baseline (VietstockFinance document **483862**) is CFO **759.517.327.189**, CFI **85.031.541.367**, CFF **-213.156.993.585**, net change **631.391.874.971**, FX **32.078.475**, opening cash **229.105.088.949**, closing cash **860.529.042.395**, capex **-74.137.239.651**, dividends **-39.812.400 VND**.
- Standalone Q4 = original FY2024 YTD less original Q3/2024 9M YTD:
  - CFO **119.880.762.105 VND**; CFI **-46.565.407.353**; CFF **-770.130.243.528**; net change **-696.814.888.776**; FX **3.553.453**.
  - Opening cash **860.529.042.395**; closing cash **163.717.707.072**.
  - Capex **-47.421.682.145**; dividends paid **-76.157.990.600 VND**.
  - YTD and quarter flows, YTD/quarter cash bridge, and YTD subtraction residuals all **0 VND**. No balancing plug.
- ROA **0,3173%**, ROE **0,8544%**, formula consolidated quarter PAT / average opening and closing assets or equity × 4 × 100.
- Direct PDF screenshot evidence: B01 printed pages 1–2 `turn798051view1`, `turn798051view2`; B02 printed page 3 `turn798051view3`; B03 printed pages 4–5 `turn798051view4`, `turn798051view5`. Visual review is **PASS**.
- Data commit Q4/2024: `f31c70a6e8052c3be901c94d297ccddec31fdf0a`.
- Status: `verified_manual_visual_reconciliation`, period complete. Continue GEG **Q1/2025**. Do not repeat extraction or visual review for Q1–Q4/2024.

### 10.18 GEG Q1/2025 — original B01/B02/B03 visually verified; tax/admin OCR corrected

- Nguồn: VietstockFinance document ID **504494**, BCTC hợp nhất Q1/2025; PDF `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%201/GEG_Baocaotaichinh_Q1_2025_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/cc8daa6c76e9f381.pdf`; sidecar `.pdf.extracted.json`; 83 trang.
- Đã xem trực tiếp PDF indices 6–10: B01 printed pages 1–2 (indices 6–7), B02 printed page 3 (index 8), B03 printed pages 4–5 (indices 9–10).
- B01 raw VND:
  - Current assets **1.895.627.338.896**; non-current assets **13.811.390.457.902**; total assets **15.707.017.796.798**.
  - Current liabilities **829.890.405.609**; long-term liabilities **8.499.913.734.564**; total liabilities **9.329.804.140.173**.
  - Equity **6.377.213.656.625**. Balance sheet assets = liabilities + equity, current/non-current composition and current/long-term liabilities all residual **0 VND**.
  - B01 01/01/2025 opening comparative in the Q1 report: assets **15.173.556.340.436**, liabilities **9.409.067.317.958**, equity **5.764.489.022.478 VND**. Compared with the original Q4/2024 closing B01, liabilities are identical but opening assets/equity are each **1.192.616.418 VND higher**. Retain Q4 original and Q1 opening comparative separately; do not overwrite either basis. This difference is a presentation/reconciliation item still pending explanation.
- B02 raw VND, Q1 current-quarter column (Q1 equals YTD):
  - Revenue **1.112.755.859.981**; COGS **286.668.495.975**; gross profit **826.087.364.006**.
  - Financial income **7.837.526.270**; financial expenses **187.421.671.779**; interest expense **184.359.083.942**; share of profit in associates **3.450.715.502**; selling expense current Q1 cell is a dash; admin expense **44.874.042.418**; operating profit **605.079.891.581**.
  - Other income **229.946.621**; other expenses **15.102.772**; other profit **214.843.849**; PBT **605.294.735.430**.
  - Current tax **30.035.228.409**; deferred tax **-37.686.501.526**; total tax **-7.651.273.117**; PAT **612.946.008.547**; parent PAT **378.240.835.561**; NCI **234.705.172.986**; EPS **1.056**.
  - All B02 bridges are exact: revenue−COGS=gross profit; gross profit plus financial/associate results less selling/admin=operating profit; other income−other expense=other profit; operating+other=PBT; current+deferred tax=total tax; PBT−total tax=PAT; parent+NCI=PAT. Residuals **0 VND**.
- Source correction: original Q1/2025 B02 screenshot row 16 visibly reads deferred tax **(37.686.501.526) VND**; archived OCR had **-31.686.501.526**, while the later Q1/2026 comparative had **-37.686.301.526**. The original Q1/2025 report is canonical; use **-37.686.501.526**. This corrects total tax to **-7.651.273.117 VND** and PBT−tax=PAT exactly. Also correct admin expense row 9 to **44.874.042.418 VND** (previous OCR 44.814.042.418 produced a 60m VND residual in operating profit); screenshot shows 44.874.042.418 and operating-profit bridge is now exact. Selling-expense row 8 current Q1 cell is a dash (store nil/zero), not the Q1/2024 comparative **135.147.589 VND**.
- B03 original Q1/2025 raw VND (Q1 equals YTD):
  - CFO **62.310.535.515**; CFI **76.527.759.434**; CFF **-127.159.459.528**; net cash change **11.678.835.421**.
  - Opening cash **163.717.707.072**; FX **3.490.065**; closing cash **175.400.032.558**.
  - Capex **-1.199.715.023**; dividends paid **-221.374.400**.
  - CFO+CFI+CFF=net change and opening+net change+FX=closing; residuals **0 VND**.
- The Q1/2026 comparative previously used for the cashflow source also matches these Q1/2025 B03 values; retain it as corroborating/audit evidence only. Its deferred-tax comparative amount is not the original-period canonical value.
- ROA **15,8791%**, ROE **40,3862%** using quarter PAT / average opening-closing assets or equity × 4 × 100.
- Direct screenshot evidence: B01 printed p1–2 `turn501875view0`, `turn501875view1`; B02 printed p3 `turn501875view2`; B03 printed p4–5 `turn501875view3`, `turn501875view4`. All three statements visual PASS.
- Data commit Q1/2025: `1b278c047e80d0ba3965cac57e468f77e742df70`.
- Status: `verified_manual_visual_reconciliation`. Q1/2025 is complete. Continue GEG **Q2/2025**; do not repeat any Q1–Q4/2024 or Q1/2025 core extraction/visual review. Carry the B01 opening-balance difference as a separate cross-period pending item.

### 10.19 GEG Q2/2025 — original B01/B02/B03 visually verified; source-sidecar path corrected

- Nguồn: VietstockFinance document ID **513346**, BCTC hợp nhất Q2/2025; URL `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%202/GEG_Baocaotaichinh_Q2_2025_Hopnhat.pdf`; PDF 85 trang; archive `reports/raw/GEG/auto-geg-20261021/4a525617c885ff3f.pdf`; đúng sidecar gốc `reports/raw/GEG/auto-geg-20261021/4a525617c885ff3f.pdf.extracted.json`.
- Đã xem trực tiếp ảnh PDF:
  - B01 printed p1, PDF index 6; B01 printed p2, index 7.
  - B02 printed p3, index 8.
  - B03 printed p4–5, indices 9–10.
  - Evidence refs: `turn571822view0`–`turn571822view4`; cả B01/B02/B03 visual PASS.
- B01 raw VND:
  - Current assets **1.751.807.765.411**; non-current assets **13.433.655.631.118**; total assets **15.185.463.396.529**.
  - Current liabilities **689.069.127.083**; long-term liabilities **7.999.546.127.260**; total liabilities **8.688.615.254.343**.
  - Equity **6.496.848.142.186**; assets = liabilities + equity; current/noncurrent and current/long-term liability subtotals all residual **0 VND**.
  - Cash **75.431.231.865**; equivalents **398.118.112.165**; reported cash and equivalents total **473.549.350.030 VND**. Sum of the two components is **6.000 VND lower** than the reported total (relative **0,000001267%**). Keep all three source values unchanged; no plug.
  - Other B01 detail values: short-term investments **236.500.000.000**; short-term receivables **914.018.215.370**; inventories **105.104.270.467**; fixed assets **12.897.652.730.850**; retained earnings **595.533.639.319 VND**.
- B02 current quarter Q2/2025 values, raw VND:
  - Revenue **624.339.137.173**; COGS **351.447.828.104**; gross profit **272.891.309.069**.
  - Financial income **119.441.275.360**; financial expenses **172.262.962.873**; interest expense **158.452.550.000**; share of profit in associates **709.366.343**.
  - Selling expense current-quarter cell is a dash; store **0**. Admin expense **37.254.702.429**; operating profit **183.524.285.470**.
  - Other income **1.058.716.373**; other expense **491.643.016**; other profit **567.073.357**; PBT **184.091.358.827**.
  - Current tax **28.569.111.623**; deferred tax **-2.192.612.235**; total tax **26.376.499.388**; PAT **157.714.859.439**; parent PAT **165.820.759.376**; NCI **-8.105.899.937**; basic and diluted EPS **356 VND**.
  - Revenue−COGS=gross profit; gross profit + finance income − finance expense + associates − selling − admin = operating profit; other income−other expense=other profit; operating + other=PBT; current+deferred=total tax; PBT−tax=PAT; parent+NCI=PAT. All residuals **0 VND**.
- Important OCR column corrections from the original B02 screenshot:
  - Current Q2 financial expense is **172.262.962.873 VND**; interest expense **158.452.550.000 VND**. The previous extracted **163.438.254.030 VND** for interest expense belongs to Q2/2024 comparative, not Q2/2025.
  - Current Q2 admin expense is **37.254.702.429 VND**.
  - Current Q2 other expense is **491.643.016 VND**, not **401.643.016**.
  - Current Q2 selling expense is a dash; **-135.147.589 VND** is in the Q2/2024 comparative column and is not assigned to Q2/2025.
  - PAT/current tax/deferred tax/parent/NCI all taken from the Q2/2025 current-quarter column; not mixed with H1 YTD.
- B03 H1/2025 original YTD raw VND:
  - CFO **555.421.075.993**; CFI **476.067.298.075**; CFF **-721.712.954.268**; net cash change **309.775.419.800**.
  - Opening cash **163.717.707.072**; FX **56.223.158**; closing cash **473.549.350.030**.
  - Capex YTD **-16.668.892.827**; dividends paid YTD **-296.857.300 VND**.
- Same-year original Q1/2025 B03 baseline, document **504494**: CFO **62.310.535.515**; CFI **76.527.759.434**; CFF **-127.159.459.528**; net **11.678.835.421**; FX **3.490.065**; opening cash **163.717.707.072**; closing cash **175.400.032.558**; capex **-1.199.715.023**; dividends **-221.374.400 VND**.
- Standalone Q2 = original H1 YTD less original Q1 YTD:
  - CFO **493.110.540.478 VND**; CFI **399.539.538.641**; CFF **-594.553.494.740**; net cash change **298.096.584.379**; FX **52.733.093**.
  - Opening cash **175.400.032.558**; closing cash **473.549.350.030**.
  - Capex **-15.469.177.804**; dividends paid **-75.482.900 VND**.
  - H1 and Q2 standalone flow sums, cash bridges and Q1/YTD subtraction residuals all **0 VND**.
- ROA **4,0842%**, ROE **9,8005%**, using consolidated quarter PAT / average opening and closing assets/equity × 4 × 100.
- Sidecar path correction: the previous data record's `financial_line_items_source` mistakenly referenced `reports/raw/GEG/auto-geg-20261021/e5c84e9cb42b1698.pdf.extracted.json`, which is the **Q2/2026 comparative report**, not the original Q2/2025 report. It is corrected to `4a525617c885ff3f.pdf.extracted.json`. The 2026 comparative remains audit-only; no Q2/2025 current-period data should be populated from it.
- Data commit: `6f46accce8df3d5b621e4ab4cf46df37cfa9b7c0`.
- Status: `verified_manual_visual_reconciliation`; Q2/2025 complete. Continue GEG **Q3/2025**. Do not repeat Q1/2024–Q1/2025 core extraction; carry Q2/Q3/2024 visual-pending and Q1/2025 opening-balance presentation difference separately.

### 10.20 GEG Q3/2025 — original VietstockFinance B01/B02/B03 visually verified and corrected

- Nguồn: VietstockFinance document ID **523528**, BCTC hợp nhất Q3/2025; URL `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%203/GEG_Baocaotaichinh_Q3_2025_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/770d2246aaa4f701.pdf`; sidecar `.pdf.extracted.json`; PDF 83 trang.
- Đã xem trực tiếp ảnh PDF gốc: B01 trang in 1–2 (PDF pages 5–6), B02 trang in 3 (PDF page 7), B03 trang in 4–5 (PDF pages 8–9). Evidence refs: `turn168010view0` đến `turn168010view4`.
- Đơn vị báo cáo là **VND**, phạm vi **hợp nhất**. Không dùng số comparative của năm trước thay số hiện tại.

#### B01 — raw VND; residuals 0
- Tài sản ngắn hạn **1.975.118.527.567** + tài sản dài hạn **13.272.833.523.252** = tổng tài sản **15.247.952.050.819**.
- Nợ ngắn hạn **950.488.102.304** + nợ dài hạn **7.724.273.864.190** = tổng nợ **8.674.761.966.494**.
- Vốn chủ sở hữu **6.573.190.084.325**; nợ + vốn chủ = tổng tài sản **15.247.952.050.819**, residual **0 VND**.
- Tiền và tương đương tiền **406.053.297.053** gồm tiền **95.553.297.053** + tương đương tiền **310.500.000.000**, khớp chính xác.
- Dòng tài sản khác đã đọc: đầu tư ngắn hạn **378.500.000.000**; phải thu ngắn hạn **1.099.569.520.475**; hàng tồn kho **62.960.131.810**; tài sản cố định **12.701.094.168.860**; xây dựng cơ bản dở dang **381.389.541.012**; đầu tư tài chính dài hạn **54.283.512.223**; retained earnings **666.486.918.225 VND**.

#### B02 — raw VND; toàn bộ cầu nối 0
- Doanh thu thuần **671.328.091.438** − giá vốn **348.638.552.595** = lợi nhuận gộp **322.689.538.843**.
- Doanh thu tài chính **7.288.526.236**; chi phí tài chính **194.351.138.463**; trong đó lãi vay **193.441.309.636**; lãi công ty liên kết **625.069.998**.
- Chi phí bán hàng row25 là dấu gạch ngang: giữ **null**, không gán 0 và không lặp nhầm chi phí quản lý. Chi phí quản lý row26 **37.895.058.681**.
- Lợi nhuận thuần hoạt động **98.356.937.933**; thu nhập khác **616.491.042**; chi phí khác **247.139.597**; lợi nhuận khác **369.351.445**; PBT **98.726.289.378**.
- Thuế hiện hành **18.340.054.977**; thuế hoãn lại **323.314.089**; tổng thuế **18.663.369.066**; PAT hợp nhất **80.062.920.312**; parent PAT **74.645.813.663**; NCI **5.417.106.649**; EPS cơ bản/suy giảm **198**.
- Cầu nối doanh thu−giá vốn=gross profit; gross profit + finance income − finance expense + associates − selling − admin = operating profit; other income−other expense=other profit; operating + other=PBT; current+deferred tax=total tax; PBT−tax=PAT; parent+NCI=PAT. Tất cả residual **0 VND**.
- Lỗi OCR/cột đã sửa: trước đó financial expense bị để 0; đúng theo B02 row22 là **194.351.138.463 VND**. Trước đó selling expense bị gán nhầm bằng admin expense; row25 hiện tại là dấu gạch ngang, giữ `null`. Admin expense đúng là **37.895.058.681 VND**.

#### B03 — 9M YTD và quý III riêng; residuals 0
- 9M YTD: CFO **856.209.015.015**; CFI **244.031.897.120**; CFF **-857.979.656.903**; net cash change **242.261.255.232**; opening cash **163.717.707.072**; FX **74.334.749**; closing cash **406.053.297.053 VND**.
- H1/2025 baseline dùng báo cáo Q2/2025 gốc document **513346**, không dùng comparative của Q2/2026: CFO **555.421.075.993**; CFI **476.067.298.075**; CFF **-721.712.954.268**; net cash **309.775.419.800**; FX **56.223.158**; cash closing **473.549.350.030**; capex **-16.668.892.827**; dividends **-296.857.300 VND**.
- Q3 standalone = 9M YTD trừ original H1 YTD: CFO **300.787.939.022**; CFI **-232.035.400.955**; CFF **-136.266.702.635**; net cash change **-67.514.164.568**; FX **18.111.591**; opening cash **473.549.350.030**; closing cash **406.053.297.053 VND**.
- Capex Q3 **-103.386.144.231 VND** = 9M capex **-120.055.037.058** less H1 **-16.668.892.827**. Dividends Q3 **-49.677.200 VND** = 9M row36 **-346.534.500** less H1 **-296.857.300**. Giữ dấu âm theo báo cáo.
- YTD and Q3 flow sums, cash bridges, FX and subtraction residuals all **0 VND**. B01 cash total equals B03 ending cash exactly.

- ROA **2,10%**, ROE **4,90%**, dùng PAT quý riêng / bình quân số đầu-cuối kỳ × 4 × 100; average total assets **15.216.707,723674 triệu VND**, average equity **6.535.019,1132555 triệu VND**.
- Data commit: `a69ced9560a3afc29c27a8d993c727b15147f0d5`.
- Trạng thái: `verified_manual_visual_reconciliation`, B01/B02/B03 PASS, không còn ngoại lệ lõi/chi tiết cho Q3/2025. Các ngoại lệ khác của GEG (Q2/Q3/2024 visual, Q1/2025 opening comparative delta, Q2/2025 cash-components residual 6.000 VND) được giữ riêng, không ảnh hưởng trạng thái Q3.
- Tiếp theo: **GEG Q4/2025**. Không trích xuất hoặc xem lại Q1/Q2/2025 và các kỳ 2024 đã hoàn tất.

### 10.21 GEG Q4/2025 — original VietstockFinance B01/B02/B03 visually verified; complete

- Nguồn: VietstockFinance document ID **529632**, BCTC hợp nhất Q4/2025; URL `https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%204/GEG_Baocaotaichinh_Q4_2025_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/a5dc3fd9e734420f.pdf`; sidecar `.pdf.extracted.json`; PDF 84 trang.
- Đã xem trực tiếp ảnh PDF gốc: B01 trang in 1–2, B02 trang in 3, B03 trang in 4–5. Evidence refs: `turn162727view0`, `turn162727view1`, `turn140584view0`, `turn162727view2`, `turn162727view3`.
- Phạm vi hợp nhất, đơn vị VND. Không lấy các cột comparative 2024/YTD thay cho cột Quý IV/2025.

#### B01 — raw VND, residuals 0
- Tài sản ngắn hạn **1.793.332.240.030** + tài sản dài hạn **13.317.555.791.672** = tổng tài sản **15.110.888.031.702**.
- Nợ ngắn hạn **884.097.585.558** + nợ dài hạn **7.729.078.580.317** = tổng nợ **8.613.176.165.875**.
- Vốn chủ **6.497.711.865.827**; tổng nợ + vốn = tổng tài sản **15.110.888.031.702**, residual **0 VND**.
- Tiền và tương đương tiền **86.364.663.248** = tiền **46.702.358.323** + tương đương tiền **39.662.304.925**, residual **0 VND**.
- Chi tiết tài sản đã đọc: đầu tư ngắn hạn **335.162.676.704**; phải thu ngắn hạn **1.279.925.753.264**; hàng tồn kho **46.144.766.536**; TSCĐ **12.506.295.684.512**; XDCB dở dang **666.224.607.122**; đầu tư tài chính dài hạn **57.611.864.671**; tài sản dài hạn khác **33.100.995.517**.
- Vốn chủ: vốn góp **4.148.043.710.000**; thặng dư **14.462.886.313**; quỹ đầu tư phát triển **96.180.413.885**; lợi nhuận chưa phân phối **705.958.826.235**; NCI equity **1.533.066.029.394**.

#### B02 — cột riêng Q4/2025, raw VND
- Doanh thu **590.444.253.989**; giá vốn **297.744.769.538**; lợi nhuận gộp **292.699.484.451**; cầu doanh thu − giá vốn = lợi nhuận gộp residual **0 VND**.
- Lỗi OCR đã sửa: COGS cũ **297.744.169.538 VND** thiếu **600.000 VND**. Ảnh B02 row3 xác nhận **297.744.769.538 VND**; sau sửa, phép tính khớp chính xác.
- Doanh thu tài chính **7.405.857.236**; chi phí tài chính **129.223.283.175**; chi phí lãi vay **128.720.727.251**; lãi từ công ty liên kết **201.824.614**.
- Chi phí bán hàng row25 hiện tại là dấu gạch ngang: giữ `null`; không gán 0 và không sao chép số comparative năm 2024. Chi phí quản lý doanh nghiệp row26 **80.029.939.227**.
- Lợi nhuận thuần hoạt động **91.053.943.899**; thu nhập khác **558.911.923**; chi phí khác **1.060.644.068**; lỗ khác **-501.732.145**; PBT **90.552.211.754**.
- Thuế hiện hành **-5.791.447.756** (benefit); thuế hoãn lại **288.594.688**; tổng thuế **-5.502.853.068**; PAT **96.055.064.822**; parent PAT **83.445.048.823**; NCI **12.610.015.999**; EPS cơ bản **111**, EPS suy giảm **570**.
- Các cầu nối lợi nhuận hoạt động, lợi nhuận khác, PBT, thuế, PAT và parent+NCI=PAT đều residual **0 VND**.

#### B03 — FY2025 YTD và quý IV riêng
- FY2025 YTD raw VND: CFO **932.884.327.033**; CFI **1.921.143.888**; CFF **-1.012.240.268.026**; biến động tiền thuần **-77.434.797.105**; tiền đầu năm **163.717.707.072**; tỷ giá **81.753.281**; tiền cuối năm **86.364.663.248**.
- Original 9M/2025 baseline từ GEG Q3/2025 VietstockFinance doc **523528**: CFO **856.209.015.015**; CFI **244.031.897.120**; CFF **-857.979.656.903**; net **242.261.255.232**; FX **74.334.749**; opening **163.717.707.072**; closing **406.053.297.053**; capex **-120.055.037.058**; dividends **-346.534.500 VND**.
- Q4 standalone = FY2025 YTD trừ original 9M/2025 YTD: CFO **76.675.312.018**; CFI **-242.110.753.232**; CFF **-154.260.611.123**; net cash change **-319.696.052.337**; FX **7.418.532**; opening cash **406.053.297.053**; closing cash **86.364.663.248**.
- Capex Q4 **-288.511.522.757 VND** = FY2025 YTD **-408.566.559.815** less 9M **-120.055.037.058**. Dividends Q4 **-76.484.415.200 VND** = FY2025 YTD **-76.830.949.700** less 9M **-346.534.500**. Negative signs retained.
- YTD and Q4 flow sums, cash bridges, FX and YTD-to-quarter delta residuals all **0 VND**; B01 cash/equivalents equals B03 ending cash exactly.

#### Ratios and status
- ROA **2,5312%**, ROE **5,8790%**, using PAT Q4 / average opening-closing assets or equity × 4 × 100. Average total assets **15.179.420,0412605 triệu VND**; average equity **6.535.450,975076 triệu VND**.
- Data commit: `4fd6282fbaf785879018cfe645611c59a7cf23e2`.
- Status: `verified_manual_visual_reconciliation`; B01/B02/B03 PASS, all raw-VND residuals zero. GEG Q4/2025 complete; do not reload/re-extract/re-review unless new contradiction.
- Kỳ tiếp theo: **GEG Q1/2026**. Preserve historical GEG holds (Q2/Q3 2024 visual, Q1/2025 opening comparative delta, Q2/2025 6,000 VND cash-component residual within tolerance, Q2/2026 cash-basis exception) separately.

## 11. Giới hạn thao tác

- Không sửa code, schema, pipeline, dashboard hoặc logic tự động trong công việc nhập liệu BCTC nếu chưa có yêu cầu riêng.
- Không thêm nguồn thứ ba, không dùng tìm kiếm web ngoài hai nguồn đã được người dùng duyệt.
- Không tự tạo dữ liệu, không suy diễn số thiếu, không thay đổi quy trình chỉ để làm cho một kỳ được PASS.
- Mọi cập nhật data/checkpoint phải có commit và lưu SHA commit; xác minh lại nội dung sau khi ghi.
