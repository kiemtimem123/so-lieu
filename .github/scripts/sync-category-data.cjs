const fs = require("node:fs");
const path = require("node:path");

const definitions = [
  { id: 22675, category: "transport", name: "Tổng khối lượng vận chuyển hàng hóa", unit: "Nghìn tấn", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/tong-khoi-luong-van-chuyen-hang-hoa-22675" },
  { id: 30221, category: "agriculture", name: "Diện tích sản lượng lúa mùa miền Nam", unit: "Nghìn ha", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/dien-tich-san-luong-lua-mua-mien-nam-30221" },
  { id: 32542, category: "ports", name: "Tổng DWT tàu vào cảng biển Cảng vụ TP. Hồ Chí Minh", unit: "DWT", source: "Cục Hàng hải Việt Nam (các Cảng vụ Hàng hải)", url: "https://dulieukinhte.com/du-lieu-dong/tong-dwt-tau-vao-cang-bien-cang-vu-tp-ho-chi-minh-32542" },
  { id: 31248, category: "property", name: "Số dự án nhà ở thương mại được chấp thuận chủ trương đầu tư", unit: "Dự án", source: "Bộ Xây dựng", url: "https://dulieukinhte.com/du-lieu-dong/so-du-an-nha-o-thuong-mai-duoc-chap-thuan-chu-truong-dau-tu-31248" },
  { id: 34763, category: "labor", name: "Lao động có việc làm", unit: "Nghìn người", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/lao-dong-co-viec-lam-34763" },
  { id: 22659, category: "passengers", name: "Tổng số khối lượng vận chuyển hành khách", unit: "Nghìn người", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/tong-so-khoi-luong-van-chuyen-hanh-khach-22659" },
  { id: 22905, category: "agri-price", name: "Chỉ số giá sản xuất nông, lâm nghiệp và thủy sản so cùng kỳ", unit: "%", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/chi-so-gia-san-xuat-nong-lam-nghiep-va-thuy-san-so-cung-ky-22905" },
  { id: 18709, category: "retail", name: "Tổng mức bán lẻ hàng hóa và dịch vụ", unit: "Tỷ đồng", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/tong-muc-ban-le-hang-hoa-va-dich-vu-18709" },
  { id: 22603, category: "exports", name: "Tổng kim ngạch xuất khẩu", unit: "Triệu USD", source: "Tổng cục Hải quan", url: "https://dulieukinhte.com/du-lieu-dong/tong-kim-ngach-xuat-khau-22603" },
  { id: 22606, category: "imports", name: "Tổng kim ngạch nhập khẩu", unit: "Triệu USD", source: "Tổng cục Hải quan", url: "https://dulieukinhte.com/du-lieu-dong/tong-kim-ngach-nhap-khau-22606" },
  { id: 24655, category: "cpi", name: "Chỉ số giá tiêu dùng CPI lũy kế từ đầu năm", unit: "%", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/chi-so-gia-tieu-dung-cpi-luy-ke-tu-dau-nam-24655" },
  { id: 22865, category: "logistics-index", name: "Chỉ số vận tải kho bãi so quý trước", unit: "%", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/chi-so-van-tai-kho-bai-so-quy-truoc-22865" },
  { id: 22613, category: "sea-freight", name: "Luân chuyển hàng hóa đường biển", unit: "Triệu tấn/Km", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/luan-chuyen-hang-hoa-duong-bien-22613" },
  { id: 36762, category: "corporate-bonds-property", name: "Phát hành trái phiếu doanh nghiệp ngành bất động sản", unit: "Tỷ đồng", source: "Hiệp hội Thị trường Trái phiếu Việt Nam (VBMA)", url: "https://dulieukinhte.com/du-lieu-dong/phat-hanh-tpdn-nganh-bat-dong-san-36762" },
  { id: 33392, category: "agri-exports-rubber", name: "Giá xuất khẩu bình quân cao su", unit: "USD/tấn", source: "Tổng cục Hải quan", url: "https://dulieukinhte.com/du-lieu-dong/gia-xuat-khau-binh-quan-cao-su-33392" },
  { id: 33408, category: "agri-imports-rubber", name: "Giá nhập khẩu bình quân cao su", unit: "USD/tấn", source: "Tổng cục Hải quan", url: "https://dulieukinhte.com/du-lieu-dong/gia-nhap-khau-binh-quan-cao-su-33408" },
  { id: 33265, category: "credit-balance", name: "Tổng dư nợ tín dụng đối với nền kinh tế", unit: "Tỷ đồng", source: "Ngân hàng Nhà nước Việt Nam (NHNN)", url: "https://dulieukinhte.com/du-lieu-dong/tong-du-no-tin-dung-doi-voi-nen-kinh-te-33265" },
  { id: 29926, category: "credit-growth", name: "Tăng trưởng tín dụng so đầu năm", unit: "%", source: "Ngân hàng Nhà nước Việt Nam (NHNN)", url: "https://dulieukinhte.com/du-lieu-dong/tang-truong-tin-dung-so-dau-nam-29926" },
  { id: 34758, category: "labor-force", name: "Lực lượng lao động", unit: "Nghìn người", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/luc-luong-lao-dong-34758" },
  { id: 29406, category: "global-rice", name: "Giá gạo thế giới", unit: "Theo nguồn", source: "Dữ Liệu Kinh Tế (nguồn tổng hợp)", url: "https://dulieukinhte.com/du-lieu-dong/gia-gao-the-gioi-29406" },
  { id: 66457, category: "global-rubber", name: "Giá cao su TSR20 thế giới", unit: "Theo nguồn", source: "Dữ Liệu Kinh Tế (nguồn tổng hợp)", url: "https://dulieukinhte.com/du-lieu-dong/gia-cao-su-tsr20-ine-the-gioi-66457" },
  { id: 29380, category: "global-steel", name: "Giá thép thanh thế giới", unit: "Theo nguồn", source: "Dữ Liệu Kinh Tế (nguồn tổng hợp)", url: "https://dulieukinhte.com/du-lieu-dong/gia-thep-thanh-the-gioi-29380" },
  { id: 18699, category: "housing-cpi", name: "Chỉ số giá tiêu dùng nhà ở và vật liệu xây dựng", unit: "Điểm", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/chi-so-gia-tieu-dung-nha-o-va-vat-lieu-xay-dung-18699" },
  { id: 22870, category: "coastal-shipping-index", name: "Chỉ số vận tải đường ven biển và viễn dương so quý trước", unit: "%", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/chi-so-van-tai-duong-ven-bien-va-vien-duong-so-quy-truoc-22870" },
  { id: 27690, category: "omo-buy-total", name: "Tổng khối lượng trúng thầu mua (bơm tiền) nghiệp vụ thị trường mở OMO", unit: "Tỷ đồng", source: "Ngân hàng Nhà nước Việt Nam (NHNN), qua Dữ Liệu Kinh Tế", url: "https://dulieukinhte.com/du-lieu-dong/tong-mua-bom-tien-nghiep-vu-thi-truong-mo-omo-27690" },
  { id: 53631, category: "omo-net-outstanding", name: "Chênh lệch lưu hành OMO và tín phiếu NHNN", unit: "Tỷ đồng", source: "Ngân hàng Nhà nước Việt Nam (NHNN), qua Dữ Liệu Kinh Tế", url: "https://dulieukinhte.com/du-lieu-dong/chenh-lech-luu-hanh-omo-va-tin-phieu-nhnn-53631" },

  { id: 33445, category: "m2", name: "Tổng phương tiện thanh toán M2", unit: "Tỷ đồng", source: "Ngân hàng Nhà nước Việt Nam (NHNN)", url: "https://dulieukinhte.com/du-lieu-dong/tong-phuong-tien-thanh-toan-m2-33445" },
  { id: 33446, category: "household-deposits", name: "Tiền gửi của dân cư trong cung tiền M2", unit: "Tỷ đồng", source: "Ngân hàng Nhà nước Việt Nam (NHNN)", url: "https://dulieukinhte.com/du-lieu-dong/tien-gui-cua-dan-cu-trong-cung-tien-m2-33446" },
  { id: 33447, category: "corporate-deposits", name: "Tiền gửi của các TCKT trong cung tiền M2", unit: "Tỷ đồng", source: "Ngân hàng Nhà nước Việt Nam (NHNN)", url: "https://dulieukinhte.com/du-lieu-dong/tien-gui-cua-cac-tckt-trong-cung-tien-m2-33447" },
  { id: 37096, category: "gold-doji-buy", name: "Giá vàng DOJI Sài Gòn mua vào", unit: "Triệu đồng/lượng", source: "Dữ Liệu Kinh Tế (nguồn tổng hợp)", url: "https://dulieukinhte.com/du-lieu-dong/gia-vang-doji-sai-gon-mua-vao-37096" },
  { id: 37105, category: "gold-btmc-buy", name: "Giá vàng Bảo Tín Minh Châu mua vào", unit: "Triệu đồng/lượng", source: "Dữ Liệu Kinh Tế (nguồn tổng hợp)", url: "https://dulieukinhte.com/du-lieu-dong/gia-vang-bao-tin-minh-chau-mua-vao-37105" },
  { id: 37106, category: "gold-btmc-sell", name: "Giá vàng Bảo Tín Minh Châu bán ra", unit: "Triệu đồng/lượng", source: "Dữ Liệu Kinh Tế (nguồn tổng hợp)", url: "https://dulieukinhte.com/du-lieu-dong/gia-vang-bao-tin-minh-chau-ban-ra-37106" },
  { id: 33340, category: "deposit-mb-12m", name: "Lãi suất tiết kiệm khách hàng cá nhân MB 12 tháng", unit: "%/năm", source: "Dữ Liệu Kinh Tế (chuỗi lịch sử biểu lãi suất MB)", url: "https://dulieukinhte.com/du-lieu-dong/lai-suat-tiet-kiem-khach-hang-ca-nhan-mb-12-thang-33340" }

];
function fail(message) { console.error("ERROR:", message); process.exit(1); }
let response;
try {
  const first = JSON.parse(fs.readFileSync("category-response-1.json", "utf8"));
  const second = JSON.parse(fs.readFileSync("category-response-2.json", "utf8"));
  const third = JSON.parse(fs.readFileSync("category-response-3.json", "utf8"));
  if (!first || !Array.isArray(first.data) || !second || !Array.isArray(second.data) || !third || !Array.isArray(third.data)) {
    fail("Một trong các lô API không trả về mảng data hợp lệ.");
  }
  response = { data: [...first.data, ...second.data, ...third.data] };
} catch (error) {
  fail("Không đọc được phản hồi API theo lô: " + error.message);
}
if (!response || !Array.isArray(response.data)) fail("API không trả về mảng data.");
const outputData = [];
const outputPath = path.join("data", "category-data.json");
let previousById = new Map();
try {
  const previous = JSON.parse(fs.readFileSync(outputPath, "utf8"));
  if (Array.isArray(previous.data)) previousById = new Map(previous.data.map(item => [String(item.id), item]));
} catch (_) {
  console.log("Chưa có snapshot trước đó hợp lệ; sẽ tạo snapshot mới.");
}
for (const def of definitions) {
  const series = response.data.find(item => String(item.id) === String(def.id));
  if (!series || series.skipped || !Array.isArray(series.observations)) {
    fail("Thiếu chuỗi dữ liệu " + def.id + ". Không cập nhật snapshot để tránh ghi dữ liệu thiếu.");
  }
  const today = new Date().toISOString().slice(0, 10);
  const fetchedObservations = series.observations
    .filter(item => item && /^\d{4}-\d{2}-\d{2}$/.test(String(item.date)) && String(item.date) <= today && item.value !== null && item.value !== undefined && Number.isFinite(Number(item.value)))
    .map(item => ({ date: String(item.date), value: Number(item.value) }));
  const previous = previousById.get(String(def.id));
  const merged = new Map();
  for (const item of [...(Array.isArray(previous?.observations) ? previous.observations : []), ...fetchedObservations]) {
    if (item && /^\d{4}-\d{2}-\d{2}$/.test(String(item.date)) && String(item.date) <= today && item.value !== null && item.value !== undefined && Number.isFinite(Number(item.value))) {
      merged.set(String(item.date), { date: String(item.date), value: Number(item.value) });
    }
  }
  const observations = [...merged.values()].sort((a, b) => a.date.localeCompare(b.date)).slice(-50);
  if (!observations.length) fail("Không có quan sát hợp lệ đến ngày hiện tại cho " + def.id);
  const latest = observations[observations.length - 1];
  if (previous?.date && latest.date < previous.date) fail("Ngăn ghi đè bằng dữ liệu cũ cho " + def.category);
  if (previous?.date && latest.date === previous.date && !fetchedObservations.some(item => item.date > previous.date)) {
    console.warn("CẢNH BÁO: API không có quan sát mới hơn snapshot hiện tại cho " + def.category + " (" + previous.date + "); giữ nguyên dữ liệu mới nhất đã lưu.");
  }
  outputData.push({ ...def, value: latest.value, date: latest.date, unit: series.unit || previous?.unit || def.unit, observations });
}
const output = { source: "DulieuKinhte API", fetchedAt: new Date().toISOString(), data: outputData };
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const tempPath = outputPath + ".tmp";
fs.writeFileSync(tempPath, JSON.stringify(output, null, 2) + "\n", "utf8");
fs.renameSync(tempPath, outputPath);
console.log("Đã lưu " + outputData.length + " chuỗi dữ liệu theo danh mục.");
for (const item of outputData) console.log(item.category + " | " + item.name + " | " + item.value + " " + item.unit + " | " + item.date);
