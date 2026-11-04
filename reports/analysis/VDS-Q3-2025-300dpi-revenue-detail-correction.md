# VDS Q3/2025 — bổ sung kiểm tra B02 ở 300 DPI, sửa OCR HTM và đóng doanh thu row20

- Nguồn: VietstockFinance document **523128**, BCTC hợp nhất VDS Q3/2025.
- PDF: `reports/raw/VDS/auto-vds-20261021/bd7db8914d33e414.pdf`
- URL: https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%203/VDS_Baocaotaichinh_Q3_2025_Hopnhat.pdf
- Workflow render bổ sung: https://github.com/kiemtimem123/so-lieu/actions/runs/41825721924
- Artifact: `vietstock-source-review-VDS-2025-Q3`, ID `13318947582`, SHA-256 `d1fa36877d114892b63b343deae17481d4f12ba721e7e7ef98fb89113fb04da0`.
- Render bổ sung PDF pages **11–13** ở **300 DPI**: B02 trang in 6–8. Các trang B01/B03 đã được visual review trước đó trong artifact 180 DPI.

## Sửa lỗi OCR doanh thu — không phải doanh thu tư vấn

Trên B02 PDF page 11:
- Row 1.2, lãi từ HTM trong **cột riêng Quý III/2025** là **11,491,178,083 VND**.
- Snapshot OCR cũ đọc nhầm thành **11,401,178,083 VND**, thiếu đúng **90,000,000 VND**.
- Row 1.8, doanh thu tư vấn đầu tư trong **cột Quý III/2025 để trống**.
- Row 1.8 trong cột **lũy kế 9 tháng** là **881,819,860 VND**; giá trị này bằng Q1/2025 832,001,623 + Q2/2025 49,818,237, vì vậy không có doanh thu row1.8 phát sinh riêng Q3 để ghi nhận.
- Sau khi sửa HTM, tổng các dòng doanh thu Q3 khớp row20 chính xác; không cần và không được gán 90 triệu hoặc 881,819,860 vào row1.8 Q3.

### Doanh thu hoạt động riêng Q3/2025 (VND)

| Dòng B02 | Chỉ tiêu | Q3/2025 |
|---|---|---:|
| 1.1 | FVTPL | 259,287,392,878 |
| 1.2 | HTM | 11,491,178,083 |
| 1.3 | Cho vay và phải thu | 108,048,129,231 |
| 1.4 | AFS | 5,155,965,000 |
| 1.6 | Môi giới | 81,425,970,141 |
| 1.7 | Bảo lãnh/phát hành | — |
| 1.8 | Tư vấn đầu tư | — |
| 1.9 | Lưu ký | 1,960,643,491 |
| 1.10 | Tư vấn tài chính | 1,754,090,910 |
| 1.11 | Thu nhập hoạt động khác | 812,043,806 |
| **20** | **Tổng doanh thu hoạt động** | **469,935,413,540** |

Tổng cấu phần = row20, residual **0 VND**.

### Chi phí hoạt động riêng Q3/2025 (VND)

| Dòng B02 | Chỉ tiêu | Q3/2025 |
|---|---|---:|
| 2.1 | FVTPL (số âm theo báo cáo) | (29,733,185,559) |
| 2.3 | Lỗ AFS | 45,714,000 |
| 2.4 | Dự phòng/suy giảm tài sản tài chính | 66,940,600,625 |
| 2.6 | Chi phí tự doanh | 1,282,302,835 |
| 2.7 | Chi phí môi giới | 55,091,767,129 |
| 2.8 | Bảo lãnh/phát hành | — |
| 2.9 | Tư vấn chứng khoán | 15,200,000 |
| 2.10 | Lưu ký | 2,236,805,580 |
| 2.11 | Tư vấn tài chính | 4,182,481,667 |
| 2.12 | Chi phí dịch vụ khác | 6,267,062,492 |
| **40** | **Tổng chi phí hoạt động** | **106,328,748,769** |

Row2.1 được giữ dấu âm đúng theo nguồn; tổng các dòng có dấu như báo cáo = row40, residual **0 VND**. Không bỏ row23.3 AFS loss 45,714,000.

## Các dòng còn lại B02 được xác nhận tại 300 DPI

- Doanh thu tài chính row50 **19,292,895,989 VND**, gồm FX gain **77,177** và thu nhập row42 **19,292,818,812**.
- Chi phí tài chính row60 **9,560,904,110 VND**, gồm lỗ tỷ giá **250,000,000** và lãi vay **9,310,904,110**.
- Chi phí bán hàng row61 để trống; chi phí quản lý row62 **47,492,454,241 VND**.
- Lợi nhuận hoạt động row70 **325,846,202,409**; thu nhập khác row71 **748,950**; chi phí khác row72 trống; lợi nhuận khác row80 **748,950**; LNTT row90 **325,846,951,359**.
- Thuế hiện hành **26,295,285,720**; thuế hoãn lại **35,294,569,352**; tổng thuế **61,589,855,072**.
- LNST **264,257,096,287**; phân bổ công ty mẹ **261,233,437,741**; NCI **3,023,658,546**; EPS **960**.

Các cầu nối lợi nhuận hoạt động, lợi nhuận trước thuế, thuế, PAT, parent/NCI residual đều **0 VND**.

## Cột lũy kế 9M/2025 được lưu riêng

- Row20 doanh thu lũy kế **819,858,909,744 VND**; cấu phần row1.1–1.11 gồm HTM **27,460,602,740** và row1.8 tư vấn **881,819,860**.
- Row40 chi phí lũy kế **379,630,030,213 VND**; bao gồm row23.3 AFS **45,714,000**, row24 dự phòng **194,209,140,779**, row29 **15,200,000** và các dòng còn lại như sidecar/ảnh nguồn.
- Lợi nhuận hoạt động lũy kế **331,035,265,945**; LNTT **331,048,115,091**; thuế **58,972,582,215**; PAT **272,075,532,876**; parent **269,304,589,718**; NCI **2,770,943,158**; EPS YTD **990**.
- HTM Q1 **4,734,246,576** + Q2 **11,235,178,081** + Q3 **11,491,178,083** = 9M **27,460,602,740**, residual 0.
- Advisory Q1 **832,001,623** + Q2 **49,818,237** = 9M **881,819,860**; Q3 current cell blank.

## Kết luận và trạng thái

B02 Q3/2025 row20 revenue detail đã PASS; trước đó residual 90 triệu là OCR HTM sai chữ số, không phải thiếu row1.8. B02 expense detail cũng PASS, bao gồm row23.3 AFS loss. Các cầu nối B02 current Q3 và YTD đều residual **0 VND**. Q3/2025 detail exception đã đóng; row1.8 Q3 vẫn null đúng theo ảnh.

Snapshot data commit: `8f22d161e6125211c1d102a79b8bc517d354d68e`.
