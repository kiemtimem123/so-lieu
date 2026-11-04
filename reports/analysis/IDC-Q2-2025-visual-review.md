# IDC Q2/2025 — kiểm tra trực quan B01/B02/B03 và tổng hợp H1

- Nguồn: VietstockFinance document ID **514037**, BCTC hợp nhất IDC Q2/2025.
- Danh mục nguồn: https://finance.vietstock.vn/IDC/tai-tai-lieu.htm?doctype=1
- ZIP: `reports/raw/IDC/auto-idc-20261021/48616c2bb9d17c99.zip`
- PDF tiếng Anh đã kiểm tra: `1_idc_2025_7_30_2e1316b_en_financialstatementshn_q2_2025_s.pdf`
- PDF tiếng Việt trong cùng ZIP: `4_idc_2025_7_30_caaaf64_vi_baocaotaichinhhn_q2_2025_s.pdf`
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41784357124
- Artifact: `vietstock-source-review-IDC-2025-Q2`, ID `13300477616`, SHA-256 `0a3f8eecc5f54dade12b9dde4247f26064676c0937b6a898f5f08c3274567829`.
- Đã render và xem trực tiếp PDF pages **8–14**, **180 DPI**: B01 8–11, B02 12, B03 13–14.

## B01 — bảng cân đối kế toán hợp nhất tại 30/06/2025 (VND)

| Chỉ tiêu | Giá trị |
|---|---:|
| Tài sản ngắn hạn | 7,811,294,674,643 |
| Tiền và tương đương tiền | 863,253,933,107 |
| Đầu tư ngắn hạn | 4,019,330,803,621 |
| Phải thu ngắn hạn | 1,559,600,303,738 |
| Hàng tồn kho | 1,326,633,847,347 |
| Tài sản ngắn hạn khác | 42,475,786,830 |
| Tài sản dài hạn | 11,795,122,370,205 |
| Tài sản cố định | 3,035,410,975,751 |
| **Tổng tài sản (row 270)** | **19,606,417,044,848** |
| Nợ ngắn hạn | 3,669,554,755,411 |
| Nợ dài hạn | 8,481,390,563,394 |
| **Tổng nợ phải trả (row 300)** | **12,150,945,318,805** |
| **Vốn chủ sở hữu (row 400)** | **7,455,471,726,043** |
| Lợi nhuận sau thuế chưa phân phối | 1,603,390,908,975 |
| Tổng nguồn vốn (row 440) | 19,606,417,044,848 |

Tổng cấu phần tài sản ngắn hạn, tài sản ngắn + dài hạn, nợ ngắn + dài hạn và row 270 = row 300 + row 400 đều residual **0 VND**. Dòng 440 nhìn rõ trong ảnh trang 11; dấu đỏ không che giá trị.

## B02 — kết quả kinh doanh riêng Q2/2025 (VND)

Dùng cột đầu tiên **The second quarter of 2025**; không nhầm với Q2/2024 hoặc cột lũy kế 6 tháng.

| Chỉ tiêu | Q2/2025 |
|---|---:|
| **Doanh thu gộp (row 01)** | **1,763,197,891,011** |
| Giảm trừ doanh thu (row 02) | **0** |
| **Doanh thu thuần (row 10)** | **1,763,197,891,011** |
| Giá vốn hàng bán | (1,218,680,135,812) |
| **Lợi nhuận gộp** | **544,517,755,199** |
| Doanh thu tài chính | 62,954,887,826 |
| Chi phí tài chính | (29,939,147,355) |
| Trong đó: chi phí lãi vay | (28,604,086,345) |
| Lỗ từ công ty liên kết | (343,427,723) |
| Chi phí bán hàng | (21,450,520,742) |
| Chi phí quản lý doanh nghiệp | (64,454,735,514) |
| **Lợi nhuận hoạt động** | **491,284,811,691** |
| Thu nhập khác | 29,086,228,155 |
| Chi phí khác | (1,046,602,608) |
| Lợi nhuận khác | 28,039,625,547 |
| **Lợi nhuận trước thuế** | **519,324,437,238** |
| Thuế TNDN hiện hành | (102,821,214,554) |
| **Thuế hoãn lại — row 52** | **(539,315,464)** |
| **Tổng chi phí thuế TNDN** | **103,360,530,018** |
| **Lợi nhuận sau thuế** | **415,963,907,220** |
| LNST thuộc cổ đông công ty mẹ | 297,573,101,125 |
| Lợi ích cổ đông không kiểm soát | 118,390,806,095 |
| EPS cơ bản / pha loãng | 902 / 902 |

**Sửa lỗi OCR thuế:** ảnh PDF tiếng Anh trang 12 in row 52 **(539,315,464 VND)**. OCR tiếng Việt cũ ghi **(639,315,464 VND)**, lệch **100.000.000 VND**. Giá trị trực quan đã xác nhận là 539.315.464; không còn chênh thuế/PAT. Row 62 NCI cũng xác nhận **118.390.806.095 VND**, sửa OCR cũ 118.350.806.095 (lệch 40 triệu). Tổng thuế theo số có dấu nguồn = -(102.821.214.554) + -(539.315.464) = -(103.360.530.018); PBT trừ chi phí thuế = PAT. Mọi cầu nối B02 residual **0 VND**.

## B02 — cột lũy kế H1/2025, lưu riêng (VND)

Cột thứ ba “For the period ended 30 June 2025” đã được ghi riêng trong `income_statement_source_ytd_raw_vnd`, không đưa số sáu tháng vào trường quý II.

| Chỉ tiêu | H1/2025 |
|---|---:|
| Doanh thu gộp | 3,556,682,187,141 |
| Giảm trừ doanh thu | 0 |
| Doanh thu thuần | 3,556,682,187,141 |
| Giá vốn hàng bán | (2,460,773,595,359) |
| **Lợi nhuận gộp** | **1,095,908,591,782** |
| Doanh thu tài chính | 128,055,065,816 |
| Chi phí tài chính | (68,959,484,828) |
| Chi phí lãi vay | (64,668,168,033) |
| Lãi từ công ty liên kết | 17,054,849 |
| Chi phí bán hàng | (49,783,063,598) |
| Chi phí quản lý | (138,395,002,221) |
| **Lợi nhuận hoạt động** | **966,843,161,800** |
| Thu nhập khác | 77,940,338,711 |
| Chi phí khác | (4,750,416,068) |
| Lợi nhuận khác | 73,189,922,643 |
| **Lợi nhuận trước thuế** | **1,040,033,084,443** |
| Thuế hiện hành | (211,368,386,572) |
| Thu nhập thuế hoãn lại | 4,283,753,953 |
| **Tổng chi phí thuế** | **207,084,632,619** |
| **Lợi nhuận sau thuế** | **832,948,451,824** |
| LNST cổ đông công ty mẹ | 640,852,011,752 |
| NCI H1 (PAT trừ lợi nhuận mẹ) | 192,096,440,072 |
| EPS báo cáo H1 | 1,942 |

Đã cộng Q1/2025 + Q2/2025 và so với cột H1: **doanh thu gộp, giảm trừ, doanh thu thuần, giá vốn, lợi nhuận gộp, doanh thu/chi phí tài chính, lãi vay, liên kết, bán hàng, quản lý, lợi nhuận hoạt động, thu nhập/chi phí khác, LNTT, thuế hiện hành, thuế hoãn lại, tổng thuế, PAT và lợi nhuận mẹ đều residual 0 VND**. H1 NCI 192.096.440.072 là giá trị suy ra từ PAT H1 trừ lợi nhuận mẹ H1; nó đồng thời bằng NCI Q1 + Q2. OCR token H1 của dòng NCI bị cụt, nên không đánh dấu đây là số OCR đọc trực tiếp. EPS H1 là số báo cáo lũy kế, không kiểm tra bằng phép cộng EPS quý.

**Chuẩn hóa dấu thuế:** lưu thuế hoãn lại theo dấu nguồn của từng báo cáo: Q1/2025 là thu nhập thuế hoãn lại dương **4.823.069.417 VND**; Q2/2025 là chi phí thuế hoãn lại âm **-539.315.464 VND** (mặc dù tên dòng là “deferred tax income”, ảnh có ngoặc). Tổng H1 = **+4.283.753.953 VND**. Trường normalized top-level vẫn giữ quy ước chi phí thuế: Q1 là lợi ích thuế âm, Q2 là chi phí thuế dương. Không đồng nhất trường raw với trường normalized.

## B03 — dòng tiền H1/2025 và Q2 riêng (VND)

### B03 gốc của báo cáo Q2/2025

| Chỉ tiêu | H1/2025 YTD |
|---|---:|
| CFO | 1,402,209,397,523 |
| CFI | (2,438,216,817,714) |
| CFF | (288,817,920,091) |
| **Lưu chuyển tiền thuần** | **(1,324,825,340,282)** |
| Tiền đầu kỳ | 2,188,037,806,317 |
| Ảnh hưởng tỷ giá | 41,467,072 |
| **Tiền cuối kỳ** | **863,253,933,107** |
| CAPEX row 21 | (909,344,214,214) |
| Cổ tức đã trả row 36 | (588,587,063,470) |

Q2 riêng theo B03 gốc = H1 YTD trừ Q1/2025 YTD:
- CFO **809.015.066.804 VND**
- CFI **-1.693.078.122.700 VND**
- CFF **-545.521.959.637 VND**
- Net cash **-1.429.585.015.533 VND**
- FX **38.713.120 VND**
- Tiền đầu kỳ **2.292.800.235.520 VND**
- Tiền cuối kỳ **863.253.933.107 VND**
- CAPEX **-746.582.157.511 VND**
- Cổ tức **-568.281.373.470 VND**

CFO + CFI + CFF = net cash và tiền đầu kỳ + net cash + FX = tiền cuối kỳ; H1 và Q2 riêng đều residual **0 VND**.

### B03 comparative “As restated - Note 41” được chọn cho chuỗi hiển thị

Snapshot vẫn chọn cột H1/2025 đã trình bày lại trong BCTC Q2/2026:
- H1 CFO **876.372.147.509 VND**
- H1 CFI **-1.912.379.567.700 VND**
- H1 CFF **-288.817.920.091 VND**
- Net cash, FX, tiền đầu kỳ/cuối kỳ giữ nguyên so với B03 gốc.

Q2 riêng theo cơ sở selected As-restated:
- CFO **283.177.816.790 VND**
- CFI **-1.167.240.872.686 VND**
- CFF **-545.521.959.637 VND**
- Net cash **-1.429.585.015.533 VND**
- FX **38.713.120 VND**
- Tiền đầu kỳ **2.292.800.235.520 VND**
- Tiền cuối kỳ **863.253.933.107 VND**

**Bản chất khác biệt:** comparative As-restated chuyển **525.837.250.014 VND** từ CFO sang CFI; CFF, net cash, FX và số dư tiền không đổi. Cả B03 gốc và B03 comparative selected đều có cầu nối dòng tiền/tiền cuối kỳ residual 0. Giữ bộ As-restated ở top-level snapshot như cơ sở đã lựa chọn; lưu B03 gốc Q2/2025 như bộ thay thế riêng, không trộn hai cơ sở.

## Kết luận

<badge color="success">B01/B02/B03 visual PASS</badge>

Q2/2025 đã hoàn tất kiểm tra nguồn và ảnh. Doanh thu gộp Q2 **1.763.197.891.011 VND** với giảm trừ bằng 0; H1 gross revenue **3.556.682.187.141 VND** khớp Q1+Q2. Sửa thuế hoãn lại OCR và NCI theo PDF tiếng Anh cùng ZIP; thuế/PAT và tất cả dòng B02 lũy kế khớp. Hai cơ sở B03 tự cân đối, top-level As-restated giữ nguyên.

Data commit: `def9868f713b16ae2955174d1689190df2d5af93`.
