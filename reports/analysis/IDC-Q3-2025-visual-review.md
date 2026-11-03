# IDC Q3/2025 — kiểm tra trực quan PDF

- Mã tài liệu VietstockFinance: **523494**
- Phạm vi: BCTC hợp nhất
- PDF member: `4_idc_2025_10_30_de24c2b_en_financialstatementshn_q3_2025hn_s.pdf`
- URL: https://static2.vietstock.vn/data/HNX/2025/BCTC/VN/QUY%203/IDC_Baocaotaichinh_Q3_2025_Hopnhat/4_idc_2025_10_30_de24c2b_en_financialstatementshn_q3_2025hn_s.pdf
- Trang PDF đã xem: 8–14, 180 DPI; B01 8–11, B02 12, B03 13–14.
- GitHub Actions run: https://github.com/kiemtimem123/so-lieu/actions/runs/41690820936
- Artifact: `vietstock-source-review-IDC-2025-Q3`, ID `13257427801`, SHA-256 `8cb8bdc1153cbe20798090ae24e9513db67e91a2f42ffba02f657fa4151dcbb1`, retention 14 days.
- Metadata: `reports/raw/IDC/auto-idc-20261021/render-metadata-2025-Q3.json`.

## B01 — tình hình tài chính (VND)

| Chỉ tiêu | Giá trị |
|---|---:|
| Tài sản ngắn hạn | 9.562.532.464.360 |
| Tài sản dài hạn | 11.730.497.789.571 |
| Tổng tài sản (row 270) | 21.293.030.253.931 |
| Nợ ngắn hạn (row 310) | 4.317.438.822.891 |
| Nợ dài hạn (row 330) | 8.608.809.141.409 |
| Tổng nợ (row 300) | 12.926.247.964.300 |
| Vốn chủ sở hữu (row 400) | 8.366.782.289.631 |

- Total assets = current assets + non-current assets; residual 0 VND.
- Total liabilities = current liabilities + non-current liabilities; residual 0 VND.
- Total assets = total liabilities + equity; residual 0 VND.
- Row 440 amount is partly hidden by the issuer's red seal in PDF page 11. Do not transcribe the corrupt text-layer value and do not claim a 71,700 VND difference. The independently readable row 300 + row 400 matches row 270 exactly.

## B02 — kết quả kinh doanh, cột quý III riêng (VND)

| Chỉ tiêu | Giá trị |
|---|---:|
| Doanh thu bán hàng | 2.871.423.273.613 |
| Giảm trừ doanh thu | (93.800.926) |
| Doanh thu thuần | 2.871.329.472.687 |
| Giá vốn | (1.614.206.888.266) |
| Lợi nhuận gộp | 1.257.122.584.421 |
| Doanh thu tài chính | 84.797.217.769 |
| Chi phí tài chính | (34.133.582.233) |
| Trong đó: chi phí lãi vay | (33.912.013.940) |
| Lỗ công ty liên kết | (139.003.519) |
| Chi phí bán hàng | (26.561.121.573) |
| Chi phí quản lý | (70.669.003.009) |
| Lợi nhuận hoạt động | 1.210.417.091.856 |
| Thu nhập khác | 9.812.198.684 |
| Chi phí khác | (1.736.562.513) |
| Lợi nhuận khác | 8.075.636.171 |
| Lợi nhuận trước thuế | 1.218.492.728.027 |
| Thuế hiện hành | (265.623.067.711) |
| Thu nhập thuế hoãn lại | 28.267.841.672 |
| Lợi nhuận sau thuế | 981.137.501.988 |
| LNST cổ đông mẹ | 841.835.881.584 |
| LNST cổ đông không kiểm soát | 139.301.620.404 |
| EPS cơ bản / pha loãng | 2.218 / 2.218 |

Các cầu nối doanh thu thuần, lợi nhuận gộp, lợi nhuận hoạt động, lợi nhuận khác, LNTT, thuế–LNST và phân bổ mẹ/NCI đều residual 0 VND. Dùng cột riêng quý III, không dùng cột lũy kế 9 tháng cho B02.

## B03 — lưu chuyển tiền tệ

Nguồn Q3/2025 là YTD 9 tháng; số Q3 riêng lấy YTD Q3 trừ H1/2025 từ báo cáo Q2/2025 gốc cùng cơ sở trình bày. Comparative H1/2025 “As restated” từ Q2/2026 lưu riêng, không trộn vào phép tính này.

| Chỉ tiêu | 9M/2025 YTD (VND) | Q3 riêng (VND) |
|---|---:|---:|
| CFO | 2.943.740.801.880 | 1.541.531.404.357 |
| CFI | (4.680.519.162.668) | (2.242.302.344.954) |
| CFF | 340.361.746.335 | 629.179.666.426 |
| Biến động tiền thuần | (1.396.416.614.453) | (71.591.274.171) |
| Ảnh hưởng tỷ giá | 65.368.055 | 23.900.983 |
| Tiền đầu kỳ | 2.188.037.806.317 | 863.253.933.107 |
| Tiền cuối kỳ | 791.686.559.919 | 791.686.559.919 |

Q3 riêng: capex **(893.695.067.506) VND**; cổ tức đã trả **(57.513.573.250) VND**.

- Q3 9M flow residual: 0 VND.
- Q3 9M cash bridge residual: 0 VND.
- Original H1 flow and cash bridge residual: 0 VND.
- Q3 standalone flow residual: 0 VND.
- Q3 standalone cash bridge residual: 0 VND.

## Trạng thái

**B01/B02/B03: source text + visual review PASS.** Ngoại lệ ghi nhận: dòng 440 trang 11 bị con dấu che một phần; phương trình tổng độc lập khớp chính xác. Không cần OCR lại. Q3 standalone cash-flow basis was corrected and committed to same-original-basis subtraction.
