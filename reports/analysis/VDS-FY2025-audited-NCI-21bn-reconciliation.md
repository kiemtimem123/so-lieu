# VDS FY2025 audited HN — xác minh khoản tăng NCI 21 tỷ đồng

- Trạng thái kiểm định: **PASS — đã xác nhận khoản tăng 21.000.000.000 VND trong thuyết minh NCI và đối chiếu được số dư cuối năm**.
- Phạm vi: báo cáo tài chính hợp nhất kiểm toán năm 2025; không sử dụng báo cáo riêng công ty mẹ (RI).
- Kho lưu trữ: `reports/raw/VDS/auto-vds-20261021/a65994df991573d9.zip`.
- Thành viên PDF đã chọn đúng: `VDS_Baocaotaichinh_2025_Kiemtoan_Hopnhat.pdf` (không phải `ISC_Baocaotaichinh_2025_Kiemtoan_Hopnhat.pdf`).
- PDF SHA-256: `9c4c4b64f9df79340c943283ffd4f448b20a26ffb4cfb06ef736793205d44c9c`; 83 trang.
- Kết xuất ảnh gốc để kiểm tra: workflow run **41854400509**, artifact **13336881442**, render 150 DPI; không thay thế hoặc sửa PDF nguồn.

## 1. Bằng chứng trực tiếp trong thuyết minh 26

PDF page **60**, printed page **55**, Note 26 “Lợi ích cổ đông không kiểm soát” ghi các biến động trong năm 2025 (VND):

| Khoản mục | Giá trị |
|---|---:|
| Số đầu năm | 48.488.925.445 |
| **Tăng phần vốn sở hữu ở công ty con** | **21.000.000.000** |
| (Lỗ)/lãi đã thực hiện trong năm | (1.396.298.463) |
| Lỗ chưa thực hiện trong năm | (547.773.687) |
| **Lợi ích cổ đông không kiểm soát cuối năm** | **67.544.853.295** |

Đối chiếu số học:
`48.488.925.445 + 21.000.000.000 - 1.396.298.463 - 547.773.687 = 67.544.853.295`
Residual = **0 VND**.

Vì vậy khoản **21 tỷ đồng** là khoản tăng gộp phần vốn/quyền lợi thuộc cổ đông không kiểm soát ở đơn vị con được hợp nhất. Bản chất phù hợp với việc có thêm phần vốn thuộc nhà đầu tư bên ngoài ở đơn vị con; đây **không phải** tăng vốn điều lệ của riêng công ty mẹ VDS.

## 2. Đối chiếu B04 hợp nhất cuối năm

PDF pages **24–25**, printed pages **19–20**, B04 row 9 “Lợi ích cổ đông không kiểm soát” trình bày:
- Số dư đầu năm 2025: **48.488.925.445 VND**.
- Tăng ròng trong năm 2025: **19.055.927.850 VND**.
- Số dư cuối năm: **67.544.853.295 VND**.

Tăng ròng B04 khớp Note 26:
`21.000.000.000 - 1.396.298.463 - 547.773.687 = 19.055.927.850`
Residual = **0 VND**.

Do đó, **cầu nối B04 toàn năm đã PASS** và khoản tăng gộp 21 tỷ được giải thích bởi thuyết minh kiểm toán.

## 3. Đối chiếu với B04 bán niên Q2/2025

BCTC hợp nhất Q2/2025 VietstockFinance document **513947**, PDF page **19**, printed page **13**, B04 row 9 cho thấy:
- Đầu năm: **48.488.925.445 VND**.
- Đến 30/06/2025: **47.250.464.312 VND**.
- Giảm lũy kế 6 tháng: **1.238.461.133 VND**.
- Không có khoản tăng NCI hiện hành trong cột tăng của kỳ bán niên.

Như vậy khoản tăng gộp 21 tỷ **không có trong B04 đến 30/06/2025**; được ghi nhận ở phần còn lại của năm. Tài liệu cuối năm không chỉ rõ ngày phát sinh, nên không gán khoản tăng cho riêng Q3 hay Q4 nếu không có báo cáo kỳ tương ứng chứng minh.

## 4. Phạm vi đơn vị và giới hạn xác định đối tượng góp vốn

- PDF page **28**, printed page **23**, Note 1 liệt kê một công ty con và một quỹ thành viên:
  - CTCP Quản lý Quỹ Rồng Việt (VDAM): tỷ lệ sở hữu trực tiếp 58%, gián tiếp 0%.
  - Quỹ Đầu tư Rồng Việt (RVIF): tỷ lệ sở hữu trực tiếp 85%, gián tiếp 2,9%.
- PDF page **50**, printed page **45**, Note 10 ghi khoản đầu tư dài hạn vào RVIF cuối năm **49.497.795.000 VND**, đầu năm không có số dư.
- PDF page **21**, printed page **16**, B03b row 71 ghi tổng tiền thu từ phát hành cổ phiếu/nhận vốn góp của chủ sở hữu ở cấp Nhóm Công ty là **68.000.000.000 VND** trong năm.

Các thông tin này là bối cảnh đối chiếu, nhưng **Note 26 không chỉ rõ** khoản 21 tỷ thuộc VDAM hay RVIF, không nêu tên cá nhân/tổ chức góp vốn, tỷ lệ vốn trước/sau, số lượng cổ phần/chứng chỉ quỹ phát hành, hay hình thức pháp lý chính xác của giao dịch. Vì vậy:
- Có thể xác nhận khoản tăng thuộc phần vốn/quyền lợi NCI tại đơn vị con.
- Không được gán chắc chắn cho VDAM hoặc RVIF chỉ từ Note 1/Note 10.
- Không được khẳng định toàn bộ 68 tỷ B03 row 71 là khoản 21 tỷ này.
- Muốn kết luận chính xác nhà đầu tư nào, đơn vị nào và hình thức (phát hành thêm/góp vốn/chuyển nhượng phần sở hữu) cần nghị quyết, hồ sơ tăng vốn hoặc thuyết minh chi tiết của chính đơn vị con/quỹ. Chưa có bằng chứng đó trong các trang đã kiểm tra của BCTC kiểm toán hợp nhất.

## 5. Tách riêng với hồ sơ A — sai khác phân bổ lợi nhuận B02 Q1/H1

Việc tìm được khoản tăng vốn **không giải quyết** sai khác parent/NCI trên B02:
- Q1/2025 B02 gốc: parent **19.089.097.924**, NCI **-76.755.668**.
- Q2/2025 B02 H1 YTD: parent **8.071.151.977**, NCI **-252.715.388**.
- Q2 current quarter: parent **-9.900.252.664**, NCI **-1.293.653.003**.
- Q1 suy ra từ H1 trừ Q2: parent **17.971.404.641**, NCI **1.040.937.615**.
- Chênh lệch phân bổ giữa Q1 công bố gốc và Q1 hàm ý vẫn là **1.117.693.283 VND**, trong khi tổng PAT không đổi.

Q3/2025 YTD trừ Q3 current-quarter tiếp tục khớp chính xác với H1 YTD theo cơ sở phân bổ của Q2. BCTC kiểm toán FY2025 và Note 26 không cung cấp báo cáo Q1 điều chỉnh hoặc bảng cầu nối giải thích việc thay đổi phân bổ nói trên.

**Kết luận hồ sơ:**
- **B — cầu nối biến động vốn NCI toàn FY2025: PASS.** Khoản tăng 21 tỷ đã được thuyết minh và toàn bộ rollforward B04 cuối năm khớp 0.
- **A — phân bổ lợi nhuận B02 giữa Q1 gốc và H1/YTD: PENDING.** Không thay số Q1, không backsolve vào dữ liệu chính, không thêm balancing plug.
- Không sửa `data/financials-VDS.json` và không gộp số liệu RI vào HN.


## 6. Xác nhận thêm bằng ảnh B04 Q3/2025 và định vị thời điểm tăng vốn

- B04 Q3/2025, VietstockFinance document **523128**, PDF page **18** / printed page **13**, đã được render trực tiếp từ PDF gốc ở 300 DPI? Không: artifact này là render 150 DPI; kiểm tra lại ảnh gốc PDF page 18 đã xoay đúng chiều. Artifact workflow run **41858315839**, artifact **13339205504**, file `page-18.jpg`.
- B04 row 9 “Lợi ích cổ đông không kiểm soát”, cột năm nay: số dư đầu năm **48.488.925.445 VND**; tăng trong kỳ **22.785.197.412 VND**; không có số giảm hiện hành; số dư cuối 30/09/2025 **71.274.122.857 VND**. Phép cộng B04 khớp chính xác.
- B04 Q2/2025 PDF page **19** / printed page **13** đã được kiểm tra ảnh 300 DPI trước đó: NCI đầu năm **48.488.925.445 VND**, giảm trong kỳ **1.238.461.133 VND**, cuối 30/06/2025 **47.250.464.312 VND**; không có khoản tăng hiện hành.
- Q3 B02 standalone ghi NCI PAT **3.023.658.546 VND**; Q3 B04 closing less Q2 closing = **24.023.658.545 VND**. Phần khác lợi nhuận = **20.999.999.999 VND**, chênh **-1 VND** so với khoản tăng 21 tỷ trong Note 26 FY2025. Sai khác 1 VND nhỏ hơn ngưỡng 0,01%, được ghi nhận là residual chứ không thêm plug.
- Vì vậy, khi kết hợp với Note 26 kiểm toán FY2025, bằng chứng định vị khoản tăng vốn 21 tỷ ở **Q3/2025** rất mạnh: Note 26 ghi “Tăng phần vốn sở hữu ở công ty con” 21 tỷ; B04 Q3 cho thấy phần tăng NCI ngoài lợi nhuận trong riêng Q3 là 20.999.999.999 VND. Không tự ý đổi giá trị nguồn hay chỉnh 1 VND.
- B04 FY2025 Note 26/B04 cuối năm vẫn khớp chính xác toàn năm: +21 tỷ vốn ở công ty con, lỗ đã thực hiện -1.396.298.463, lỗ chưa thực hiện -547.773.687; NCI cuối năm 67.544.853.295 VND.
- Đây xác nhận **hồ sơ B (vốn NCI 21 tỷ): PASS** và thời điểm phát sinh có thể xác định ở Q3/2025. Nó **không giải thích hồ sơ A**: sai khác phân bổ B02 Q1 gốc so với H1 trừ Q2 vẫn 1.117.693.283 VND.


## 7. Đối chiếu các cột so sánh kỳ sau và giới hạn hồ sơ A

### 7.1. B02 Q1/2026 so sánh Q1/2025
- VietstockFinance document **543855**, B02 PDF page **13** / printed page **8**, giữ số Q1/2025 comparative: PAT **19.012.342.256 VND**, parent **19.089.097.924 VND**, NCI **-76.755.668 VND**.
- Các giá trị trùng B02 Q1/2025 gốc; không phải số Q1 implied từ H1 less Q2.

### 7.2. B02 Q2/2026 so sánh H1/2025
- VietstockFinance document **555653**, PDF member `VDS_Baocaotaichinh_Q2_2026_Hopnhat.pdf` trong `reports/raw/VDS/auto-vds-20261021/6ca61e80d55ffaac.zip`; B02 PDF page **13** / printed page **8**, trực tiếp kiểm tra ảnh 300 DPI.
- Cột H1/2025 comparative vẫn giữ PAT **7.818.436.589 VND**, parent **8.071.151.977 VND**, NCI **-252.715.388 VND**, giống Q2/2025 H1/YTD. Render workflow run **41878236428**, artifact **13347787384**, SHA-256 PDF member `cf4351deb1e3c184ba11ff18f8c81ce15cc41e37070830f666dd48b33a7e471d`.

### 7.3. Hồ sơ công bố/giải trình Q1 và Q2/2025
- VDS công bố Q1/2025 gồm BCTC hợp nhất và công văn giải trình biến động LNST Q1/2025 so với Q1/2024; công văn số **387/2025/CV-TCKT**, ngày **29/04/2025**, tập trung PBT, thuế và LNST tổng hợp, không phải bảng cầu nối parent/NCI. Trang công bố: `https://www.vdsc.com.vn/quan-he-co-dong/cong-bo-thong-tin/rong-viet-cong-bo-bao-cao-tai-chinh-hop-nhat-quy-1-2025-va-giai-trinh-chenh-lech-loi-nhuan-i880`.
- VDS công bố Q2/2025 gồm BCTC hợp nhất và công văn giải trình LNST Q2/2025 so với Q2/2024; trang công bố: `https://www.vdsc.com.vn/en/investor-relations/disclosures/vdsc-discloses-the-consolidated-financial-statements-2q2025-and-explanation-of-profit-differences-i912?groupId=1`. Nội dung công bố được rà không nêu điều chỉnh phân bổ parent/NCI của Q1 hoặc cầu nối Q1/H1.

### 7.4. Kết luận cập nhật
- **Hồ sơ B – vốn NCI 21 tỷ:** PASS/CLOSED; Note 26 kiểm toán và Q3 B04 xác nhận tăng phần vốn sở hữu ở công ty con trong Q3/2025.
- **Hồ sơ A – phân bổ B02 Q1/H1:** vẫn PENDING. Q1/2026 comparative giữ số Q1 original, Q2/2026 comparative giữ số H1/YTD, Q3/2025 YTD less Q3 standalone khớp H1. Không tìm thấy trong các công bố/giải trình đã rà một báo cáo Q1 restated hoặc bảng giải thích phân bổ parent/NCI.
- Giữ nguyên Q1 original và Q2 H1/YTD original; số Q1 tính từ H1 less Q2 chỉ là phép đối chiếu, không phải số Q1 đã công bố. Không sửa `data/financials-VDS.json`.


## 8. Đối chiếu thêm Nghị quyết ĐHĐCĐ FY2025 về điều chỉnh lợi ích NCI

- Nghị quyết ĐHĐCĐ thường niên FY2025 số **01/2026/BB-ĐHĐCĐ**, ngày **16/04/2026**, được công bố ngày **17/04/2026**, tại bảng phân phối lợi nhuận FY2025 ghi riêng dòng **“Điều chỉnh Lợi ích cổ đông không kiểm soát” = -1.944.072.150 VND**.
- Giá trị này khớp tuyệt đối tổng hai dòng Note 26: lỗ đã thực hiện **-1.396.298.463 VND** + lỗ chưa thực hiện **-547.773.687 VND** = **-1.944.072.150 VND**.
- Nghị quyết sử dụng số điều chỉnh NCI này trong cầu nối xác định lợi nhuận chưa phân phối lũy kế hợp nhất cuối năm; đây là điều chỉnh ở tầng retained earnings/equity, không phải dòng NCI PAT của B02. Vì vậy không được áp đặt phép bằng giữa NCI equity movement và B02 NCI PAT.
- Nguồn văn bản nghị quyết: `https://static2.vietstock.vn/vietstock/2026/4/17/20260417___vds___bbh_va_nqdhdcd_thuong_nien_fy_2025.pdf`, đoạn bảng phân phối lợi nhuận FY2025 (printed pages 14–15; PDF page index 14 trong tool view).
- Kết luận: phần điều chỉnh NCI **1.944.072.150 VND đã có phân loại/định danh trong Nghị quyết ĐHĐCĐ**. Điều này giúp phân biệt rõ với câu hỏi B02 parent/NCI Q1/H1 vẫn còn PENDING **1.117.693.283 VND**.
