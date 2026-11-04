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
