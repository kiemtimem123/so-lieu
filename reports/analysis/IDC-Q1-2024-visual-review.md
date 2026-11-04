# IDC Q1/2024 — kiểm tra trực quan B01/B02/B03

- Nguồn: VietstockFinance document ID **462783**, BCTC hợp nhất IDC Q1/2024.
- PDF: `reports/raw/IDC/auto-idc-20261021/44694a289f32bd8c.pdf`
- URL: https://static2.vietstock.vn/data/HNX/2024/BCTC/VN/QUY%201/IDC_Baocaotaichinh_Q1_2024_Hopnhat.pdf
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41698364477
- Artifact: `vietstock-source-review-IDC-2024-Q1`, ID `13262217679`, SHA-256 `f335e18d8c2894b33bcf3c7593fbc98950434e42937233f528b0217baa7c7da9`.
- Rendered PDF pages 9–15 at 180 DPI: B01 pages 9–12, B02 page 13, B03 pages 14–15.

## B01 — bảng cân đối kế toán hợp nhất (VND)

| Chỉ tiêu | 31/03/2024 |
|---|---:|
| Tài sản ngắn hạn | 6,149,122,173,715 |
| Tiền và tương đương tiền | 1,108,047,375,757 |
| Đầu tư tài chính ngắn hạn | 966,774,198,900 |
| Phải thu ngắn hạn | 2,168,567,501,270 |
| Hàng tồn kho | 1,858,248,737,055 |
| Tài sản ngắn hạn khác | 47,484,360,733 |
| Tài sản dài hạn | 11,237,270,117,635 |
| Tài sản cố định | 3,155,290,701,843 |
| **Tổng tài sản** | **17,386,392,291,350** |
| Nợ ngắn hạn | 3,519,203,176,880 |
| Nợ dài hạn | 7,375,093,997,091 |
| **Tổng nợ phải trả** | **10,894,297,173,971** |
| **Vốn chủ sở hữu** | **6,492,095,117,379** |
| Tổng nguồn vốn (dòng 440) | 17,386,392,291,350 |

Các cấu phần tài sản ngắn hạn, tài sản dài hạn, nợ ngắn/dài hạn và tổng tài sản = nợ + vốn đều có residual **0 VND**.

## B02 — kết quả kinh doanh riêng Q1/2024 (VND)

Dùng cột đầu tiên **Quý I năm nay**. Không lấy các con số ở cột so sánh Q1/2023.

| Chỉ tiêu | Q1/2024 |
|---|---:|
| Doanh thu thuần | 2,467,056,536,161 |
| Giá vốn hàng bán | (1,368,769,156,854) |
| Lợi nhuận gộp | 1,098,287,379,307 |
| Doanh thu tài chính | 30,956,011,616 |
| Chi phí tài chính | (34,736,078,687) |
| Trong đó: chi phí lãi vay | (34,575,846,071) |
| Lãi từ công ty liên kết | 80,805,520 |
| Chi phí bán hàng | (41,894,251,738) |
| Chi phí quản lý doanh nghiệp | (51,089,217,428) |
| **Lợi nhuận hoạt động** | **1,001,604,648,590** |
| Thu nhập khác | 1,822,336,145 |
| Chi phí khác | (4,092,556,626) |
| Lợi nhuận khác | (2,270,220,481) |
| **Lợi nhuận trước thuế** | **999,334,428,109** |
| Chi phí thuế TNDN hiện hành | (211,205,688,538) |
| Thu nhập thuế TNDN hoãn lại | 9,045,683,826 |
| **Tổng chi phí thuế TNDN** | **202,160,004,712** |
| **Lợi nhuận sau thuế** | **797,174,423,397** |
| LNST thuộc cổ đông công ty mẹ | 695,138,495,107 |
| Lợi ích cổ đông không kiểm soát | 102,035,928,290 |
| EPS cơ bản | 2,106 đồng/cổ phiếu |

Các cầu nối doanh thu–giá vốn–lợi nhuận gộp, lợi nhuận hoạt động, lợi nhuận khác, LNTT, thuế–LNST và phân bổ mẹ/NCI đều có residual **0 VND**.

**Lỗi OCR/cột đã sửa:** trước đây parser đã lấy một số giá trị từ cột so sánh Q1/2023, khiến chi phí tài chính/lãi vay, chi phí quản lý, lợi nhuận hoạt động, các dòng khác, thuế và PAT bị trộn kỳ. Ảnh gốc xác nhận chi phí bán hàng **41,894,251,738 VND**; giá trị này là đúng và không tạo chênh cầu nối. Chi phí lãi vay đúng là **34,575,846,071 VND**, không phải 53,797,972,876 VND (số so sánh năm trước). EPS của báo cáo gốc là **2,106**.

Báo cáo Q1/2025 sau đó trình bày lại các giá trị so sánh Q1/2024 cho doanh thu đến NCI trùng với số gốc đã xác minh; EPS so sánh là **2,095**, thấp hơn EPS báo cáo gốc 11 đồng/cổ phiếu. Giữ riêng cả hai EPS theo đúng tài liệu và kỳ công bố, không ghi đè EPS gốc.

## B03 — lưu chuyển tiền tệ hợp nhất Q1/2024 (VND)

Q1 đồng thời là số lũy kế YTD.

| Chỉ tiêu | Q1/2024 |
|---|---:|
| Lưu chuyển tiền từ hoạt động kinh doanh (CFO) | 951,312,310,814 |
| Lưu chuyển tiền từ hoạt động đầu tư (CFI) | (154,748,226,063) |
| Lưu chuyển tiền từ hoạt động tài chính (CFF) | (1,022,256,653,200) |
| **Lưu chuyển tiền thuần trong kỳ** | **(225,692,568,449)** |
| Tiền đầu kỳ | 1,333,592,588,129 |
| Ảnh hưởng tỷ giá | 147,356,077 |
| **Tiền cuối kỳ** | **1,108,047,375,757** |
| Chi mua sắm/xây dựng TSCĐ (row 21) | (206,983,772,973) |
| Cổ tức, lợi nhuận đã trả (row 36) | (538,942,833,000) |

CFO + CFI + CFF = net cash movement; tiền đầu kỳ + net change + FX = tiền cuối kỳ. Cả hai residual đều **0 VND**.

## Kết luận

<badge color="success">B01/B02/B03 visual PASS</badge>

Snapshot đã được cập nhật: EPS top-level 2,106; phục hồi các chi tiết B01; xác nhận B02 đúng cột Q1/2024; bổ sung CAPEX và cổ tức chi trả trong B03. Không OCR lại. Mọi cầu nối số học có residual 0 VND.
