# VDS Q2/2025 HN — bổ sung xác minh phân bổ lợi nhuận parent/NCI

- Trạng thái: **PENDING — chưa tìm được cầu nối giải thích thay đổi phân bổ Q1 sang H1**.
- Mã tài liệu VietstockFinance: **513947**.
- Danh mục nguồn: https://finance.vietstock.vn/VDS/tai-tai-lieu.htm?doctype=1
- PDF gốc: https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%202/VDS_Baocaotaichinh_Q2_2025_Hopnhat.pdf
- Tệp người dùng cung cấp: `VDS_Baocaotaichinh_Q2_2025_Hopnhat.pdf`; SHA-256 `69d48629505968301d1ed8b3635b68183c585d643bc71c500cc230922459095d`.
- Tệp có 50 trang, ký số ngày **30/07/2025**; phạm vi **hợp nhất HN**, đơn vị trình bày trên B01–B04 là VND.
- Các trang được mở trực tiếp từ PDF gốc và đối chiếu với bản người dùng cung cấp: B02 PDF pages **12–14** (printed pages 6–8); B04 PDF pages **19–20** (printed pages 13–14); B05 notes PDF pages **21–50** (printed pages 15–44).

## 1. B02 — các số HN được xác nhận trực quan

Q2/2025, current-quarter column:
- PAT total: **-11,193,905,667 VND**.
- PAT attributable to owners of parent (row 201): **-9,900,252,664 VND**.
- PAT attributable to NCI (row 203): **-1,293,653,003 VND**.
- Parent + NCI = total PAT exactly.

H1/2025, YTD column:
- PAT total: **7,818,436,589 VND**.
- Parent PAT: **8,071,151,977 VND**.
- NCI PAT: **-252,715,388 VND**.
- Parent + NCI = total PAT exactly.

Các số này khớp số HN đã lưu; không có căn cứ sửa snapshot dữ liệu.

## 2. Đối chiếu ngược Q1 — ngoại lệ phân bổ còn nguyên

Q1/2025 B02 gốc đã ghi nhận:
- Parent PAT: **19,089,097,924 VND**.
- NCI PAT: **-76,755,668 VND**.
- Total PAT: **19,012,342,256 VND**.

Q1 hàm ý từ H1 YTD trừ Q2 current-quarter:
- Parent: **17,971,404,641 VND**.
- NCI: **1,040,937,615 VND**.
- Total PAT: **19,012,342,256 VND**.

Tổng PAT khớp tuyệt đối; riêng phân bổ thay đổi **1,117,693,283 VND** từ parent sang NCI so với Q1 đã công bố. Không thay Q1 gốc bằng phép trừ lũy kế; không ghi nhận phép trừ này là số quý I đã công bố. Q3/2025 YTD trừ Q3 standalone tiếp tục khớp đúng số H1 đã công bố, nhưng không làm rõ nguyên nhân chênh lệch giữa Q1 gốc và Q1 hàm ý.

## 3. B04 — phát hiện thêm biến động số dư NCI, nhưng chưa có giải trình

B04, printed page 13 (PDF page 19), row 9 “Lợi ích cổ đông không kiểm soát”:
- Số dư đầu năm: **48,488,925,445 VND**.
- Giảm trong kỳ: **1,238,461,133 VND**.
- Số dư cuối kỳ: **47,250,464,312 VND**.

So với lỗ sau thuế lũy kế phân bổ cho NCI trên B02 là **252,715,388 VND**, biến động giảm số dư NCI lớn hơn **985,745,745 VND**. B04 chỉ thể hiện tổng tăng/giảm số dư, không nêu bản chất giao dịch hoặc cầu nối chi tiết cho khoản chênh lệch này. Đây là **một câu hỏi đối chiếu vốn chủ sở hữu riêng**, không được mặc định là nguyên nhân của chênh lệch phân bổ lợi nhuận 1,117,693,283 VND.

## 4. Thuyết minh đã kiểm tra và giới hạn bằng chứng

- B05 printed page 16 (PDF page 22) nêu công ty con CTCP Quản lý Quỹ Rồng Việt (VDAM), tỷ lệ sở hữu **58%**, và Quỹ Đầu tư Rồng Việt (RVIF), tỷ lệ sở hữu **85%**.
- B05 printed page 17 (PDF page 23) nêu nguyên tắc trình bày lợi ích cổ đông không kiểm soát trong kết quả hoạt động hợp nhất và vốn chủ sở hữu hợp nhất.
- B05 printed page 44 (PDF page 50) tính EPS theo lợi nhuận sau thuế phân bổ cho cổ đông sở hữu cổ phiếu phổ thông, số này khớp B02: Q2 **-9,900,252,664 VND**, H1 **8,071,151,977 VND**. Không có bảng phân rã bổ sung giải thích sự chuyển phân bổ giữa parent và NCI.
- Trang sự kiện sau ngày kết thúc kỳ ghi việc phát hành thêm 24,3 triệu cổ phiếu ngày 08/07/2025, tăng vốn góp chủ sở hữu **243 tỷ VND**. Sự kiện sau ngày 30/06 này không phải bằng chứng giải thích phân bổ lợi nhuận B02 hoặc biến động NCI trong sáu tháng đầu năm.

## 5. Kết luận và hành động tiếp theo

1. Giữ nguyên dữ liệu B02 Q1/2025 gốc, Q2/2025 current-quarter và H1/2025 YTD.
2. Giữ ngoại lệ phân bổ **1,117,693,283 VND** ở trạng thái PENDING; không backsolve, không chuyển số giữa parent/NCI và không thêm balancing plug.
3. Mở một kiểm tra riêng cho biến động vốn NCI **1,238,461,133 VND** tại B04; chưa quy kết phần chênh lệch **985,745,745 VND** cho lợi nhuận, cổ tức, giao dịch vốn hoặc thay đổi tỷ lệ sở hữu khi tài liệu chưa chỉ rõ.
4. Để đóng ngoại lệ cần tài liệu VietstockFinance chính thức thể hiện báo cáo Q1 điều chỉnh/restated, giải trình phân bổ lợi nhuận, bảng cầu nối lợi ích NCI hoặc giao dịch vốn/cổ tức của công ty con/quỹ thành viên đủ để đối chiếu. Nếu không có, giữ PENDING có mô tả.
5. Không sửa `data/financials-VDS.json`; không sử dụng báo cáo riêng RI năm 2025 làm bằng chứng thay thế cho HN Q2/2025.

## 6. Quy tắc quy trình được rút ra

Đối với báo cáo hợp nhất, phải kiểm tra độc lập hai cầu nối:
- **B02:** parent PAT + NCI PAT = consolidated PAT; đối chiếu Q1 gốc với H1 YTD trừ Q2 current-quarter.
- **B04:** số dư đầu kỳ NCI + các biến động vốn trong kỳ = số dư cuối kỳ; không giả định biến động B04 chính là NCI PAT, cũng không dùng B04 tổng hợp để tự giải thích phân bổ B02.

Một cầu nối đạt PASS không thay thế cầu nối còn lại. Nếu một trong hai thiếu thuyết minh giao dịch chi tiết, giữ ngoại lệ PENDING.


## 7. Bổ sung sau khi kiểm tra BCTC hợp nhất kiểm toán FY2025

Phần kết luận cũ tại mục 3 về việc chưa xác định bản chất biến động B04 được **cập nhật** bằng bằng chứng năm kiểm toán:
- Note 26 BCTC hợp nhất kiểm toán FY2025 (PDF page 60 / printed page 55) xác nhận “Tăng phần vốn sở hữu ở công ty con” **21.000.000.000 VND**.
- Cầu nối NCI từ đầu đến cuối năm đã PASS: 48.488.925.445 + 21.000.000.000 - 1.396.298.463 - 547.773.687 = 67.544.853.295 VND.
- B04 FY2025 ghi tăng ròng NCI **19.055.927.850 VND**, đúng bằng 21 tỷ trừ hai khoản lỗ trong Note 26.
- Vì vậy, câu hỏi “khoản tăng 21 tỷ là gì?” đã có lời giải ở cấp độ thuyết minh: tăng phần vốn/quyền lợi NCI tại đơn vị con được hợp nhất, phù hợp với nghiệp vụ tăng vốn/góp vốn từ phía sở hữu không kiểm soát. Note 26 không nêu pháp nhân cụ thể, nhà đầu tư hoặc hồ sơ pháp lý; không gán chắc cho VDAM hay RVIF.
- B04 H1 vẫn là số dư 47.250.464.312 VND; sự tăng vốn 21 tỷ không nằm trong B04 đến 30/06/2025. Không xác định chính xác quý phát sinh nếu thiếu B04 kỳ sau.
- Ngoại lệ B02 parent/NCI **1.117.693.283 VND** chưa được giải thích và tiếp tục PENDING. Không dùng khoản tăng vốn 21 tỷ để đóng hồ sơ A.
- Hồ sơ kiểm toán chi tiết: `reports/analysis/VDS-FY2025-audited-NCI-21bn-reconciliation.md`, commit `fc831882e689fa6b41e3d93f844a21d9f9182312`.

Không sửa `data/financials-VDS.json`; Q2/2025 vẫn chưa hoàn thành do ngoại lệ B02 còn mở.


## 8. Kết quả rà soát B04 Q3/2025 sau khi có BCTC hợp nhất kiểm toán FY2025

- Ảnh B04 Q3/2025 PDF page 18 / printed page 13 được kiểm tra trực tiếp; row 9 NCI: đầu năm 48.488.925.445 VND, tăng lũy kế 22.785.197.412 VND, cuối 30/09/2025 là 71.274.122.857 VND.
- Đối chiếu Q2 B04 cuối 30/06 là 47.250.464.312 VND, Q3 B02 NCI PAT riêng quý là 3.023.658.546 VND: phần tăng ngoài PAT trong Q3 = 71.274.122.857 - 47.250.464.312 - 3.023.658.546 = **20.999.999.999 VND**, residual -1 VND so với Note 26 FY2025 “Tăng phần vốn sở hữu ở công ty con” 21.000.000.000 VND.
- Do đó hồ sơ B đã **PASS** ở cấp độ phân loại và định vị thời điểm: khoản tăng 21 tỷ là vốn/quyền lợi NCI tại công ty con, phát sinh trong Q3/2025 theo đối chiếu B04 Q2→Q3 và B02 Q3; cầu nối năm kiểm toán khớp tuyệt đối. Không có tên công ty con/nhà đầu tư trong Note 26 nên không gán cụ thể.
- Khoản -1 VND trên đối chiếu Q3 là residual số học được giữ lại, không sửa số nguồn. Nó nằm trong ngưỡng 0,01%.
- Hồ sơ A tiếp tục **PENDING**: Q1 parent/NCI gốc khác Q1 hàm ý từ H1 trừ Q2 **1.117.693.283 VND**. Không dùng nghiệp vụ vốn 21 tỷ Q3 làm lời giải cho phân bổ lợi nhuận Q1/H1.


## 9. Kiểm tra hồi cứu cột so sánh Q1/2026 và H1/2026 — chưa có bản sửa phân bổ Q1/H1

### 9.1. Q1/2026 so sánh Q1/2025

- BCTC hợp nhất Q1/2026 VietstockFinance document **543855**, B02 PDF page **13** / printed page **8**, đã được kiểm tra trực quan trong đợt audit Q1/2026.
- Cột so sánh Q1/2025 vẫn giữ: PAT hợp nhất **19.012.342.256 VND**; phân bổ cho chủ sở hữu **19.089.097.924 VND**; NCI **-76.755.668 VND**. Đây trùng hoàn toàn Q1/2025 original B02 và Q1/2025 B04.
- Không thấy Q1/2025 được trình bày lại trong cột so sánh quý I năm sau.

### 9.2. Q2/2026 so sánh H1/2025

- BCTC hợp nhất Q2/2026 VietstockFinance document **555653**, PDF page **13** / printed page **8**, B02, được render và trực tiếp kiểm tra ảnh gốc ở **300 DPI**; workflow run **41878236428**, artifact **13347787384**, member `VDS_Baocaotaichinh_Q2_2026_Hopnhat.pdf` trong archive `reports/raw/VDS/auto-vds-20261021/6ca61e80d55ffaac.zip`.
- Cột H1/2025 so sánh vẫn giữ: PAT hợp nhất **7.818.436.589 VND**; parent **8.071.151.977 VND**; NCI **-252.715.388 VND**. Giá trị đúng như Q2/2025 original H1/YTD.
- Như vậy H1 basis cũng được mang sang kỳ so sánh năm sau, không thấy Q2/2025 H1 được trình bày lại.

### 9.3. Kết luận kiểm định A

Các báo cáo kỳ sau đang duy trì đồng thời:
- Q1/2025 original (Q1/2026 comparative): parent **19.089.097.924**, NCI **-76.755.668**.
- H1/2025 original (Q2/2026 comparative): parent **8.071.151.977**, NCI **-252.715.388**.

Q3/2025 YTD less Q3/2025 standalone cũng khớp chính xác H1/2025 nêu trên. Vì vậy, sai khác không phải lỗi đọc nhầm trang/OCR trong lần kiểm tra hiện tại; đây là **inconsistency đã tồn tại trong các cột phân bổ lợi nhuận được công bố**, và các báo cáo so sánh Q1/2026, Q2/2026 không cho thấy VDS đã phát hành số Q1 điều chỉnh để giải quyết nó.

Số Q1 suy ra từ H1 less Q2 vẫn chỉ là phép đối chiếu:
- Parent **17.971.404.641 VND**.
- NCI **1.040.937.615 VND**.
- Total PAT **19.012.342.256 VND**.

Chênh lệch phân bổ so với Q1 original vẫn **1.117.693.283 VND**. Không thay thế Q1 original bằng số suy ra; không thêm balancing plug; không sửa `data/financials-VDS.json`. Hồ sơ A tiếp tục **PENDING — source-level allocation inconsistency not explained**.

### 9.4. Tách riêng residual B04/NCI equity so với B02 NCI PAT

Không được đồng nhất dòng biến động vốn NCI ở B04/Note 26 với riêng chỉ tiêu NCI PAT trên B02. Năm 2025:
- B02 FY2025 NCI PAT: **-958.326.405 VND**.
- Note 26 kiểm toán FY2025 có hai dòng lỗ thực hiện và chưa thực hiện: **-1.396.298.463** và **-547.773.687 VND**, tổng **-1.944.072.150 VND**.
- Chênh lệch giữa tổng hai dòng Note 26 và B02 NCI PAT là **985.745.745 VND**; cùng độ lớn với residual giữa H1 B04 NCI movement và H1 B02 NCI PAT. Báo cáo hiện kiểm tra chưa cung cấp cầu nối chi tiết đủ để khẳng định bản chất phân loại của residual này.

Do đó:
- **Câu hỏi nguồn gốc khoản vốn 21 tỷ ở NCI:** đã xác nhận riêng (Note 26: tăng phần vốn sở hữu ở công ty con; Q3 B04 định vị phát sinh Q3, residual 1 VND).
- **Câu hỏi phân bổ lợi nhuận B02 Q1/H1:** vẫn PENDING 1.117.693.283 VND.
- **Câu hỏi cầu nối B04/Note 26 NCI equity với B02 NCI PAT:** lưu riêng PENDING 985.745.745 VND; không gộp với 1.117.693.283 VND.

Không dùng report Q1/Q2 comparative năm sau để sửa dữ liệu gốc; chúng chỉ chứng minh VDS tiếp tục mang hai cơ sở báo cáo khác nhau vào cột so sánh.
