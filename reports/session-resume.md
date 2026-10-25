# Ghi chú tiếp nối phiên xử lý báo cáo tài chính

## Quy tắc tiếp tục

1. **Nguồn sự thật về tiến độ:** đọc `reports/processing-checkpoint.json` trước tiên. Khi thông tin trong ghi chú này khác checkpoint, luôn ưu tiên checkpoint và trạng thái workflow GitHub Actions mới nhất.
2. **Không nạp lại toàn bộ dữ liệu:** không đọc hết các tệp `data/financials-*.json` và không mở toàn bộ kho OCR. Chỉ đọc snapshot `data/financials-{SYMBOL}.json` của mã hiện tại và các sidecar liên quan trong `reports/raw/{SYMBOL}/`.
3. **Xử lý từng mã:** ưu tiên `activeSymbol` nếu chưa được đóng cho xử lý tự động; nếu không, dùng `resumeSymbolHint`. Chỉ chuyển mã sau khi checkpoint đã lưu trạng thái mã hiện tại.
4. **Bỏ qua dữ liệu không xác minh được:** giữ ô số liệu chưa xác minh ở trạng thái trống; đánh dấu chờ rà soát thủ công và `skipUnconfirmedAutomation=true` khi không cần tiếp tục OCR tự động. Không tự suy diễn số để cân đối báo cáo.
5. **Nguồn báo cáo:** chỉ dùng danh mục tài liệu VietstockFinance `https://finance.vietstock.vn/{ticker}/tai-tai-lieu.htm?doctype=1` và PDF/ZIP được liên kết tại đó.
6. **Giữ nguyên dữ liệu đã lưu:** không xóa `data/financials-*.json`, `reports/raw/`, hoặc checkpoint; chỉ sửa mã đang xử lý và lưu commit theo từng lượt.

## Trạng thái tham chiếu khi tạo ghi chú

- Nhánh: `main`.
- Mã đã hoàn tất gần nhất trong checkpoint: `BID`.
- Mã đang được tiếp tục tự động tại thời điểm tạo ghi chú: `VCI`.
- Workflow đang chạy tại thời điểm ghi chú: [OCR workflow #1586](https://github.com/kiemtimem123/so-lieu/actions/runs/40233050329).
- Các kỳ VCI còn chờ tự động trích xuất trong checkpoint lúc đó: `2024-Q2`, `2024-Q3`, `2024-Q4`. Nếu chúng không thể xác minh tự động, giữ trống dữ liệu thiếu, đóng ở trạng thái rà soát thủ công rồi chuyển sang mã kế tiếp (VCK theo thứ tự cấu hình hiện tại).

Ghi chú này chỉ là chỉ dẫn rút gọn; trạng thái hiện tại luôn phải được lấy từ `reports/processing-checkpoint.json` và workflow mới nhất, không dựa vào các mốc tham chiếu cũ phía trên.

## Latest continuation policy (2026-10-26 local time)

- VCI is configured with `skipUnconfirmedThroughPeriod: 2026-Q3` in `config/securities.json`. The selector skips unresolved VCI history through Q3/2026, but will re-open VCI automatically when a quarter later than Q3/2026 appears in its snapshot.
- The selector's quarter matcher was corrected in commit [4872ef5](https://github.com/kiemtimem123/so-lieu/commit/4872ef577892672f6919984a530ce3c977b8c795); the skip-through policy is in [c7317a0](https://github.com/kiemtimem123/so-lieu/commit/c7317a07140005eca4ebe1046fde13e8b737006c).
- Latest checkpoint read during this session (2026-10-25 21:02:49 UTC): VCI was still the only ticker incomplete for automation; `2024-Q2` was the remaining pending core period, while Q3/Q4 2024 and later periods were marked for manual review. Follow the live checkpoint/workflow, because the in-flight OCR pass may have changed this since.
- All other configured tickers were already marked `completeForAutomation: true`. With the user's instruction to skip unconfirmed values, do not reopen completed tickers just to repeat manual-review-only periods. The next new automatic work is triggered by a newer quarterly report or a genuinely incomplete checkpoint.
