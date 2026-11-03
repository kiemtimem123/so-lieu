# SOP xử lý báo cáo tài chính doanh nghiệp niêm yết

- Phiên bản: 1.6
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
## 11. Giới hạn thao tác

- Không sửa code, schema, pipeline, dashboard hoặc logic tự động trong công việc nhập liệu BCTC nếu chưa có yêu cầu riêng.
- Không thêm nguồn thứ ba, không dùng tìm kiếm web ngoài hai nguồn đã được người dùng duyệt.
- Không tự tạo dữ liệu, không suy diễn số thiếu, không thay đổi quy trình chỉ để làm cho một kỳ được PASS.
- Mọi cập nhật data/checkpoint phải có commit và lưu SHA commit; xác minh lại nội dung sau khi ghi.
