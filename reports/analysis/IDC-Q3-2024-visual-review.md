# IDC Q3/2024 — kiểm tra trực quan B01/B02/B03 và đối chiếu 9M

- Nguồn: VietstockFinance document ID **483651**, BCTC hợp nhất IDC Q3/2024.
- ZIP: `reports/raw/IDC/auto-idc-20261021/ba6b182fb273799c.zip`
- PDF member: `1_idc_2024_11_1_1f04f63_1028tctbtc_29102024_cbtt_bctc_hop_nhat_signed.pdf`
- URL nguồn: https://static2.vietstock.vn/data/HNX/2024/BCTC/VN/QUY%203/IDC_Baocaotaichinh_Q3_2024_Hopnhat.zip
- Workflow run: https://github.com/kiemtimem123/so-lieu/actions/runs/41761569855
- Artifact: `vietstock-source-review-IDC-2024-Q3`, ID `13290178465`, SHA-256 `4effef033ae15a4ee7b3cf1af2ea82d28d94d2654b56a0c6fced42cae600cf42`.
- Rendered PDF pages **8–14** at **180 DPI**: B01 pages 8–11, B02 page 12, B03 pages 13–14.

## B01 — bảng cân đối kế toán hợp nhất tại 30/09/2024 (VND)

| Chỉ tiêu | Giá trị |
|---|---:|
| Tài sản ngắn hạn | 6,744,296,361,521 |
| Tiền và tương đương tiền | 1,287,599,607,878 |
| Đầu tư tài chính ngắn hạn | 1,633,093,932,161 |
| Phải thu ngắn hạn | 2,302,284,480,566 |
| Hàng tồn kho | 1,461,433,828,368 |
| Tài sản ngắn hạn khác | 59,884,512,548 |
| Tài sản dài hạn | 11,390,620,067,429 |
| Tài sản cố định | 3,145,330,152,635 |
| **Tổng tài sản (row 270)** | **18,134,916,428,950** |
| Nợ ngắn hạn | 4,602,455,824,878 |
| Nợ dài hạn | 6,841,753,870,894 |
| **Tổng nợ phải trả (row 300)** | **11,444,209,695,772** |
| **Vốn chủ sở hữu (row 400)** | **6,690,706,733,178** |
| Lợi nhuận sau thuế chưa phân phối | 1,130,523,936,094 |
| Tổng nguồn vốn (row 440) | 18,134,916,428,950 |

Cấu phần tài sản ngắn hạn, tổng tài sản, tổng nợ và phương trình tài sản = nợ + vốn đều residual **0 VND**. Row 440 nhìn rõ trong ảnh gốc và bằng row 270.

## B02 — kết quả kinh doanh riêng Q3/2024 (VND)

Dùng **cột “Quý 3 năm 2024” đầu tiên**. Cột thứ ba là số lũy kế chín tháng, được lưu riêng dưới `income_statement_source_ytd_raw_vnd`; không đưa số 9M vào trường quý.

| Chỉ tiêu | Q3/2024 riêng quý |
|---|---:|
| Doanh thu bán hàng và cung cấp dịch vụ | 2,275,542,075,430 |
| Giảm trừ doanh thu | (12,347,222) |
| **Doanh thu thuần** | **2,275,529,728,208** |
| Giá vốn hàng bán | (1,482,208,258,233) |
| **Lợi nhuận gộp** | **793,321,469,975** |
| Doanh thu tài chính | 44,433,707,502 |
| Chi phí tài chính | (34,399,178,354) |
| Trong đó: chi phí lãi vay | (30,953,328,439) |
| Lãi từ công ty liên kết | 197,452,841 |
| Chi phí bán hàng | (27,442,146,367) |
| Chi phí quản lý doanh nghiệp | (61,006,782,583) |
| **Lợi nhuận hoạt động** | **715,104,523,014** |
| Thu nhập khác | 3,389,615,048 |
| Chi phí khác | (1,847,402,659) |
| Lợi nhuận khác | 1,542,212,389 |
| **Lợi nhuận trước thuế** | **716,646,735,403** |
| Chi phí thuế TNDN hiện hành | (153,565,492,375) |
| Thu nhập thuế TNDN hoãn lại | 11,263,775,631 |
| **Tổng chi phí thuế TNDN** | **142,301,716,744** |
| **Lợi nhuận sau thuế** | **574,345,018,659** |
| LNST thuộc cổ đông công ty mẹ | 511,013,714,299 |
| Lợi ích cổ đông không kiểm soát | 63,331,304,360 |
| EPS cơ bản | 1,549 đồng/cổ phiếu |

Các cầu nối doanh thu/giảm trừ, giá vốn/lợi nhuận gộp, lợi nhuận hoạt động, lợi nhuận khác, LNTT, thuế–LNST và phân bổ mẹ/NCI đều residual **0 VND**.

## B02 — cột lũy kế 9 tháng 2024 (VND), lưu tách riêng

| Chỉ tiêu | 9M/2024 |
|---|---:|
| Doanh thu thuần | 6,891,075,592,325 |
| Giá vốn hàng bán | (4,189,600,827,023) |
| **Lợi nhuận gộp** | **2,701,474,765,302** |
| Doanh thu tài chính | 114,804,153,928 |
| Chi phí tài chính | (104,270,547,399) |
| Trong đó: chi phí lãi vay | (99,259,511,885) |
| Lãi từ công ty liên kết | 1,441,378,934 |
| Chi phí bán hàng | (96,450,931,294) |
| Chi phí quản lý doanh nghiệp | (175,960,415,611) |
| **Lợi nhuận hoạt động** | **2,441,038,403,860** |
| Thu nhập khác | 18,696,517,536 |
| Chi phí khác | (6,334,828,774) |
| Lợi nhuận khác | 12,361,688,762 |
| **Lợi nhuận trước thuế** | **2,453,400,092,622** |
| Chi phí thuế hiện hành | (539,496,264,187) |
| Thu nhập thuế hoãn lại | 41,486,498,925 |
| **Tổng chi phí thuế** | **498,009,765,262** |
| **Lợi nhuận sau thuế** | **1,955,390,327,360** |
| LNST thuộc cổ đông công ty mẹ | 1,638,637,053,794 |
| Lợi ích cổ đông không kiểm soát | 316,753,273,566 |
| EPS lũy kế được báo cáo | 4,966 đồng/cổ phiếu |

Đã đối chiếu 19 dòng B02 cộng dồn: **Q1/2024 + Q2/2024 + Q3/2024 = 9M/2024**. Toàn bộ residual theo từng dòng, gồm doanh thu, lợi nhuận, thuế, mẹ và NCI, đều **0 VND**. EPS 9M được ghi nhận như số báo cáo lũy kế, không cộng EPS các quý.

## B03 — lưu chuyển tiền tệ hợp nhất

### 9M/2024 theo báo cáo gốc (VND)

| Chỉ tiêu | 9M/2024 |
|---|---:|
| CFO | 3,581,088,955,857 |
| CFI | (1,308,653,005,272) |
| CFF | (2,318,597,493,209) |
| **Lưu chuyển tiền thuần** | **(46,161,542,624)** |
| Tiền và tương đương tiền đầu kỳ | 1,333,592,588,129 |
| Ảnh hưởng tỷ giá | 168,562,373 |
| **Tiền cuối kỳ** | **1,287,599,607,878** |
| Chi mua sắm, xây dựng TSCĐ và BĐS đầu tư (row 21) | (556,571,792,867) |
| Cổ tức, lợi nhuận đã trả cho chủ sở hữu (row 36) | (1,447,247,160,483) |

### Q3/2024 riêng quý — 9M trừ H1/2024 gốc (VND)

| Chỉ tiêu | Q3/2024 riêng quý |
|---|---:|
| CFO | 1,285,081,665,229 |
| CFI | (584,539,974,071) |
| CFF | (423,294,813,214) |
| **Lưu chuyển tiền thuần** | **277,246,877,944** |
| Ảnh hưởng tỷ giá | (64,692,858) |
| Tiền đầu kỳ (khớp số dư 30/06/2024) | 1,010,417,422,792 |
| Tiền cuối kỳ | 1,287,599,607,878 |
| CAPEX phát sinh riêng quý | (243,302,603,942) |
| Cổ tức đã trả phát sinh riêng quý | (21,516,304,093) |

Cả cầu nối CFO + CFI + CFF = net cash movement và cầu nối tiền đầu kỳ + net movement + FX = tiền cuối kỳ đều residual **0 VND** cho 9M và Q3 riêng. Tiền đầu Q3 = tiền cuối H1/2024, residual **0 VND**.

### Bảo toàn cơ sở dòng tiền đã chọn cho snapshot

Snapshot vẫn dùng cơ sở comparative Q3/2025 cho chuỗi dòng tiền top-level. Cột 9M được chọn trùng bộ tổng 9M xác nhận trên B03 gốc; tuy nhiên Q3 standalone được suy ra khi trừ H1 comparative selected khác với phép trừ H1 báo cáo gốc do phân loại CFO/CFI:
- Q3 original CFO **1,285,081,665,229 VND**, CFI **-584,539,974,071 VND**.
- Q3 selected standalone CFO **1,257,193,896,688 VND**, CFI **-556,652,212,064 VND**.
- CFF không đổi **-423,294,813,214 VND**; net cash và FX khác nhau đúng **6,534 VND** theo hai cột trình bày, mỗi bộ vẫn tự cân đối chính xác.

Không ghi đè các trường cashflow top-level selected. Bộ B03 gốc được giữ đầy đủ trong `cashflow_source_reconciliation.original_q3_2024_report_comparison`; không trộn CFO/CFI giữa hai cơ sở.

## Kết luận

**B01/B02/B03 visual PASS.** Đã lưu riêng cột Q3 và 9M của B02; 19 chỉ tiêu lợi nhuận cộng dồn từ ba quý khớp đúng báo cáo 9M. B03 gốc 9M/Q3 riêng, CAPEX và cổ tức đã kiểm tra trực quan; mọi cầu nối residual 0 VND. Dòng tiền top-level theo comparative selected vẫn nguyên trạng.

Data commit: `d14d0a148b7e7a6723c292e728ea95387e23c195`.
