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

### 9.4. Không đồng nhất biến động vốn NCI B04/Note 26 với NCI PAT B02

B04 và Note 26 là bảng biến động vốn chủ sở hữu/lợi ích NCI; B02 là báo cáo kết quả hoạt động, trong đó NCI PAT là phần lợi nhuận sau thuế phân bổ cho NCI. Đây là hai lớp chỉ tiêu khác nhau; không được mặc định biến động số dư NCI phải bằng NCI PAT nếu còn có vốn góp và các thay đổi lợi nhuận đã thực hiện/chưa thực hiện trong vốn chủ sở hữu.

Các con số năm 2025 để tham chiếu:
- B02 FY2025 NCI PAT: **-958.326.405 VND**.
- Note 26 kiểm toán FY2025 trình bày hai thành phần biến động NCI: lỗ đã thực hiện **-1.396.298.463 VND** và lỗ chưa thực hiện **-547.773.687 VND**.
- Tổng hai dòng Note 26 là **-1.944.072.150 VND**, khác B02 NCI PAT **985.745.745 VND**. Chênh lệch này cũng xuất hiện khi so B04 NCI movement H1 với B02 H1 NCI PAT.
- Không có cơ sở để coi phép trừ này tự thân là lỗi dữ liệu hoặc yêu cầu nó phải bằng 0. Note 26/B04 có bảng biến động vốn NCI riêng; B02 ghi nhận NCI PAT riêng. Giữ chênh lệch trong ghi chú phân loại, không thêm plug, không tạo cờ lỗi số liệu chỉ vì hai chỉ tiêu khác nhau.

Do đó:
- **Câu hỏi nguồn gốc khoản vốn 21 tỷ ở NCI:** đã xác nhận riêng (Note 26: tăng phần vốn sở hữu ở công ty con; Q3 B04 định vị phát sinh Q3, residual 1 VND).
- **Câu hỏi phân bổ lợi nhuận B02 Q1/H1:** vẫn PENDING **1.117.693.283 VND**.
- Không coi **985.745.745 VND** là một lỗi hoặc ngoại lệ độc lập nếu chưa có quy tắc/khoản mục nguồn nào yêu cầu B04/Note 26 NCI equity change phải bằng B02 NCI PAT.

Không dùng report Q1/Q2 comparative năm sau để sửa dữ liệu gốc; chúng chỉ chứng minh VDS tiếp tục mang hai cơ sở báo cáo khác nhau vào cột so sánh.


## 10. Đối chiếu công văn giải trình Q1/Q2/2025 và kết luận giới hạn hồ sơ A

- Công bố chính thức Q1/2025 của VDS nêu hai tài liệu đi kèm là BCTC hợp nhất Q1/2025 và công văn giải trình biến động LNST Q1/2025 **so với Q1/2024**. Công văn số **387/2025/CV-TCKT** ngày **29/04/2025** giải trình các chỉ tiêu lợi nhuận trước thuế, chi phí thuế và LNST tổng hợp; phần nội dung công bố không phải bảng cầu nối thay đổi phân bổ parent/NCI. Nguồn công bố: VDSC disclosure page Q1/2025; PDF công văn được lập chỉ cho biến động LNST so với cùng kỳ.
- Công bố chính thức Q2/2025 của VDS nêu BCTC hợp nhất Q2/2025 và công văn giải trình LNST Q2/2025 **so với Q2/2024**. Nội dung công bố được rà thấy không mô tả điều chỉnh lại phân bổ parent/NCI của Q1 hoặc cầu nối Q1 original sang H1 YTD.
- Q1/2026 B02 comparative giữ nguyên phân bổ Q1/2025 original; Q2/2026 B02 comparative giữ nguyên phân bổ H1/2025 YTD. Q3/2025 YTD less Q3 standalone tiếp tục đúng H1/YTD basis. Các tài liệu kỳ sau do đó không cho thấy một bản Q1 restated được đưa vào cột so sánh.
- Kết luận A: **PENDING — source-level allocation inconsistency remains unexplained**. Chênh lệch **1.117.693.283 VND** chỉ là khác biệt phân bổ giữa Q1 original và Q1 implied from H1 less Q2; PAT hợp nhất vẫn khớp tuyệt đối. Không chọn một cơ sở thay thế, không ghi phép trừ là số Q1 đã công bố và không sửa `data/financials-VDS.json`.
- Để đóng A cần tài liệu điều chỉnh/đính chính Q1, công văn giải thích phân bổ NCI, hoặc bảng tính hợp nhất có thể hiện phân bổ parent/NCI cho Q1 và H1 trên cùng basis. Chỉ giải trình tăng/giảm tổng LNST so với cùng kỳ không đủ.


## 11. Đối chiếu nghị quyết phân phối lợi nhuận FY2025 — xác định khoản điều chỉnh NCI 1.944 tỷ

- Nghị quyết ĐHĐCĐ thường niên năm tài chính 2025, số **01/2026/BB-ĐHĐCĐ**, ngày **16/04/2026**, được công bố ngày **17/04/2026**, thông qua BCTC riêng và hợp nhất FY2025 đã được EY kiểm toán, đồng thời thông qua phương án phân phối lợi nhuận FY2025.
- Tại bảng “Phân phối lợi nhuận năm 2025”, phần các khoản mục đã thực hiện/điều chỉnh trong năm, có dòng riêng **“Điều chỉnh Lợi ích cổ đông không kiểm soát” = -1.944.072.150 VND**.
- Số này khớp tuyệt đối với tổng hai thành phần của Note 26 BCTC hợp nhất kiểm toán FY2025:
  - Lỗ đã thực hiện: **-1.396.298.463 VND**.
  - Lỗ chưa thực hiện: **-547.773.687 VND**.
  - Tổng: **-1.944.072.150 VND**.
- Đây là bằng chứng bổ sung rằng khoản -1.944 tỷ là **điều chỉnh lợi ích NCI trong cầu nối lợi nhuận chưa phân phối hợp nhất**, được trình bày riêng trong phương án phân phối lợi nhuận và được ĐHĐCĐ thông qua. Không được đem khoản này so trực tiếp rồi yêu cầu nó bằng B02 NCI PAT; hai dòng nằm ở hai lớp báo cáo khác nhau.
- Nghị quyết này **không giải thích** chênh lệch phân bổ B02 Q1/H1 **1.117.693.283 VND**. Hồ sơ A vẫn PENDING.
- Nguồn gốc vốn NCI 21 tỷ và thời điểm Q3/2025 vẫn là hồ sơ riêng đã đóng PASS; không gộp khoản điều chỉnh NCI -1.944 tỷ này vào vốn góp 21 tỷ.
- Nguồn chính thức: tệp nghị quyết/biên bản ĐHĐCĐ được lưu tại Vietstock `https://static2.vietstock.vn/vietstock/2026/4/17/20260417___vds___bbh_va_nqdhdcd_thuong_nien_fy_2025.pdf`; các dòng đối chiếu trong trích xuất văn bản gồm nội dung phê duyệt phân phối lợi nhuận FY2025 và dòng Adjustment of Non-controlling Interests.


## 12. So sánh trực tiếp thuyết minh B05 về công ty con/quỹ thành viên tại Q1 và Q2/2025

- Đã render và đọc trực tiếp ảnh PDF gốc ở 300 DPI:
  - Q1/2025 HN, PDF page **21**, printed page **16**, source `reports/raw/VDS/auto-vds-20261021/a2d499f8fc79f469.pdf`.
  - Q2/2025 HN, PDF page **22**, printed page **16**, source `reports/raw/VDS/auto-vds-20261021/69d4862950596830.pdf`.
  - Workflow run **41879521045**, artifact **13349410378**, `vds-q1-q2-2025-ownership-note-review`.
- Tại 31/03/2025 và 30/06/2025, cả hai báo cáo cùng liệt kê:
  - Công ty con CTCP Quản lý Quỹ Rồng Việt (VDAM): vốn điều lệ **100.000.000.000 VND**, tỷ lệ sở hữu VDS **58%**.
  - Quỹ thành viên Quỹ Đầu tư Rồng Việt (RVIF): vốn quỹ **70.000.000.000 VND**, tỷ lệ sở hữu VDS **85%**.
- Không thấy thay đổi được công bố về tên đơn vị, vốn ghi trong bảng, hay tỷ lệ sở hữu giữa ngày 31/03 và 30/06/2025. Điều này làm yếu giả thuyết rằng chênh lệch phân bổ B02 Q1/H1 phát sinh đơn thuần do thay đổi tỷ lệ sở hữu/đơn vị hợp nhất trong Q2.
- Giới hạn: so sánh hai ngày báo cáo không loại trừ giao dịch nội kỳ, giao dịch vốn chưa làm thay đổi tỷ lệ sở hữu, hoặc biến động giữa các thành viên/quỹ không được phản ánh ở dòng vốn/tỷ lệ cuối kỳ trong bảng này. Không dùng kết quả này để đóng A.
- Hồ sơ A vẫn **PENDING 1.117.693.283 VND**. Cần tiếp tục kiểm tra B05 Q3/Q4/2025 và thuyết minh biến động sở hữu; tuy nhiên, chỉ tài liệu thể hiện cầu nối phân bổ parent/NCI Q1 sang H1 mới đủ đóng ngoại lệ B02.


## 13. Lệnh kiểm tra bổ sung — Q3/Q4 B05 ownership notes

Đang kiểm tra trực tiếp B05 của hai báo cáo hợp nhất Q3/2025 và Q4/2025 để xem thuyết minh công ty con/quỹ thành viên có ghi nhận thay đổi vốn, tỷ lệ sở hữu, hoặc thông tin nhận vốn trong giai đoạn phát sinh khoản tăng NCI 21 tỷ ở Q3 hay không. Chỉ kết luận theo trang PDF gốc sau khi ảnh kết xuất được kiểm tra; chưa ghi nhận kết quả Q3/Q4 tại thời điểm tạo mục này.


## 14. Xác định đúng đơn vị tăng vốn 21 tỷ — VDAM tăng vốn điều lệ 100 → 150 tỷ

### 14.1. So sánh B05 tại bốn thời điểm báo cáo

Các trang B05-CTCK/HN đã được render và đọc trực tiếp ở **300 DPI** từ PDF gốc:

| Kỳ báo cáo | VDAM — vốn điều lệ | Tỷ lệ VDS sở hữu | RVIF — vốn quỹ | Tỷ lệ VDS sở hữu |
|---|---:|---:|---:|---:|
| Q1/2025 (31/03) | 100 tỷ | 58% | 70 tỷ | 85% |
| Q2/2025 (30/06) | 100 tỷ | 58% | 70 tỷ | 85% |
| Q3/2025 (30/09) | **150 tỷ** | 58% | 70 tỷ | 85% |
| Q4/2025 (31/12) | **150 tỷ** | 58% | 70 tỷ | 85% |

Nguồn/trang:
- Q1 PDF page 21 / printed page 16.
- Q2 PDF page 22 / printed page 16.
- Q3 PDF page 21 / printed page 16.
- Q4 PDF page 21 / printed page 16.

Q3 và Q4 B05 đều ghi VDAM chỉ có một công ty con, vốn điều lệ **150.000.000.000 VND**, tỷ lệ sở hữu VDS **58%**; RVIF tiếp tục có vốn quỹ **70.000.000.000 VND**, tỷ lệ sở hữu VDS **85%**. Mục thông tin đăng ký VDAM ghi giấy phép thay đổi gần nhất ngày **29/09/2025**; không suy diễn rằng riêng ngày này chắc chắn là ngày hoàn tất nộp tiền nếu không có nghị quyết/giấy chứng nhận chi tiết.

### 14.2. Cầu nối 21 tỷ được xác định qua vốn VDAM và phần sở hữu NCI

- Vốn điều lệ VDAM tăng từ **100 tỷ** tại 30/06/2025 lên **150 tỷ** tại 30/09/2025: tăng **50.000.000.000 VND**.
- VDS giữ tỷ lệ sở hữu **58%**, do đó phần lợi ích không kiểm soát tại VDAM là **42%**.
- Phần vốn tương ứng NCI: **50.000.000.000 × 42% = 21.000.000.000 VND**.
- Con số này khớp chính xác Note 26 BCTC hợp nhất kiểm toán FY2025, dòng “Tăng phần vốn sở hữu ở công ty con” **21.000.000.000 VND**.
- Kiểm tra B04 Q2→Q3 và B02 Q3 độc lập:
  - Q2 B04 closing NCI: **47.250.464.312 VND**.
  - Q3 B04 closing NCI: **71.274.122.857 VND**.
  - Mức tăng số dư NCI trong Q3: **24.023.658.545 VND**.
  - Trừ Q3 standalone B02 NCI PAT **3.023.658.546 VND**, phần tăng vốn hàm ý **20.999.999.999 VND**, residual **-1 VND** so với 21 tỷ (giữ nguyên, không điều chỉnh).
- Vì vậy, hồ sơ B được xác nhận ở mức cụ thể: **VDAM tăng vốn điều lệ 50 tỷ trong Q3/2025; phần 42% thuộc NCI tương ứng 21 tỷ**. Không phải tăng vốn điều lệ riêng của VDS mẹ, và không phải RVIF tăng vốn.

### 14.3. Giới hạn về danh tính người góp vốn và hồ sơ pháp lý

B05 và Note 26 xác nhận thay đổi vốn và tỷ lệ sở hữu, nhưng các trang đã kiểm tra không liệt kê tên cá nhân/tổ chức góp vốn, số cổ phần phát hành, số tiền thực nộp từng cổ đông hoặc nghị quyết tăng vốn chi tiết. Vì vậy, có thể xác định **phần vốn NCI tương ứng 21 tỷ** từ tỷ lệ 42%, nhưng chưa thể nêu tên từng nhà đầu tư bên ngoài hoặc ngày thanh toán chính xác.

### 14.4. Kết luận và tách khỏi hồ sơ A

- **B — tăng vốn NCI 21 tỷ: PASS/CLOSED.** Đơn vị nhận vốn xác định là VDAM; vốn điều lệ từ 100 lên 150 tỷ trong Q3/2025; tỷ lệ VDS 58%, NCI 42%; 42% của 50 tỷ bằng chính xác 21 tỷ.
- **A — phân bổ B02 Q1/H1: PENDING.** Chênh lệch **1.117.693.283 VND** vẫn không được giải thích bởi giao dịch vốn VDAM, vì VDAM tăng vốn sau thời điểm H1; Q1 và Q2 B05 đều trình bày vốn 100 tỷ/58%.
- Giữ nguyên các số B02 gốc Q1, Q2 current-quarter và H1 YTD; không backsolve, không thêm plug, không sửa `data/financials-VDS.json`.

Bằng chứng render: Q3/Q4 workflow runs **41881072688** và **41881158938**; artifacts **13348677962** và **13348792588**; PDF SHA-256 lần lượt `bd7db8914d33e4144845c01aca837597b2986183d20a690f6fbcbbc855c5e6d5` và `d2252c9c1aaafbaffa8395c96fffd5b2063aa8b3da881047ee3e74270691e9e2`, pages 20–23 rendered at 300 DPI.
