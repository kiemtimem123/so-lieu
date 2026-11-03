# SOP xử lý báo cáo tài chính doanh nghiệp niêm yết

- Phiên bản: 1.2
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

## 10. Áp dụng cho trạng thái VDS hiện tại

Mã đang hoạt động: **VDS**. Q1–Q4/2024 và Q1/2025 đã COMPLETE, có checkpoint và visual review. Q2/2025 đã đối chiếu trực quan B01/B02/B03 và nhập đủ các số quý; hiện **PENDING duy nhất ở cầu nối phân bổ LNST cổ đông mẹ/NCI giữa số quý và lũy kế H1**. Không chuyển sang Q3/2025 trước khi xử lý ngoại lệ này.

### 10.1 Các kỳ đã đóng
- Q1–Q3/2024: đã có checkpoint trước; không chạy lại trích xuất lõi hoặc visual review.
- Q4/2024: B01/B02/B03 đã xem trực tiếp PDF gốc VietstockFinance, document ID 489660; dữ liệu/checkpoint đã lưu. Dòng 29 B02: 25.000.000 VND thuộc cột FY2024 YTD, không thuộc quý 4 riêng lẻ.
- Q1/2025: PDF hợp nhất VietstockFinance document ID 504544; B01 PDF trang 7–9 (trang in 1–3), B02 PDF trang 12–14 (trang in 6–8), B03 PDF trang 15–17 (trang in 9–11). Tất cả tổng B01/B02/B03 khớp. Data commit `1ed4ef951122aa1b2060d0b795462c2be9521345`. Không lặp lại trích xuất lõi/visual review.

### 10.2 Kết quả xác minh Q2/2025
- Nguồn: VietstockFinance document ID **513947**, báo cáo hợp nhất, đơn vị VND; PDF gốc lưu tại `reports/raw/VDS/auto-vds-20261021/69d4862950596830.pdf` (50 trang). Đã xem trực tiếp B01 trang in 1–3 (PDF trang 7–9), B02 trang in 6–8 (PDF trang 12–14), B03 trang in 9–11 (PDF trang 15–17).
- B01: tổng tài sản **6.856.334.146.952 VND** = tổng nợ **4.022.130.711.905 VND** + vốn chủ **2.834.203.435.047 VND**; tài sản ngắn hạn **5.746.624.022.451 VND** + tài sản dài hạn **1.109.710.124.501 VND** = tổng tài sản. Tổng nợ ngắn hạn **4.001.526.230.572 VND**, nợ dài hạn **20.604.481.333 VND**.
- B02 quý riêng: doanh thu hoạt động **180.998.605.171 VND**; chi phí hoạt động **160.666.996.283 VND**; cấu phần doanh thu và chi phí đều cộng chính xác. PBT **-17.442.687.286 VND**; chi phí thuế TNDN **-6.248.781.619 VND** (thuế hoãn lại âm); PAT **-11.193.905.667 VND**; phân bổ Q2: cổ đông mẹ **-9.900.252.664 VND**, NCI **-1.293.653.003 VND**; EPS **-41**.
- Dòng 29 B02 (chi phí nghiệp vụ tư vấn đầu tư chứng khoán): cột Q2 hiện tại và cột H1 hiện tại để trống. **20.000.000 VND chỉ ở cột H1 năm trước**, không gán vào Q2/2025.
- B03 H1 YTD gốc: CFO **423.813.880.703 VND**; CFI **-766.006.221.613 VND**; CFF **424.400.000.000 VND**; biến động tiền thuần **82.207.659.090 VND**; tiền đầu kỳ **1.207.137.419.234 VND**; tiền cuối kỳ **1.289.345.078.324 VND**. Số quý 2 riêng được tính bằng H1 YTD trừ Q1 YTD từ báo cáo Q1 gốc: CFO **977.015.279.251 VND**, CFI **-844.021.190.816 VND**, CFF **492.600.000.000 VND**, biến động tiền **625.594.088.435 VND**, tiền đầu quý **663.750.989.889 VND**, tiền cuối quý **1.289.345.078.324 VND**. Flow sum và cash bridge residual đều bằng 0. B03 row 76 blank → cổ tức đã trả giữ `null`; row 65 là cổ tức/lợi nhuận nhận từ đầu tư dài hạn, không phải cổ tức trả.
- ROA **-0,68%**, ROE **-1,58%** theo công thức lợi nhuận sau thuế quý / bình quân tài sản hoặc vốn chủ đầu-cuối kỳ × 4 × 100.

### 10.3 Ngoại lệ PENDING: phân bổ LNST cổ đông mẹ/NCI
- Q1/2025 B02 gốc (document ID 504544) ghi Q1 PAT **19.012.342.256 VND**, parent **19.089.097.924 VND**, NCI **-76.755.668 VND**.
- Q2/2025 B02 gốc (document ID 513947) ghi Q2 riêng PAT **-11.193.905.667 VND**, parent **-9.900.252.664 VND**, NCI **-1.293.653.003 VND**.
- Cột H1 YTD trên chính báo cáo Q2 ghi PAT **7.818.436.589 VND**, parent **8.071.151.977 VND**, NCI **-252.715.388 VND**. PAT H1 = Q1 PAT + Q2 PAT chính xác, nhưng parent/NCI không cộng theo hai cột quý gốc.
- H1 YTD trừ Q2 riêng hàm ý Q1 allocation parent **17.971.404.641 VND**, NCI **1.040.937.615 VND**; so với Q1 PDF gốc, chênh lệch phân bổ đúng **1.117.693.283 VND** từ parent sang NCI, không làm đổi PAT. Báo cáo đã xem không nêu giải thích điều chỉnh này.
- Không sửa số Q1 đã xác minh; không lấy số suy ra làm số Q1 chuẩn; không đưa plug. Giữ cả ba nhóm số gốc, lưu delta và đặt `PENDING_UNEXPLAINED_CROSS_PERIOD_REALLOCATION`.
- Đã thử nguồn phụ WiData `https://widata.vn/VDS?tab=documents` theo quyền đã duyệt, nhưng trang trả DisabledError trong lần truy xuất hiện tại; không có giá trị WiData nào được sao chép. Không sử dụng nguồn thứ ba khi chưa có chấp thuận.
- Các tổng B01, B02 quý riêng và B03 đã PASS; chỉ cầu nối phân bổ parent/NCI YTD là PENDING. Không đánh dấu kỳ COMPLETE, không chuyển sang Q3 cho đến khi có giải thích/bằng chứng hợp lệ.

### 10.4 Checkpoint và bước tiếp theo
- Data commit Q1/2025: `1ed4ef951122aa1b2060d0b795462c2be9521345`.
- Data commit Q2/2025 (đã lưu số gốc, raw VND, visual review và ngoại lệ): `f3e867ed828280d95c6fbe163c97eb5be36a4884`.
- Q2/2025 hiện là kỳ đang hoạt động; `doNotRepeatCoreExtraction=true` và `doNotRepeatVisualReview=true`. Chỉ xử lý ngoại lệ phân bổ parent/NCI, không trích xuất lại các bảng đã PASS.
- Chỉ khi ngoại lệ được phân xử bằng nguồn hợp lệ mới đặt Q2 COMPLETE và chuyển VDS Q3/2025. Sau đó tiếp tục Q4/2025, Q1/2026, Q2/2026.

## 11. Giới hạn thao tác

- Không sửa code, schema, pipeline, dashboard hoặc logic tự động trong công việc nhập liệu BCTC nếu chưa có yêu cầu riêng.
- Không thêm nguồn thứ ba, không dùng tìm kiếm web ngoài hai nguồn đã được người dùng duyệt.
- Không tự tạo dữ liệu, không suy diễn số thiếu, không thay đổi quy trình chỉ để làm cho một kỳ được PASS.
- Mọi cập nhật data/checkpoint phải có commit và lưu SHA commit; xác minh lại nội dung sau khi ghi.
