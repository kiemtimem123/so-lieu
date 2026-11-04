# SOP xử lý báo cáo tài chính doanh nghiệp niêm yết

- Phiên bản: 1.34
- Ngày ban hành: 04/11/2026
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

### 10.6 GAS Q4/2024 — B01/B02/B03 source-text reconciled; image review PENDING

- Nguồn chính: VietstockFinance document ID **490581**, báo cáo tài chính hợp nhất năm 2024, đơn vị VND. Tệp PDF gốc: `https://static2.vietstock.vn/data/HOSE/2024/BCTC/VN/QUY%204/GAS_Baocaotaichinh_Q4_2024_Hopnhat.pdf`; archive `reports/raw/GAS/auto-gas-20261021/7fa3b1653ff606d1.pdf`; sidecar `.pdf.extracted.json`; 75 trang.
- Nội dung bảng trong PDF gốc đã truy xuất được qua text extraction. Công cụ chụp ảnh trang PDF đã thử trên các trang B01/B02/B03 nhưng bị lỗi giới hạn kích thước (PDF 13.553.614 bytes); vì vậy **chưa visual verified**. Không ghi nhận đã xem ảnh. Không sử dụng nguồn dữ liệu thứ ba; các giá trị dưới đây lấy từ chính PDF VietstockFinance document 490581.
- **B01 — Bảng cân đối kế toán hợp nhất (trang in 1–2):**
  - Tổng tài sản **81.893.564.503.501 VND**.
  - Tổng nợ phải trả row300 **20.322.569.237.871 VND**. Row300 đã đọc được trực tiếp từ bảng gốc, không suy ngược.
  - Nợ ngắn hạn row310 **14.581.511.125.671 VND**; nợ dài hạn row330 **5.741.058.112.200 VND**; cộng đúng tổng nợ, residual **0**.
  - Vốn chủ sở hữu row400 **61.570.995.265.630 VND**; tổng nợ + vốn chủ sở hữu bằng tổng tài sản, residual **0**.
  - Tài sản ngắn hạn **57.295.844.201.420 VND**; tài sản dài hạn **24.597.720.302.081 VND**; cộng đúng tổng tài sản, residual **0**.
  - Tiền và tương đương tiền **5.649.483.431.468 VND** (tiền **1.248.083.431.468**, tương đương tiền **4.401.400.000.000**); retained earnings **9.553.019.715.422 VND**; NCI equity **1.323.213.381.181 VND**.
- **B02 — Kết quả kinh doanh hợp nhất, Quý IV cột Năm nay (trang in 3):**
  - Doanh thu bán hàng/cung cấp dịch vụ row01 **24.960.846.410.089 VND**; giảm trừ row02 **15.729.073.724 VND**; doanh thu thuần row10 **24.945.117.336.365 VND**. Residual row01 − row02 − row10 = **0**. Giá vốn **20.900.958.213.404 VND**; lợi nhuận gộp **4.044.159.122.961 VND**; gross-profit residual **0**.
  - Doanh thu tài chính **419.753.041.491 VND**; chi phí tài chính **140.949.317.288 VND**, trong đó lãi vay **57.220.327.243 VND**; phần lãi công ty liên doanh/liên kết **12.623.872.062 VND**; chi phí bán hàng **668.833.753.996 VND**; chi phí quản lý **1.097.693.949.210 VND**; lợi nhuận hoạt động **2.569.059.016.020 VND**.
  - Thu nhập khác **1.712.505.229 VND**; chi phí khác **12.474.501.162 VND**; lỗ khác **-10.761.995.933 VND**; PBT **2.558.297.020.087 VND**.
  - Thuế hiện hành **498.141.880.056 VND**; thuế hoãn lại **7.816.140.590 VND**; tổng chi phí thuế **505.958.020.646 VND**; PAT **2.052.338.999.441 VND**; parent PAT **2.044.102.438.055 VND**; NCI PAT **8.236.561.386 VND**. PBT − tổng thuế = PAT và parent + NCI = PAT, residual đều **0**.
  - EPS row70 **852 VND/cổ phiếu**. Số OCR cũ 408 là đọc nhầm cột, đã sửa.
  - Trường `revenue` trong snapshot chuẩn là **doanh thu thuần row10 = 24.945.117.336.365 VND** (24.945.117,336365 triệu VND), không phải doanh thu gộp row01. Giá trị OCR cũ 34.960.846.410.089 VND cũng sai; doanh thu gộp đúng row01 là 24.960.846.410.089 VND.
- **B03 — Lưu chuyển tiền tệ hợp nhất, FY2024 YTD (trang in 4):**
  - CFO **8.705.303.886.462 VND**; CFI **7.978.721.478.066 VND**; CFF **-16.711.006.239.817 VND**; biến động tiền thuần **-26.980.875.289 VND**. CFO + CFI + CFF = net change, residual **0**.
  - Tiền tồn đầu năm **5.668.895.214.949 VND**; ảnh hưởng tỷ giá FY **+7.569.091.808 VND**; tiền tồn cuối năm **5.649.483.431.468 VND**. Opening + net change + FX = closing, residual **0**.
  - Chi mua sắm TSCĐ row21 **-1.821.623.230.975 VND**; cổ tức/lợi nhuận đã trả row36 **-13.971.054.206.100 VND**.
- **Q4 riêng — phương pháp và kết quả:** Lấy FY2024 YTD trong B03 gốc Q4 trừ 9M/2024 YTD trong B03 gốc Q3 VietstockFinance document `483862`, cùng phạm vi hợp nhất:
  - CFO **+1.344.415.959.226 VND**.
  - CFI **+5.520.432.980.286 VND**.
  - CFF **-13.303.960.768.096 VND**.
  - Net cash change **-6.439.111.828.584 VND**; CFO + CFI + CFF = net change, residual **0**.
  - Opening cash Q4 lấy closing cash Q3 **10.851.522.950.436 VND**; closing cash Q4 **5.649.483.431.468 VND**.
  - Capex Q4 **-568.193.423.765 VND**; dividends paid Q4 **-12.971.054.206.100 VND**.
  - Q3 B03 row61 ảnh hưởng tỷ giá YTD không đọc được trong sidecar đã lưu. Vì vậy để `foreign_exchange_effect=null` cho Q4 riêng. Chênh lệch cầu nối tiền trước FX là **-1.237.072.309.616 VND** (số FX cần để khớp sẽ là +1.237.072.309.616 VND), chỉ lưu là residual chẩn đoán, **không** gán làm số nguồn, không plug. FX YTD FY2024 vẫn lưu chính xác **+7.569.091.808 VND**.
- **ROA/ROE:** ROA **9,45%**, ROE **13,54%**, theo PAT quý IV / bình quân tài sản hoặc vốn chủ đầu kỳ-cuối kỳ × 4 × 100.
- **So sánh với comparative Q1/2025:** B01 đầu năm trong VietstockFinance Q1/2025 document 504411 ghi total assets **81.854.881.408.158 VND**, total liabilities **20.283.886.142.528 VND**, equity **61.570.995.265.630 VND**. So với Q4/2024 gốc: assets và liabilities cùng thấp hơn **38.683.095.343 VND**, equity trùng chính xác. Giữ nguyên cả hai cơ sở; chưa có căn cứ diễn giải lý do khác biệt, không ghi đè số gốc Q4.
- Trạng thái kỳ: **SOURCE TEXT RECONCILED — VISUAL REVIEW PENDING**. Không chạy lại trích xuất lõi B01/B02/B03; chỉ mở lại khi có bằng chứng ảnh/nguồn mới. Data commit: `c86aa1c06944e8f2a7d218b560ec925e61e23c5d`.

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

### 10.22 GEG Q1/2026 — original VietstockFinance B01/B02/B03 visually verified; complete within cash-bridge tolerance

- Nguồn: VietstockFinance document ID **544855**, BCTC hợp nhất Q1/2026; URL `https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%201/GEG_Baocaotaichinh_Q1_2026_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/d8dade2f27045243.pdf`; sidecar `.pdf.extracted.json`; PDF 82 trang.
- Đã xem trực tiếp ảnh gốc: B01 trang in 1–2, B02 trang in 3, B03 trang in 4–5. Evidence refs: `turn499291view0` đến `turn499291view4`.
- Phạm vi hợp nhất; đơn vị VND. Q1 là kỳ độc lập và cũng là YTD Q1.

#### B01 — raw VND; all principal balances and subtotals exact
- Tài sản ngắn hạn **1.954.801.640.627** + tài sản dài hạn **13.180.264.763.883** = tổng tài sản **15.135.066.404.510**.
- Nợ ngắn hạn **745.118.568.386** + nợ dài hạn **7.628.887.919.678** = tổng nợ **8.374.006.488.064**.
- Vốn chủ **6.761.059.916.446**; tổng nợ + vốn = tổng tài sản, residual **0 VND**.
- Tiền và tương đương tiền **105.856.793.049** = tiền **46.625.510.309** + tương đương tiền **59.231.282.740**, residual **0**.
- Các cấu phần tài sản ngắn hạn đã đọc: đầu tư ngắn hạn **310.507.676.704**; phải thu ngắn hạn **1.419.494.957.548**; hàng tồn kho **53.383.397.796**; tài sản ngắn hạn khác **65.558.815.530**. Cộng các dòng này với tiền/tiền tương đương khớp tổng tài sản ngắn hạn, residual **0**.
- Tài sản dài hạn: phải thu dài hạn **43.282.198.696**; TSCĐ **12.306.921.915.949**; XDCB dở dang **739.628.606.009**; đầu tư tài chính dài hạn **58.230.571.801**; tài sản dài hạn khác **32.201.471.428**. Cộng khớp tổng dài hạn, residual **0**.
- Vốn chủ: vốn góp **4.148.043.710.000**; thặng dư **14.234.077.513**; quỹ đầu tư phát triển **96.180.413.885**; lợi nhuận chưa phân phối **912.599.944.288**; NCI equity **1.590.001.770.760**. Cộng khớp vốn chủ, residual **0**.

#### B02 — raw VND; corrected OCR financial income
- Doanh thu **767.379.199.934**; giá vốn **280.414.635.779**; lợi nhuận gộp **486.964.564.155**; residual doanh thu−giá vốn−lợi nhuận gộp **0**.
- Doanh thu tài chính **3.976.415.409**; chi phí tài chính **165.243.270.859**; chi phí lãi vay **165.232.291.642**; lợi nhuận công ty liên kết **618.707.130**; chi phí quản lý **41.100.578.261**. Mẫu B02 năm 2026 không trình bày một dòng bán hàng riêng; không tự tạo dòng/giá trị, giữ field đó null.
- Lợi nhuận thuần hoạt động **285.215.837.574**; thu nhập khác **1.521.784.785**; chi phí khác **322.343.359**; lợi nhuận khác **1.199.441.426**; PBT **286.415.279.000**.
- Thuế hiện hành **23.323.328.690**; thuế hoãn lại **-562.023.086**; tổng thuế **22.761.305.604**; PAT **263.653.973.396**; parent PAT **206.675.501.563**; NCI **56.978.471.833**; EPS cơ bản **577**, EPS suy giảm **550**.
- Lỗi OCR: doanh thu tài chính bị đọc **3.076.415.409 VND**; ảnh B02 row5 và cầu lợi nhuận hoạt động xác nhận là **3.976.415.409 VND**, sửa tăng **900.000.000 VND**. Sau sửa, cầu lợi nhuận hoạt động residual **0**.
- Cầu lợi nhuận khác, PBT, thuế, PAT và parent+NCI=PAT đều residual **0 VND**.

#### B03 — Q1 current YTD, residual cash bridge 900 VND retained
- CFO **213.327.143.465 VND**; CFI **-26.739.175.041**; CFF **-167.121.630.611**; net cash change **19.466.337.813**. Tổng ba dòng tiền = net change, residual **0 VND**.
- Tiền đầu kỳ **86.364.663.248**; tỷ giá **25.791.088**; tiền cuối kỳ **105.856.793.049**. Cầu tiền đầu + biến động + tỷ giá còn dư **+900 VND** theo số in; relative difference **0,0000008502%** (<0,01%).
- Không điều chỉnh số in, không tạo plug. Lưu residual 900 VND như sai số OCR/làm tròn nhỏ được phép theo SOP. Tiền cuối B03 khớp tổng tiền & tương đương tiền trên B01 chính xác.
- Chi mua sắm TSCĐ **-74.740.950.202 VND**; cổ tức đã trả **-28.499.200 VND**.

#### Ratios, comparative delta, status
- ROA **6,9736%**, ROE **15,9082%**, theo PAT quý / bình quân assets hoặc equity đầu-cuối kỳ × 4 × 100.
- Cột comparative đầu kỳ trong B01 Q1/2026 so với closing B01 Q4/2025: tổng tài sản khớp chính xác. Nợ comparative **8.613.176.045.875 VND** thấp hơn closing Q4 original **120.000 VND**, vốn comparative **6.497.711.985.827 VND** cao hơn closing Q4 original **120.000 VND**. Tổng nguồn vốn không đổi. Ghi nhận khác biệt comparative nhỏ riêng, không ghi đè hai kỳ.
- Data commit: `0512bb8ad9a48d92872fbb3590f57a5c3c28ebca`.
- Status: `verified_manual_visual_reconciliation_with_cash_bridge_rounding_residual`; B01/B02 PASS, B03 flow PASS và cash bridge PASS_WITHIN_TOLERANCE (900 VND). Không có plug.
- Kỳ tiếp theo: **GEG Q2/2026**. Không xử lý lại Q4/2025 hoặc các kỳ đã đóng; bảo lưu Q2/Q3 2024 visual holds, Q1/2025 comparative delta, Q2/2025 6.000 VND cash component delta và Q2/2026 historical quarter-opening cash-basis note (nếu còn phù hợp kỳ).

### 10.23 GEG Q2/2026 — B01/B02/B03 source-text reconciled; image, other-income and cash-opening exceptions remain

- Nguồn chính: VietstockFinance document ID **555452**, báo cáo hợp nhất Q2/2026; URL `https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%202/GEG_Baocaotaichinh_Q2_2026_Hopnhat.pdf`; archive `reports/raw/GEG/auto-geg-20261021/e5c84e9cb42b1698.pdf`; sidecar `.pdf.extracted.json`; PDF 43 trang.
- Endpoint PDF trực tiếp trả Internal Error trong lần truy xuất; trang WiData `https://widata.vn/GEG?tab=documents` cũng không truy xuất được bằng bộ đọc hiện tại. Không có số từ WiData nào được sao chép. **Không đánh dấu visual verified**; các kiểm tra dưới đây dựa trên text sidecar của đúng PDF VietstockFinance.
- Đơn vị VND; phạm vi hợp nhất; B01 sidecar pages 4–5 (trang in 1–2), B02 page 6 (trang in 3), B03 pages 7–8 (trang in 4–5).

#### B01 — các tổng và cấu phần nguồn text khớp
- Tài sản ngắn hạn **1.795.327.105.425** + tài sản dài hạn **13.686.336.280.651** = tổng tài sản **15.481.663.386.076 VND**.
- Nợ ngắn hạn **1.073.912.833.438** + nợ dài hạn **7.656.720.901.854** = tổng nợ **8.730.633.735.292 VND**.
- Vốn chủ sở hữu **6.751.029.650.784 VND**; nợ + vốn = tổng tài sản, residual **0**.
- Tiền và tương đương tiền **100.327.178.533** = tiền **65.562.141.184** + tương đương tiền **34.765.037.349 VND**, residual **0**.
- Cấu phần tài sản ngắn hạn: đầu tư ngắn hạn **399.347.389.553**; phải thu ngắn hạn **1.089.342.589.419**; hàng tồn kho **59.335.951.480**; tài sản ngắn hạn khác **146.973.996.440 VND**; cùng tiền/tiền tương đương, tổng khớp subtotal, residual **0**.
- Cấu phần tài sản dài hạn: phải thu dài hạn **29.767.173.178**; TSCĐ **12.889.071.805.876**; XDCB dở dang **663.499.637.448**; đầu tư tài chính dài hạn **56.008.966.262**; tài sản dài hạn khác **47.988.697.887 VND**; tổng khớp subtotal, residual **0**.
- Vốn chủ: vốn góp **4.327.165.250.000**; thặng dư vốn **14.146.077.513**; quỹ đầu tư phát triển **96.180.413.885**; lợi nhuận chưa phân phối **742.962.162.243**; NCI equity **1.570.575.747.143 VND**; tổng khớp vốn chủ, residual **0**.

#### B02 — lợi nhuận quý II, ngoại lệ một dòng thu nhập khác
- Doanh thu thuần **580.335.207.100**; giá vốn **342.819.635.918**; lợi nhuận gộp **237.515.571.182 VND**; residual **0**.
- Doanh thu tài chính **5.360.349.632**; chi phí tài chính **183.296.067.795**; lãi vay **183.236.981.159**; lãi công ty liên kết **904.922.295**; chi phí quản lý **41.821.936.719 VND**. Mẫu B02 theo Thông tư 43/2026 không có dòng chi phí bán hàng riêng; field selling expense để null.
- Lợi nhuận thuần hoạt động **18.662.838.595 VND**; thu nhập khác OCR candidate **445.937.969 VND**; chi phí khác **440.059.055 VND**; lỗ khác theo row40 **-94.121.086 VND**; PBT **18.568.717.509 VND**.
- **PENDING row31 other income**: candidate OCR 445.937.969 − expense 440.059.055 không bằng reported other loss -94.121.086; residual **100.000.000 VND**. Không thay candidate bằng số suy ra 345.937.969; trường hiển thị `other_income=null`, candidate giữ trong raw metadata/rejected values để rà soát ảnh khi truy cập được.
- Thuế hiện hành **10.500.368.887**; thuế hoãn lại **-83.657.192**; tổng thuế **10.416.711.695 VND**; PAT **8.152.005.814**; parent PAT **28.179.986.219**; NCI **-20.027.980.405 VND**; EPS cơ bản **22**, EPS suy giảm **21**.
- Các cầu nối doanh thu−giá vốn=gross profit; gross + financial income − financial expense + associates − admin = operating profit; operating profit + other result = PBT; thuế hiện hành + thuế hoãn lại = tổng thuế; PBT−tax=PAT; parent+NCI=PAT đều residual **0 VND**. Cầu other-income detail là ngoại lệ duy nhất ở B02.

#### B03 — H1 YTD pass; standalone Q2 cash opening basis PENDING
- H1/2026 YTD: CFO **722.160.976.132**; CFI **-732.448.267.884**; CFF **35.658.808.670**; net cash change **25.371.516.918 VND**; opening cash theo B03 line60 **74.942.444.345**; FX **13.217.270**; closing cash **100.327.178.533 VND**. Tổng CFO+CFI+CFF và cầu tiền YTD đều residual **0**.
- Q1/2026 gốc (doc **544855**): CFO **213.327.143.465**; CFI **-26.739.175.041**; CFF **-167.121.630.611**; net change **19.466.337.813**; FX **25.791.088**; closing cash **105.856.793.049**; capex **-74.740.950.202**; dividends **-28.499.200 VND**.
- Q2 standalone = H1 YTD less Q1 YTD: CFO **508.833.832.667**; CFI **-705.709.092.843**; CFF **202.780.439.281**; net change **5.905.179.105**; FX **-12.573.818**; closing cash **100.327.178.533**; capex **-578.529.720.523**; dividends **-42.564.200 VND**. Flow sum residual **0**.
- **PENDING cash opening basis**: H1 report B03 line60 opening cash **74.942.444.345 VND** differs from original Q1 close **105.856.793.049 VND** by **-30.914.348.704 VND** (29,2039% of Q1 close). The B01 01/01/2026 comparative cash and B03 line60 in Q2 source both show 74.942.444.345; preserve source value.
- If using Q1 close as standalone Q2 opening, the calculated closing balance is **111.749.398.336 VND**, which exceeds reported close **100.327.178.533 VND** by **11.422.219.803 VND** (10,22% of calculated close; 11,38% relative to reported close). This is material. Therefore standalone Q2 `cash_beginning=null`; do not assert quarterly cash bridge PASS and do not insert a plug.
- ROA **0,2130%**, ROE **0,4826%** theo PAT quý / bình quân tài sản hoặc vốn chủ đầu-cuối kỳ × 4 × 100.

#### Trạng thái, commit và bước tiếp theo
- Data commit Q2/2026 source-text reconciliation and quarantined other-income candidate: `ee39119046f6fc7cab0511e9af120ce504ce7dcd`.
- Q2/2026 status: `pending_visual_review_other_income_and_q2_cash_opening_basis`. B01/B02 core totals and H1 YTD cash flow are source-text reconciled; original PDF screenshot review pending; row31 other income candidate and standalone Q2 opening cash remain PENDING.
- Không chạy lại Q1/2026 đã hoàn tất.
- Người dùng yêu cầu tiếp tục không dừng vì PENDING; do GEG đã tới Q2/2026 (kỳ mới nhất trong bộ 10 kỳ), chuyển sang mã tiếp theo **IDC**, bắt đầu **Q1/2024** theo quy trình tuần tự. Giữ các ngoại lệ GEG tách riêng, không gắn verified cho các trường đang PENDING.

### 10.10 IDC Q1–Q2/2024 — lưu trạng thái trung gian, tiếp tục Q3

Nguồn chỉ dùng VietstockFinance và các tệp liên kết tại danh mục IDC; phạm vi báo cáo hợp nhất. Các số tiền bên dưới giữ nguyên gốc VND; dữ liệu hiển thị lưu theo triệu VND.

#### Q1/2024 — số lõi khớp, một chi tiết KQKD PENDING
- Document ID **462783**, PDF `https://static2.vietstock.vn/data/HNX/2024/BCTC/VN/QUY%201/IDC_Baocaotaichinh_Q1_2024_Hopnhat.pdf`, archive `reports/raw/IDC/auto-idc-20261021/44694a289f32bd8c.pdf`, sidecar `.pdf.extracted.json`.
- B01: tài sản **17.386.392.291.350 VND**, nợ **10.894.297.173.971 VND**, vốn **6.492.095.117.379 VND**; phương trình tài sản = nợ + vốn, tài sản ngắn + dài hạn và nợ ngắn + dài hạn đều residual 0.
- B02: revenue **2.467.056.536.161 VND**, COGS **1.368.769.156.854**, gross profit **1.098.287.379.307**, PBT **213.710.166.262**, current tax **38.489.929.690**, deferred tax **12.728.892**, total tax **38.502.658.582**, PAT **175.207.507.680**, parent PAT **147.786.155.639**, NCI **27.421.352.041**, EPS **2.106**. PBT-tax=PAT and parent+NCI=PAT, residual 0.
- B02 row25 selling-expense OCR candidate **41.894.251.738 VND** does not reconcile the printed operating profit **209.126.465.495 VND** with other identified components; residual **776.003.705.179 VND**. The later Q1/2025 comparative column for Q1/2024 internally reconciles but materially changes several P&L values. Keep original Q1/2024 numbers; selling-expense detail remains null and comparative basis stored separately. Do not back-solve row25.
- B03 Q1/2024 original current-period/YTD: CFO **951.312.310.814 VND**, CFI **-154.748.226.063**, CFF **-1.022.256.653.200**, net cash change **-225.692.568.449**, beginning cash **1.333.592.588.129**, FX **147.356.077**, closing cash **1.108.047.375.757**. Flow/cash bridge residuals exact.
- PDF image visual review pending. Q1 status remains `pending_visual_review_and_operating_profit_detail_reconciliation`; no re-extraction of B01/B03.

#### Q2/2024 — B01/B02 and both cashflow source bases reconcile
- Document ID **471540**, archive `reports/raw/IDC/auto-idc-20261021/ecbef46d7d1d9ff3.zip`; consolidated statement is ZIP member `2_idc_2024_7_30_f164297_741tctbtc_2972024_bctc_hop_nhat_q2_2024_signed.pdf`, sidecar `.zip.extracted.json`. It has 80 pages; financial statements at sidecar p9–15 (B01 p9–12, B02 p13, B03 p14–15).
- B01 at 30/6/2024: current assets **6.040.235.098.201 VND**, non-current assets **11.504.262.353.656**, total assets **17.544.497.451.857**; current liabilities **4.309.098.655.756**, long-term liabilities **7.097.346.081.582**, total liabilities **11.406.444.737.338**, equity **6.138.052.714.519**. Asset and liability composition equations and assets=liabilities+equity residual 0.
- B02 standalone Q2: revenue **2.148.489.327.956 VND**, COGS **1.338.623.411.936**, gross profit **809.865.916.020**, financial income **39.414.434.810**, financial expense **35.135.290.358**, associate profit **1.163.120.573**, selling expense **27.114.533.189**, admin expense **63.864.415.600**, operating profit **724.329.232.256**, other income **13.484.566.343**, other expense **394.869.489**, other profit **13.089.696.854**, PBT **737.418.929.110**, current tax **174.725.083.274**, deferred tax **-21.177.039.468**, total tax **153.548.043.806**, PAT **583.870.885.304**, parent PAT **432.484.844.388**, NCI **151.386.040.916**, EPS **1.311**. Each row bridge and PAT allocation residual 0.
- Original Q2/2024 B03 H1 YTD raw VND: CFO **2.296.007.290.628**, CFI **-724.113.031.201**, CFF **-1.895.302.679.995**, net cash change **-323.408.420.568**, opening cash **1.333.592.588.129**, FX **233.255.231**, closing cash **1.010.417.422.792**. Subtract original Q1 YTD to derive standalone Q2: CFO **1.344.694.979.814**, CFI **-569.364.805.138**, CFF **-873.046.026.795**, net cash change **-97.715.852.119**, opening cash **1.108.047.375.757**, FX **85.899.154**, closing cash **1.010.417.422.792**. H1 and Q2 standalone flow/cash bridge residuals are 0.
- IMPORTANT preserve the existing top-level cashflow basis: the dataset already selects the Q2/2025 VietstockFinance comparative H1/2024 column because the later report reclassified CFO/CFI by almost equal/opposite **27.887.768.541 / -27.887.762.007 VND**, with CFF unchanged and net/FX residual only **6.534 VND**. The original Q2/2024 source basis is now stored as a fully reconciled alternate under `source_validation.original_q2_2024_cashflow_ytd_raw_vnd` and `cashflow_source_reconciliation.original_q2_2024_report_comparison`. Do not overwrite top-level selected fields or re-run the reclassification decision.
- Q2 status: B01/B02 and both source cashflow bases text-reconciled; original PDF visual review pending. Data commit `f98ea1e052eb79e06fadd8398bec784459f86aa6`.

#### Resume point
- The user's requested save point is **IDC Q2/2024 complete source-text reconciliation**. Q1/2024's selling-expense exception remains open, but does not block continuing.
- Next: **IDC Q3/2024**, archive `reports/raw/IDC/auto-idc-20261021/ba6b182fb273799c.zip`. Do not repeat Q1/Q2 core extraction; continue source-text validation and specifically inspect cashflow reclassification and outstanding detail fields.
### 10.11 IDC Q3/2024 — B01/B02/B03 gốc đã đối chiếu, visual pending

- Nguồn: VietstockFinance document ID **483651**, BCTC hợp nhất; ZIP `https://static2.vietstock.vn/data/HNX/2024/BCTC/VN/QUY%203/IDC_Baocaotaichinh_Q3_2024_Hopnhat.zip`; archive `reports/raw/IDC/auto-idc-20261021/ba6b182fb273799c.zip`; sidecar `.zip.extracted.json`; member báo cáo hợp nhất `1_idc_2024_11_1_1f04f63_1028tctbtc_29102024_cbtt_bctc_hop_nhat_signed.pdf` (63 trang).
- Đã đọc text/OCR sidecar trang 8–14: B01 trang in 3–6 (sidecar p8–11), B02 trang in 7 (p12), B03 trang in 8–9 (p13–14). Không có ảnh trực quan; giữ visual review PENDING.
- B01 tại 30/9/2024: current assets **6.744.296.361.521 VND**, non-current assets **11.390.620.067.429**, total assets **18.134.916.428.950**; current liabilities **4.602.455.824.878**, long-term liabilities **6.841.753.870.894**, total liabilities **11.444.209.695.772**, equity **6.690.706.733.178**. Asset composition, liabilities composition and asset = liabilities + equity all residual 0.
- B02 riêng Q3: revenue **2.275.529.728.208 VND**, COGS **1.482.208.258.233**, gross profit **793.321.469.975**, financial income **44.433.707.502**, financial expense **34.399.178.354**, share of profit associates **197.452.841**, selling expense **27.442.146.367**, admin expense **61.006.782.583**, operating profit **715.104.523.014**, other income **3.389.615.048**, other expense **1.847.402.659**, other profit **1.542.212.389**, PBT **716.646.735.403**, current tax **153.565.492.375**, deferred tax benefit **11.263.775.631** (normalized to tax expense **-11.263.775.631**), total tax **142.301.716.744**, PAT **574.345.018.659**, parent PAT **511.013.714.299**, NCI **63.331.304.360**, EPS **1.549**. Gross profit, operating profit, other profit, PBT, tax, PAT and parent/NCI bridges exact.
- B03 original 9M YTD raw VND: CFO **3.581.088.955.857**, CFI **-1.308.653.005.272**, CFF **-2.318.597.493.209**, net cash change **-46.161.542.624**, opening cash **1.333.592.588.129**, FX **168.562.373**, closing cash **1.287.599.607.878**. H1 original Q2/2024 YTD baseline (document 471540): CFO **2.296.007.290.628**, CFI **-724.113.031.201**, CFF **-1.895.302.679.995**, net change **-323.408.420.568**, FX **233.255.231**, closing cash **1.010.417.422.792**.
- Standalone Q3 = 9M YTD minus H1 YTD: CFO **1.285.081.665.229 VND**, CFI **-584.539.974.071**, CFF **-423.294.813.214**, net cash change **277.246.877.944**, FX **-64.692.858**, opening cash **1.010.417.422.792**, closing cash **1.287.599.607.878**. Original 9M and standalone flow/cash bridge residuals all 0; opening equals prior Q2 close.
- The dataset retains the Q3/2025 later comparative cashflow basis at top level. Original Q3/2024 source values are stored separately in `source_validation.original_q3_2024_cashflow_ytd_raw_vnd` and `cashflow_source_reconciliation.original_q3_2024_report_comparison`; do not overwrite selected top-level fields or re-run the prior reclassification decision.
- Q3 status: source-text B01/B02/B03 bridges PASS; direct visual review PENDING; Q1 selling-expense detail exception continues separately. Data commit `893ce88fcfe6d0ba471d489379ef735c0722e582`.
- Resume at **IDC Q4/2024** using archive `reports/raw/IDC/auto-idc-20261021/00983465c42328c1.zip`. Do not repeat Q1–Q3 core source-text extraction.

### 10.12 IDC Q4/2024 — B01/B02 PASS, B03 gốc PENDING

- Nguồn: VietstockFinance document ID **490209**, BCTC hợp nhất; ZIP `https://static2.vietstock.vn/data/HNX/2024/BCTC/VN/QUY%204/IDC_Baocaotaichinh_Q4_2024_Hopnhat.zip`; archive `reports/raw/IDC/auto-idc-20261021/00983465c42328c1.zip`; sidecar `.zip.extracted.json`; 4 PDF members, 65 pages for each financial statement PDF. Đã kiểm tra cả member tiếng Anh `3_idc_2025_1_24_c3431d7_en_financialstatementshn_q4_2024.pdf` và tiếng Việt `4_idc_2025_1_24_f1a5641_vi_baocaotaichinhhn_q4_2024.pdf`, sidecar pages 8–14. Chưa xem ảnh trực quan.
- B01: current assets **7.422.043.183.221 VND**, non-current assets **11.377.492.474.012**, total assets **18.799.535.657.233**; current liabilities **4.531.970.587.537**, long-term liabilities **7.059.151.892.321**, total liabilities **11.591.122.479.858**, equity **7.208.413.177.375**. Tổng tài sản = nợ + vốn, tài sản ngắn + dài hạn và nợ ngắn + dài hạn; residual 0.
- B02 riêng Q4: revenue **1.955.334.917.901 VND**, COGS **1.319.550.083.434**, gross profit **635.784.834.467**, financial income **53.145.593.297**, financial expense **31.858.246.989**, interest expense **31.068.071.520**, share profit associates **-101.265.684**, selling expense **26.189.134.459**, admin expense **99.181.504.269**, operating profit **531.600.276.363**, other income **13.300.388.998**, other expense **5.260.441.516**, other profit **8.039.947.482**, PBT **539.640.223.845**, current tax **99.494.321.537**, deferred tax expense **2.417.678.111**, total tax **101.911.999.648**, PAT **437.728.224.197**, parent PAT **357.719.490.841**, NCI **80.008.733.356**, EPS **1.084**. Gross, operating, other profit, PBT, tax, PAT and parent/NCI checks all residual 0. Note: exact total tax is 101,911,999,648 VND; one million VND less than the earlier mistaken manual arithmetic candidate, now corrected in data.
- B03 source text OCR current-year FY2024 candidate values: CFO **3.884.016.207.794 VND**, CFI **-1.274.480.840.372**, CFF **-1.377.656.623.723**, reported net cash change **246.158.916.275**, opening cash **1.333.592.588.129**, FX **238.428.862**, closing cash **2.188.038.807.308**. These do **not** reconcile: CFO+CFI+CFF minus net change residual **985.719.827.424 VND**; cash bridge residual **-608.048.874.042 VND**. The same flow residual carries into diagnostic standalone Q4 deltas (FY2024 YTD less Q3/2024 YTD): CFO **302.927.251.937**, CFI **34.172.164.900**, CFF **940.940.869.486**, net **292.320.458.899**, FX **69.866.489**, opening **1.287.599.607.878**, closing **2.188.038.807.308**. Those derived figures are diagnostic only; do not promote to canonical quarter or insert a plug.
- Existing top-level Q4/2024 cashflow remains on the selected FY2025 comparative basis already stored in `cashflow_source_reconciliation`; this selected basis is not overwritten. Original FY2024 B03 sidecar values and residuals are preserved separately in `source_validation.original_q4_2024_cashflow_ytd_raw_vnd` and `original_cashflow_issue`.
- Status: B01/B02 source-text PASS, original B03 PENDING due material OCR/source-text inconsistency; visual review all statements PENDING. Data commit `fcfd329c7790da1c72b2bb5cf7a4c77d5aa75760`.
- Theo thứ tự kỳ, tiếp tục **IDC Q1/2025** từ archive `reports/raw/IDC/auto-idc-20261021/5b3809b3492cb8ac.pdf`. Không làm lại Q1–Q4/2024 core text extraction; giữ các ngoại lệ Q1/2024 selling expense và Q4/2024 original B03.

### 10.13 IDC Q1/2025 — B01/B02/B03 gốc đã đối chiếu, visual pending

- Nguồn: VietstockFinance document ID **503692**, PDF hợp nhất `https://static2.vietstock.vn/data/HNX/2025/BCTC/VN/QUY%201/IDC_Baocaotaichinh_Q1_2025_Hopnhat.pdf`; archive `reports/raw/IDC/auto-idc-20261021/5b3809b3492cb8ac.pdf`; sidecar `.pdf.extracted.json`; 62 trang. Đã đọc sidecar pages 9–14: B01 printed pages 4–6 (sidecar p9–11), B02 printed p7 (sidecar p12), B03 printed p8–9 (sidecar p13–14). Không visual verified.
- B01: current assets **8.117.308.377.501 VND**, non-current assets **11.293.159.720.202**, total assets **19.410.468.097.703**; current liabilities **5.348.738.935.759**, long-term liabilities **6.932.096.358.950**, total liabilities **12.280.835.294.709**, equity **7.129.632.802.994**. Tất cả phương trình tài sản/ngắn+dài hạn/nợ/vốn residual 0.
- B02 riêng Q1: revenue **1.793.484.296.130 VND**, COGS **1.242.093.459.547**, gross profit **551.390.836.583**, financial income **65.100.177.990**, financial expense **39.020.337.473**, interest expense **36.064.081.688**, share profit associates **360.482.572**, selling expense **28.332.542.856**, admin expense **73.940.266.707**, operating profit **475.558.350.109**, other income **48.854.110.556**, other expense **3.703.813.460**, other profit **45.150.297.096**, PBT **520.708.647.205**, current tax **108.547.172.018**, deferred tax income **4.823.069.417** (normalized tax expense **-4.823.069.417**), total tax **103.724.102.601**, PAT **416.984.544.604**, parent PAT **343.278.910.627**, NCI **73.705.633.977**, EPS **1.040**. All row bridges and parent/NCI allocation residual 0.
- B03 Q1/2025: CFO **593.194.330.719 VND**, CFI **-745.138.695.014**, CFF **256.704.039.546**, net cash change **104.759.675.251**, opening cash **2.188.037.806.317**, FX **2.753.952**, closing cash **2.292.800.235.520**. Flow/cash bridge residuals 0; closing cash equals B01 cash and equivalents.
- Cross-period: Q1/2025 B01 comparative opening 31/12/2024 shows total assets **18.800.160.505.704 VND**, liabilities **11.592.512.353.814**, equity **7.207.648.151.890**. Compared with original Q4/2024 B01: assets **+624.848.471**, liabilities **+1.389.873.956**, equity **-765.025.485 VND**. Retain both bases; no overwrite of Q4 source. Q1 B03 opening cash is **2.188.037.806.317 VND**, which is **1.000.991 VND** below Q4 original B01 closing cash **2.188.038.807.308** (relative difference **0,00004575%**); within the 0,01% tolerance, both source values retained unchanged.
- Q1/2025 comparative P&L column for Q1/2024 differs materially from original Q1/2024 report values; do not use the comparative to overwrite the original Q1/2024 record.
- Status: B01/B02/B03 source-text PASS, all residuals 0; only cross-period cash opening difference within tolerance, and direct visual review pending. Data commit `089b64d44e884dd6ff31ae3650a1fc41f93eb3b9`.
- Next: **IDC Q2/2025**, archive `reports/raw/IDC/auto-idc-20261021/48616c2bb9d17c99.zip`. Do not repeat IDC Q1/2025 text extraction or completed 2024 core statements.

### 10.14 IDC Q2/2025 — B01/B02/B03 source-text reconciled; English member resolves OCR

- Nguồn chính VietstockFinance document ID **514037**, BCTC hợp nhất Q2/2025; ZIP `https://static2.vietstock.vn/data/HNX/2025/BCTC/VN/QUY%202/IDC_Baocaotaichinh_Q2_2025_Hopnhat.zip`; archive `reports/raw/IDC/auto-idc-20261021/48616c2bb9d17c99.zip`; sidecar `.zip.extracted.json`; 63 trang. Đã đọc cả member tiếng Việt `4_idc_2025_7_30_caaaf64_vi_baocaotaichinhhn_q2_2025_s.pdf` và member tiếng Anh `1_idc_2025_7_30_2e1316b_en_financialstatementshn_q2_2025_s.pdf`; B01 sidecar pages 8–11, B02 p12, B03 p13–14. Visual review vẫn PENDING.
- B01 30/6/2025: current assets **7.811.294.674.643 VND**, non-current assets **11.795.122.370.205**, total assets **19.606.417.044.848**; current liabilities **3.669.554.755.411**, non-current liabilities **8.481.390.563.394**, total liabilities **12.150.945.318.805**, equity **7.455.471.726.043**. Tất cả tổng phụ và phương trình tài sản = nợ + vốn residual 0.
- B02 Q2 riêng: revenue **1.763.197.891.011 VND**, COGS **1.218.680.135.812**, gross profit **544.517.755.199**, financial income **62.954.887.826**, financial expense **29.939.147.355**, associate loss **343.427.723**, selling expense **21.450.520.742**, admin expense **64.454.735.514**, operating profit **491.284.811.691**, other income **29.086.228.155**, other expense **1.046.602.608**, other profit **28.039.625.547**, PBT **519.324.437.238**, current tax expense **102.821.214.554**, deferred tax expense (normalized) **539.315.464**, total tax expense **103.360.530.018**, PAT **415.963.907.220**, parent PAT **297.573.101.125**, NCI **118.390.806.095**, EPS **902**. All row bridges, PBT-tax-PAT and parent+NCI residuals are zero.
- OCR correction: Vietnamese member had read deferred-tax row 17 as **639.315.464 VND** and Q2 NCI as **118.350.806.095 VND**. The English-language financial-statement member in the same VietstockFinance ZIP explicitly reads row17 **(539.315.464 VND)** and row20 **118.390.806.095 VND**. The parentheses on “Deferred tax income” means deferred tax expense +539.315.464 VND after normalizing to tax-expense convention. This makes total tax 103.360.530.018 VND and PAT 415.963.907.220 VND exactly; parent+NCI also exactly equals PAT. The former 100m VND tax bridge discrepancy and 40m NCI difference are resolved by the same-source English member; no plug used.
- H1/2025 B02: PBT **1.040.033.084.443 VND**, current tax expense **211.368.386.572**, deferred-tax income **4.283.753.953** (normalized tax expense -4.283.753.953), PAT **832.948.451.824**, parent PAT **640.852.011.752**. The H1 NCI OCR token is truncated at its leading digits; implied H1 NCI = PAT - parent = **192.096.440.072 VND**. This derived value minus Q1 original NCI **73.705.633.977** equals Q2 source NCI **118.390.806.095** exactly. Retain it only as a derived cross-check; do not label it direct OCR.
- Original Q2 report B03 H1 YTD VND: CFO **1.402.209.397.523**, CFI **-2.438.216.817.714**, CFF **-288.817.920.091**, net cash change **-1.324.825.340.282**, opening cash **2.188.037.806.317**, FX **41.467.072**, closing cash **863.253.933.107**. Flow and cash bridge residual 0.
- Original Q2 standalone = H1 YTD less original Q1 YTD: CFO **809.015.066.804**, CFI **-1.693.078.122.700**, CFF **-545.521.959.637**, net cash change **-1.429.585.015.533**, opening cash **2.292.800.235.520**, FX **38.713.120**, closing cash **863.253.933.107**. Flow and cash bridge residual 0.
- Selected top-level B03 basis remains the later VietstockFinance Q2/2026 comparative `As restated – Note 41` for H1/2025: YTD CFO **876.372.147.509**, CFI **-1.912.379.567.700**, CFF **-288.817.920.091**, net **-1.324.825.340.282**, FX **41.467.072**, opening **2.188.037.806.317**, closing **863.253.933.107**. Standalone Q2 on that selected basis: CFO **283.177.816.790**, CFI **-1.167.240.872.686**, CFF **-545.521.959.637**, net **-1.429.585.015.533**, FX **38.713.120**, opening **2.292.800.235.520**, close **863.253.933.107**. Both original and restated flow/cash bridges are exact. Reclassification moves **525.837.250.014 VND** from CFO to CFI, net cash unchanged; preserve both bases separately and do not overwrite selected top-level restated values.
- Data commit **`8c423863c36ea66480a3633ba0beb3919cff3d33`**. Status: core source-text complete; visual PENDING. The user directed continue; next period is **IDC Q3/2025** from archive `reports/raw/IDC/auto-idc-20261021/04ff7104fec1b3fd.zip`. Do not repeat Q1/Q2 extraction.

### 10.15 IDC Q3/2025 — B01/B02/B03 đã kiểm tra trực quan bằng ảnh PDF

- Nguồn: VietstockFinance document ID **523494**, BCTC hợp nhất IDC Q3/2025; ZIP lưu tại `reports/raw/IDC/auto-idc-20261021/04ff7104fec1b3fd.zip`. PDF tiếng Anh được chọn đúng member `4_idc_2025_10_30_de24c2b_en_financialstatementshn_q3_2025hn_s.pdf`; URL trực tiếp: `https://static2.vietstock.vn/data/HNX/2025/BCTC/VN/QUY%203/IDC_Baocaotaichinh_Q3_2025_Hopnhat/4_idc_2025_10_30_de24c2b_en_financialstatementshn_q3_2025hn_s.pdf`.
- Công cụ xem PDF dùng chung: `.github/workflows/render-vietstock-source-pages.yml`. Workflow nhận `symbol`, `period`, `pdf_path` (PDF hoặc ZIP đã lưu trong `reports/raw`), `pdf_member` (tên PDF chính xác trong ZIP), `pages` (số trang PDF, bắt đầu từ 1) và `dpi`. Dùng PyMuPDF kết xuất PNG và ảnh ghép; upload artifact 14 ngày; lưu tọa độ artifact vào thư mục nguồn. Chọn đúng PDF member khi ZIP có nhiều PDF; không chọn tự động theo tên nếu chưa xác định được member hợp nhất/riêng lẻ.
- Cấu hình chạy cho IDC Q3/2025: PDF member tiếng Anh nêu trên; trang PDF **8–14**; **180 DPI**. GitHub Actions run **41690820936**, artifact **13257427801**, tên `vietstock-source-review-IDC-2025-Q3`; metadata `reports/raw/IDC/auto-idc-20261021/render-metadata-2025-Q3.json`. Ảnh PNG trang 08–14 được lưu trong artifact, không đưa ảnh nặng vào Git history.
- Đã xem trực tiếp ảnh: B01 PDF trang 8–11 (trang in 3–6), B02 trang 12 (trang in 7), B03 trang 13–14 (trang in 8–9). B01 tổng tài sản **21.293.030.253.931 VND**, tổng nợ **12.926.247.964.300 VND**, vốn chủ **8.366.782.289.631 VND**; nợ + vốn = tài sản, residual **0 VND**. Cộng tài sản ngắn hạn + dài hạn residual 0. Dòng 440 bị con dấu công ty che một phần; không chép số OCR lỗi, không ghi nhận sai lệch 71.700 VND trước đây, không dùng số suy ra làm giá trị nguồn.
- B02 cột riêng Q3/2025: doanh thu thuần **2.871.329.472.687 VND**; giá vốn **1.614.206.888.266**; lợi nhuận gộp **1.257.122.584.421**; thu nhập tài chính **84.797.217.769**; chi phí tài chính **34.133.582.233**; lãi vay **33.912.013.940**; lỗ công ty liên kết **139.003.519**; chi phí bán hàng **26.561.121.573**; chi phí quản lý **70.669.003.009**; lợi nhuận hoạt động **1.210.417.091.856**; lợi nhuận khác **8.075.636.171**; LNTT **1.218.492.728.027**; chi phí thuế hiện hành **265.623.067.711**; thu nhập thuế hoãn lại **28.267.841.672**; LNST **981.137.501.988**; LNST mẹ **841.835.881.584**; NCI **139.301.620.404**; EPS cơ bản và pha loãng **2.218**. Các cầu nối B02 đều residual 0.
- B03: đã sửa cách chuẩn hóa quý riêng bằng cách lấy 9M/2025 từ báo cáo Q3 trừ H1/2025 từ báo cáo Q2/2025 **trên cùng cơ sở báo cáo gốc**. Không trộn số 9M chưa phân loại lại với comparative H1 “As restated” từ Q2/2026. Q3 riêng raw VND: CFO **1.541.531.404.357**; CFI **-2.242.302.344.954**; CFF **629.179.666.426**; biến động tiền **-71.591.274.171**; FX **23.900.983**; tiền đầu quý **863.253.933.107**; cuối quý **791.686.559.919**; capex **-893.695.067.506**; cổ tức đã trả **-57.513.573.250**. Flow và cash bridge residual **0 VND**. Comparative H1 As-restated được lưu thành basis riêng.
- Lỗi OCR cũ `cost_of_goods_sold_gross_profit_equation_check` được gỡ sau khi đối chiếu ảnh: doanh thu thuần − giá vốn = lợi nhuận gộp chính xác. Placeholder EPS 70 vẫn chỉ được giữ trong lịch sử rejected values; EPS đang dùng là 2.218 theo ảnh gốc.
- Data commit **`e91771b408d175231b3eb57efcb146d475cc52ce`**. Trạng thái kỳ: **B01/B02/B03 source + visual review PASS**, ngoại lệ nhỏ duy nhất là dòng 440 bị con dấu che một phần nhưng phương trình tổng độc lập đạt chính xác. Không trích xuất lõi lại. Tiếp theo: **IDC Q4/2025**.
 
## 12. Kết xuất và kiểm tra ảnh PDF từ kho báo cáo

- Mục đích: thay việc phụ thuộc vào PDF viewer/screenshot endpoint có giới hạn dung lượng. Workflow `.github/workflows/render-vietstock-source-pages.yml` đọc trực tiếp PDF hoặc PDF member trong ZIP đã lưu ở repository, dùng PyMuPDF render từng trang thành PNG, tạo contact sheet và upload artifact tạm thời. Không thay snapshot, không chạy OCR và không đụng tới pipeline cập nhật dữ liệu tài chính.
- Dùng `workflow_dispatch` để chọn mã/kỳ/tệp/trang/DPI. Đối với PDF trong ZIP, phải truyền `pdf_member` đúng tên file PDF cần xem, nhằm phân biệt hợp nhất và riêng lẻ. `pages` là số trang PDF 1-based; trang in trên báo cáo có thể khác số trang PDF. Khi cần kích hoạt từ commit, sửa đúng cấu hình mặc định của workflow rồi commit vì workflow có trigger push theo chính file workflow; sau khi chạy xong phải trả default về mã/kỳ cần tiếp theo, không để workflow chạy nhầm kỳ. Không được sửa hoặc kích hoạt workflow đồng bộ dữ liệu tài chính để kết xuất ảnh.
- Sau khi chạy: xác nhận job **Render source pages and contact sheets** và **Upload rendered source pages** thành công; tải artifact bằng tọa độ run/artifact đã ghi trong `render-metadata-*.json`; kiểm tra ảnh PNG từng trang, không chỉ xem OCR/contact sheet. Lưu run ID, artifact ID, PDF member, trang, DPI và SHA-256 ảnh vào kiểm toán kỳ.
- Artifact mặc định giữ **14 ngày**; đây là bằng chứng tạm thời. Các kết luận số liệu và hash/trạng thái kiểm tra phải được ghi vào snapshot/checkpoint hoặc ghi chú phân tích lâu dài trước khi artifact hết hạn.
- Chỉ đổi trạng thái sang visual-reviewed sau khi ảnh của đúng PDF member, đúng kỳ, đúng phạm vi và đúng cột số liệu đã được mở xem. Nếu con dấu/chữ ký che số, đánh dấu trường đó unreadable/partially obscured; không suy diễn hoặc dùng phép cân đối để gán giá trị vào trường nguồn.
- Với file quá lớn làm viewer không mở được, dùng workflow này thay vì lặp lại yêu cầu người dùng tải PDF. Ưu tiên archive đã lưu từ VietstockFinance; nếu chỉ có URL trực tiếp thì lưu nguồn trước theo quy trình thu thập hiện hành, sau đó mới kết xuất trang.
- **Quy trình áp dụng từng kỳ**: (1) lấy kỳ đầu tiên chưa đóng theo checkpoint; (2) kiểm tra snapshot, sidecar và nguồn hiện có, không OCR lại dữ liệu đã có; (3) chọn đúng PDF hợp nhất và xác định số trang B01/B02/B03 từ sidecar; (4) kết xuất đúng các trang ở 180 DPI; (5) xem trực tiếp từng ảnh, zoom các dòng tổng/thuế/EPS/dòng tiền/dấu âm; (6) chỉ sửa trường có bằng chứng ảnh rõ; (7) kiểm tra phương trình từng bảng và chuẩn hóa quý riêng bằng cùng một cơ sở YTD; (8) lưu manifest/hash/ảnh bằng chứng dưới artifact, ghi báo cáo phân tích và checkpoint; (9) commit dữ liệu + SOP/checkpoint; (10) đọc lại file sau commit để xác nhận rồi mới chuyển kỳ. Mỗi lần một mã/kỳ; không chuyển khi kỳ đang xử lý còn ngoại lệ cốt lõi chưa được xử lý hoặc đánh dấu rõ.
- **Lịch sử áp dụng đầu tiên**: IDC Q3/2025 được render 180 DPI, PDF pages 8–14, workflow run 41690820936, artifact 13257427801. B01/B02/B03 visual PASS; dòng 440 bị con dấu che một phần, không chép OCR. Data commit `e91771b408d175231b3eb57efcb146d475cc52ce`; checkpoint commit `6cc189cbb11d983763ecad5041d52994b1deecf1`; visual report `reports/analysis/IDC-Q3-2025-visual-review.md`.


### 10.16 IDC Q4/2025 — B01/B02/B03 visual PASS; FX corrected; source subline exception retained

- Nguồn: VietstockFinance document ID **529902**, BCTC hợp nhất IDC Q4/2025; ZIP `reports/raw/IDC/auto-idc-20261021/5ff8f3ce069a369e.zip`; member PDF tiếng Anh `1_idc_2026_1_29_0d3041b_en_financialstatementshn_q4_2025hn_s.pdf`, 67 trang.
- Kết xuất ảnh: PDF pages **8–14**, 180 DPI; B01 8–11, B02 12, B03 13–14. GitHub Actions run **41693037890**, artifact **13257699370**, artifact name `vietstock-source-review-IDC-2025-Q4`, ZIP digest `sha256:231a4774ff398d0509dbc6630474f13a5ce9ab301c129ea877cb822d2b6915b8`. Metadata `reports/raw/IDC/auto-idc-20261021/render-metadata-2025-Q4.json`.
- B01: tổng tài sản **23.201.490.679.523 VND**; tài sản ngắn hạn **9.856.822.003.191**; tài sản dài hạn **13.344.668.676.332**; nợ phải trả **14.938.459.787.767**; nợ ngắn hạn **5.620.500.395.796**; nợ dài hạn **9.317.959.391.971**; vốn chủ **8.263.030.891.756**. Dòng 440 đọc được rõ **23.201.490.679.523 VND**. Các tổng phụ và phương trình tổng tài sản = nợ + vốn đều residual **0 VND**.
- B01 row 120 đầu tư ngắn hạn được ảnh trang 8 xác nhận là **6.807.014.517.859 VND**. Thay OCR/parser candidate sai **909.607 triệu** bằng **6.807.015 triệu VND**; tổng tài sản ngắn hạn cộng các cấu phần vẫn khớp.
- B02 dùng đúng cột **Quý IV/2025 riêng**, không dùng số cả năm: doanh thu thuần **2.160.138.111.718 VND**; giá vốn **1.453.163.128.638**; lợi nhuận gộp **706.974.983.080**; doanh thu tài chính **108.952.409.062**; chi phí tài chính **42.472.227.098**; lãi công ty liên kết **180.518.355**; chi phí bán hàng **18.592.495.992**; quản lý **92.138.853.752**; lợi nhuận hoạt động **662.904.333.655**; lợi nhuận khác **-3.684.745.622**; LNTT **659.219.588.033**; thuế hiện hành **142.577.559.905**; thu nhập thuế hoãn lại **23.353.093.110**; LNST **539.995.121.238**; LNST mẹ **449.103.567.116**; NCI **90.891.554.122**; EPS cơ bản/pha loãng **1.183/1.183**. Các cầu nối tổng lợi nhuận, thuế, PAT và phân bổ mẹ/NCI đều residual 0.
- **Ngoại lệ báo cáo nguồn B02**: dòng 23 “In which: interest expense” in rõ **(43.891.490.863 VND)**, trong khi dòng 22 tổng chi phí tài chính là **(42.472.227.098 VND)**. Chi phí lãi vay con in cao hơn tổng chi phí tài chính **1.419.263.765 VND**. Giữ số con đã nhìn thấy trên PDF với cờ ngoại lệ nguồn; không tự sửa số đó, không ép tổng chi phí tài chính/lợi nhuận thay đổi và không dùng dòng con này để tính lợi nhuận hoạt động. Đây là mâu thuẫn của báo cáo được phát hành, không còn là lỗi OCR.
- B03 ảnh trang 14 xác nhận FX **FY2025 = 62.830.651 VND**; **91.523.594 VND** thuộc cột FY2024 so sánh. OCR trước đã lấy nhầm FX comparative làm giá trị hiện tại, khiến cash bridge sai **28.692.943 VND**. Đã sửa FX YTD về **62.830.651 VND** và Q4 riêng = **62.830.651 − 65.368.055 = -2.537.404 VND**.
- B03 FY2025 raw VND: CFO **3.913.940.809.873**, CFI **-7.009.893.958.684**, CFF **1.460.905.190.082**, net cash change **-1.635.047.958.729**, opening cash **2.188.037.806.317**, FX **62.830.651**, closing cash **553.052.678.239**. Flow bridge và cash bridge residual **0 VND**.
- Q4 standalone = FY2025 YTD − 9M/2025 YTD từ IDC Q3/2025 cùng cơ sở báo cáo gốc: CFO **970.200.007.993**, CFI **-2.329.374.796.016**, CFF **1.120.543.443.747**, net change **-238.631.344.276**, FX **-2.537.404**, opening **791.686.559.919**, ending **553.052.678.239**; capex **-1.300.428.928.495**; dividends paid **-654.131.953.577**. Flow and cash bridges residual **0 VND**, opening cash equals Q3 closing cash.
- Dữ liệu commit **`c9a45a3606f209e12df00856f97e8c12eaed27dc`**. Visual review: PASS; B02 has one reported source exception explicitly recorded. Next quarter is **IDC Q1/2026**. Do not re-extract Q4/2025.
 
### 10.17 IDC Q1/2026 — B01/B02/B03 visual PASS; EPS comparative-column correction

- Nguồn VietstockFinance: BCTC hợp nhất IDC Q1/2026; PDF lưu tại `reports/raw/IDC/auto-idc-20261021/229a1ff9af9d3e1b.pdf`; URL `https://static2.vietstock.vn/data/HNX/2026/BCTC/VN/QUY%201/IDC_Baocaotaichinh_Q1_2026_Hopnhat.pdf`.
- Kết xuất: PDF pages **8–14** ở 180 DPI; workflow run **41694161229**, artifact **13258496176**, digest `16f7b72e32ada60f564b478a7119f96cbc79b3eb64cf324c3aa5a2893901516d`.
- B01 raw VND: current assets **10.087.525.251.101**, cash **800.729.495.703**, short-term investments **6.841.660.868.866**, short-term receivables **1.039.082.103.804**, inventory **1.336.544.952.533**, other current assets **69.507.830.195**, non-current assets **13.451.977.379.319**, fixed assets **2.875.737.262.368**, total assets **23.539.502.630.420**, current liabilities **5.593.032.195.552**, long-term liabilities **9.096.732.263.053**, total liabilities **14.689.764.458.605**, equity **8.849.738.171.815**. Row 440 equals total assets. All balance/component bridges residual 0.
- B02 Q1-only raw VND: revenue net **1.485.524.640.421**, COGS **-1.096.785.999.513**, gross profit **388.738.640.908**, finance income **131.515.653.570**, finance expenses **-58.967.381.247**, interest expense **-58.741.206.811**, share profit associates **407.741.448**, selling expenses **-18.525.479.401**, administrative expenses **-53.853.448.503**, operating profit **389.315.726.775**, other income **32.552.495.178**, other expenses **-1.571.094.975**, other profit **30.981.400.203**, PBT **420.297.126.978**, current tax **-83.687.912.608**, deferred tax income **1.297.966.689** (normalize tax expense convention as **-1.297.966.689**), PAT **337.907.181.059**, parent PAT **270.595.917.639**, NCI **67.311.263.420**. EPS basic/diluted **713/713**.
- **EPS column correction:** B02 first numeric column is Q1/2026 and contains EPS **713**. EPS **902** belongs to the comparative Q1/2025 column; do not retain 902 in Q1/2026. Correct and remove false parser candidates for selling expense **217** and operating profit **981**, which are not the source values.
- B03 Q1 is also YTD: CFO **197.524.137.001**, CFI **-68.608.251.477**, CFF **118.757.627.185**, net cash increase **247.673.512.709**, opening cash **553.052.678.239**, FX **3.304.755**, closing cash **800.729.495.703**, capex **-271.870.359.512**, dividends paid **-36.631.499.200**. Flow/cash bridges residual 0; opening cash equals Q4/2025 close.
- Snapshot commit **`cb98a0bfc9127c3e78eafa23466ec08fcd57f1fe`**; visual audit note `reports/analysis/IDC-Q1-2026-visual-review.md`, commit **`0e72dafe1d5ecc5b4e56442b24911d109fb9ef70`**. Status: B01/B02/B03 visual PASS. Next: **IDC Q2/2026**. Do not re-extract Q1/2026.

### 10.18 IDC Q2/2026 — B01/B02 visual PASS; B03 YTD PASS; Q2 cash bridge exception > 0.01%

- Nguồn: VietstockFinance document ID **556340**, BCTC hợp nhất IDC Q2/2026; ZIP `reports/raw/IDC/auto-idc-20261021/5e5637e71fa303a7.zip`; PDF tiếng Anh `2_idc_2026_7_31_a5004ca_en_financialstatementshn_q2_2026_s.pdf`, 67 trang. PDF pages **8–14** đã render và xem trực tiếp ở 180 DPI.
- Workflow run **41695506922**, artifact **13261640367**, SHA-256 `cc511d5804b930f5df2b3be6e08fa6a74df55581d368e4a7fa89090fce8f2241`. Metadata path `reports/raw/IDC/auto-idc-20261021/render-metadata-2026-Q2.json`.
- B01 30/06/2026 raw VND: current assets **16.424.882.607.866**; cash **608.684.579.632**; short-term investments **6.612.747.709.157**; current receivables **1.398.487.922.279**; inventory **7.737.431.153.217**; other current assets **67.531.243.581**; non-current assets **7.121.143.339.714**; fixed assets **2.828.137.956.093**; total assets **23.546.025.947.580**; current liabilities **5.609.121.115.090**; long-term liabilities **9.106.756.094.816**; total liabilities **14.715.877.209.906**; equity **8.830.148.737.674**; retained earnings **2.025.264.569.190**. Row 440 = total assets. B01 equations residual 0.
- B02 top-level must use first numeric column **Quý II/2026**, not H1 YTD: net revenue **2.270.489.379.557**, COGS **-1.421.483.331.885**, gross profit **849.006.047.672**, finance income **144.735.815.482**, finance expense **-56.657.259.572**, interest expense **-56.420.402.688**, selling **-22.117.041.607**, admin **-67.646.607.403**, associate profit **419.004.202**, operating profit **847.739.958.774**, other income **706.442.579**, other expense **-15.511.032.827**, other profit **-14.804.590.248**, PBT **832.935.368.526**, current tax **-179.411.251.901**, deferred-tax income **9.809.689.654**, PAT **663.333.806.279**, parent **609.810.412.292**, NCI **53.523.393.987**, EPS basic/diluted **1.461/1.461**. H1/2026 YTD figures must remain separately preserved in `income_statement_source_ytd_raw_vnd`; do not use 6-month cumulative amounts as quarter-only snapshot values. B02 bridges all residual 0.
- B03 H1/2026 current column raw VND: CFO **-5.019.037.910**, CFI **412.225.133.057**, CFF **-352.471.108.238**, net cash increase **54.734.986.909**, opening cash **553.943.475.131**, FX **6.117.592**, closing cash **608.684.579.632**, capex **-158.418.483.835**, dividends **-74.115.054.425**. H1/YTD flow and cash bridges residual 0. Do not confuse with H1/2025 comparative explicitly marked **As restated – Note 41**.
- Q2 standalone flows from H1 2026 YTD minus Q1/2026 original YTD: CFO **-202.543.174.911**, CFI **480.833.384.534**, CFF **-471.228.735.423**, net cash **-192.938.525.800**, FX **2.812.837**; opening cash from Q1 close **800.729.495.703**; ending cash from Q2 B01/B03 **608.684.579.632**. Flow-component residual **0**. Q2 capex line 21 delta = **+113.451.875.677 VND**; treat as a raw same-YTD-basis difference, retain note because the sign reverses relative to the H1 reported capex and Q1 separate line. Dividends paid Q2 delta **-37.483.555.225 VND**.
- **Open cash-basis exception:** Q2 report H1 opening cash **553.943.475.131 VND** is the 31/12/2025 “As restated” comparative and exceeds original Q4/2025 close **553.052.678.239** by **890.796.892 VND**. Q1/2026 report B03 closing cash is **800.729.495.703 VND**. Using this Q1 close as Q2 opening, Q2 cash bridge residual = **-890.796.892 VND**, or **0,1463%** of Q2 closing cash, exceeding the 0,01% tolerance. H1/YTD bridge is exact. Preserve source values, no plug, mark Q2 standalone cash bridge `NEEDS_MANUAL_REVIEW_CROSS_PERIOD_CASH_BASIS`. Do not claim full cashflow PASS just because H1/YTD balances.
- Data commit **`1f1449355dd200ccba8b77fa5e91024980078362`**; audit note `reports/analysis/IDC-Q2-2026-visual-review.md`, commit **`38990c3482aabb99c41f8b6bfe5d4db82deb231b`**. Status: B01/B02 visual PASS; B03 H1 PASS; Q2 standalone cash bridge exception pending source-basis reconciliation. Continue only after the discrepancy is resolved from a later/alternate VietstockFinance source or is explicitly closed as a documented issuer restatement exception; never insert a balancing adjustment.

### 10.19 IDC Q1/2024 — B01/B02/B03 visual PASS; sửa lẫn cột so sánh

- Nguồn VietstockFinance document ID **462783**, BCTC hợp nhất Q1/2024; PDF `reports/raw/IDC/auto-idc-20261021/44694a289f32bd8c.pdf`.
- Render tại 180 DPI: PDF pages **9–15**, B01 9–12, B02 13, B03 14–15. Workflow run **41698364477**, artifact **13262217679**, SHA-256 `f335e18d8c2894b33bcf3c7593fbc98950434e42937233f528b0217baa7c7da9`.
- **Quy tắc column mapping bắt buộc:** trước khi chọn hoặc sửa bất kỳ số nào, đọc tiêu đề của toàn bộ các cột tại đầu bảng (kỳ hiện hành / kỳ so sánh; quý / lũy kế). Đánh dấu riêng cột hiện hành và cột comparative rồi trích xuất toàn bộ dòng của cùng một cột. Không ghép từng giá trị “có vẻ hợp lý” từ các cột khác nhau. Sau đó mới kiểm tra cầu nối; nếu residual bất thường, quay lại ảnh và kiểm tra thứ tự cột trước khi kết luận nguồn sai.
- B01 raw VND: current assets **6.149.122.173.715**, cash **1.108.047.375.757**, short-term investments **966.774.198.900**, receivables **2.168.567.501.270**, inventory **1.858.248.737.055**, other current assets **47.484.360.733**, non-current assets **11.237.270.117.635**, fixed assets **3.155.290.701.843**, total assets **17.386.392.291.350**, current liabilities **3.519.203.176.880**, long-term liabilities **7.375.093.997.091**, total liabilities **10.894.297.173.971**, equity **6.492.095.117.379**, retained earnings **1.073.735.920.975**. Row 440 equals total assets; all B01 equations residual **0**.
- B02 current Q1/2024 raw VND: revenue **2.467.056.536.161**, COGS **-1.368.769.156.854**, gross profit **1.098.287.379.307**, finance income **30.956.011.616**, finance expense **-34.736.078.687**, interest expense **-34.575.846.071**, associates profit **80.805.520**, selling **-41.894.251.738**, admin **-51.089.217.428**, operating profit **1.001.604.648.590**, other income **1.822.336.145**, other expense **-4.092.556.626**, other profit **-2.270.220.481**, PBT **999.334.428.109**, current tax expense **211.205.688.538**, deferred tax income **9.045.683.826**, total tax expense **202.160.004.712**, PAT **797.174.423.397**, parent PAT **695.138.495.107**, NCI **102.035.928.290**, EPS **2.106**.
- Correction: the prior parser mixed comparative Q1/2023 amounts into current Q1/2024 fields, causing a false **776.003.705.179 VND** operating-profit residual. Visual page 13 confirms selling expenses **41.894.251.738 VND** and admin expense **51.089.217.428 VND**; their correct use yields operating profit **1.001.604.648.590 VND** with residual 0. Current interest expense is **34.575.846.071**, not comparative **53.797.972.876**. Current finance expense **34.736.078.687**, not comparative **53.848.398.253**. Current finance income **30.956.011.616**, not comparative **26.627.940.549**. All B02 profit, tax/PAT and parent/NCI bridges residual 0.
- Subsequent Q1/2025 comparative column now agrees with original Q1/2024 report for the B02 financial statement lines from revenue through NCI. EPS differs: original Q1/2024 **2.106**, later comparative **2.095**; preserve both by source basis and do not overwrite original period.
- B03 Q1/2024 raw VND: CFO **951.312.310.814**, CFI **-154.748.226.063**, CFF **-1.022.256.653.200**, net cash change **-225.692.568.449**, FX **147.356.077**, opening **1.333.592.588.129**, closing **1.108.047.375.757**, capex **-206.983.772.973**, dividends paid **-538.942.833.000**. Q1 is also YTD; flow and cash bridges residual 0.
- Snapshot commit **`166f5b6741c37b6d6197d07b568a9b368ea32185`** (subsequent comparative reconciliation commit **`d583bc324608f22309a9db8a047719af431b8703`**); visual note `reports/analysis/IDC-Q1-2024-visual-review.md`, commit **`989486e261c103174df2f269ce9f65ef8041c39d`**. Status: **B01/B02/B03 PASS**; all residuals zero. Next chronological pending visual review: **IDC Q2/2024**. Do not repeat Q1/2024 extraction.

### 10.20 IDC Q2/2024 — B01/B02/B03 visual PASS; preserve selected Q2/2025 comparative cashflow

- Nguồn VietstockFinance document ID **471540**, BCTC hợp nhất IDC Q2/2024; ZIP `reports/raw/IDC/auto-idc-20261021/ecbef46d7d1d9ff3.zip`; exact PDF member `2_idc_2024_7_30_f164297_741tctbtc_2972024_bctc_hop_nhat_q2_2024_signed.pdf`.
- Render ảnh: PDF pages **9–15** ở **180 DPI**; B01 pages 9–12, B02 page 13, B03 pages 14–15. Workflow run **41760510289**, artifact **13290038262**, digest `sha256:e3bd2cfb013ed4838b4bd8090a754b60b7800d9767ef6dee08205d733afc8cb2`.
- **B01** raw VND tại 30/06/2024: current assets **6.040.235.098.201**; cash **1.010.417.422.792**; short-term investments **1.266.290.583.521**; receivables **2.204.381.350.310**; inventories **1.520.727.568.781**; other current assets **38.418.172.797**; non-current assets **11.504.262.353.656**; fixed assets **3.186.958.999.455**; total assets **17.544.497.451.857**; current liabilities **4.309.098.655.756**; long-term liabilities **7.097.346.081.582**; total liabilities **11.406.444.737.338**; equity **6.138.052.714.519**; retained earnings **658.511.477.246**. Row 440 = total assets; all asset/liability composition and balance equations residual 0.
- **B02** use first current-quarter column **Quý II/2024**, not the prior-year comparative and not the third H1/YTD column. Raw VND: gross revenue **2.148.515.380.308**, deductions **-26.052.352**, net revenue **2.148.489.327.956**, COGS **-1.338.623.411.936**, gross profit **809.865.916.020**, finance income **39.414.434.810**, finance expense **-35.135.290.358**, interest **-33.730.337.375**, associates profit **1.163.120.573**, selling **-27.114.533.189**, admin **-63.864.415.600**, operating profit **724.329.232.256**, other income **13.484.566.343**, other expense **-394.869.489**, other profit **13.089.696.854**, PBT **737.418.929.110**, current tax expense **-174.725.083.274**, deferred-tax income **21.177.039.468**, total tax expense **-153.548.043.806**, PAT **583.870.885.304**, parent PAT **432.484.844.388**, NCI **151.386.040.916**, EPS **1.311**. (Snapshot displays tax magnitude 153.548 million.) All B02 profit, tax/PAT and parent/NCI bridges residual 0.
- **B03 original Q2/2024 H1/YTD** raw VND: CFO **2.296.007.290.628**, CFI **-724.113.031.201**, CFF **-1.895.302.679.995**, net cash **-323.408.420.568**, FX **233.255.231**, opening **1.333.592.588.129**, closing **1.010.417.422.792**, CAPEX row 21 **-313.269.188.925**, dividends paid **-1.425.730.856.390**.
- **Q2 standalone original basis** = original H1/2024 YTD less original Q1/2024 YTD, exact raw VND: CFO **1.344.694.979.814**, CFI **-569.364.805.138**, CFF **-873.046.026.795**, net cash **-97.715.852.119**, FX **85.899.154**, opening **1.108.047.375.757**, ending **1.010.417.422.792**, CAPEX **-106.285.415.952**, dividends **-886.788.023.390**. Original H1 and Q2 standalone flow/cash bridges residual 0; Q2 opening matches Q1 close.
- **Do not overwrite selected top-level cashflow basis:** The snapshot already selects the later VietstockFinance Q2/2025 comparative H1/2024 basis following an identified CFO/CFI presentation reclassification. That selected basis remains top-level (H1 CFO **2.323.895.059.169**, CFI **-752.000.793.208**, CFF **-1.895.302.679.995**, net **-323.408.414.034**, FX **233.248.697**, opening **1.333.592.588.129**, closing **1.010.417.422.792**). Original Q2/2024 B03 is fully visually reviewed and preserved separately under `cashflow_source_reconciliation.original_q2_2024_report_comparison`; never mix the two bases or replace a validated top-level series merely because an alternate source is available.
- Data commit **`3e1e2d067d2ced43803cd078269d52aadd8ff269`**; visual audit `reports/analysis/IDC-Q2-2024-visual-review.md`, commit **`8a84939a3ec45c48e89bace54e501bb95c9e8053`**. Status: B01/B02/B03 original PDF visual PASS; original and selected cashflow bases each reconcile. Next chronological visual period: **IDC Q3/2024**. Do not re-extract Q2/2024 core values.

## 11. Giới hạn thao tác

- Không sửa code, schema, pipeline, dashboard hoặc logic tự động trong công việc nhập liệu BCTC nếu chưa có yêu cầu riêng. Công cụ kết xuất ảnh PDF tại mục 12 chỉ được duy trì/sử dụng cho kiểm toán trực quan; không tự thay đổi snapshot hoặc luồng đồng bộ dữ liệu.
- Không thêm nguồn thứ ba, không dùng tìm kiếm web ngoài hai nguồn đã được người dùng duyệt.
- Không tự tạo dữ liệu, không suy diễn số thiếu, không thay đổi quy trình chỉ để làm cho một kỳ được PASS.
- Mọi cập nhật data/checkpoint phải có commit và lưu SHA commit; xác minh lại nội dung sau khi ghi.


### 10.18A Note 41 visual amendment — IDC Q2/2026 cash basis

- Note 41 PDF page 66 (printed page 61), rendered 180 DPI, shows cash equivalents 31/12/2025 previously stated **474.491.428.405 VND** + adjustment **890.796.892 VND** = As-restated **475.382.225.297 VND**; cash **78.561.249.834 VND** remains unchanged. This exactly explains the opening cash difference between original Q4/2025 and H1/2026 restated comparative.
- The Q2 standalone cash bridge still has residual **-890.796.892 VND (0,1463%)**, above 0,01%, because the Q1/2026 values available in the repository are as-published, not restated on the same basis. Mark it as a documented cross-period restatement exception. Do not modify Q1 data, CFO/CFI/CFF, net cash movement, or insert a balancing plug. Only close when the same-basis comparative is directly documented.
- Note 41 evidence: run **41697391168**, artifact **13262111894**, PDF page 66, image SHA-256 `72a16c5383e506eafd84a10e41c2e9f604fac5b261869f5832371e80b8276d4e`; report `reports/analysis/IDC-Q2-2026-visual-review.md`.
