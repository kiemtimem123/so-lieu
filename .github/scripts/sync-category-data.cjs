const fs = require("node:fs");
const path = require("node:path");

const definitions = [
  { id: 22675, category: "transport", name: "Tổng khối lượng vận chuyển hàng hóa", unit: "Nghìn tấn", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/tong-khoi-luong-van-chuyen-hang-hoa-22675" },
  { id: 30221, category: "agriculture", name: "Diện tích sản lượng lúa mùa miền Nam", unit: "Nghìn ha", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/dien-tich-san-luong-lua-mua-mien-nam-30221" },
  { id: 32542, category: "ports", name: "Tổng DWT tàu vào cảng biển Cảng vụ TP. Hồ Chí Minh", unit: "DWT", source: "Cục Hàng hải Việt Nam (các Cảng vụ Hàng hải)", url: "https://dulieukinhte.com/du-lieu-dong/tong-dwt-tau-vao-cang-bien-cang-vu-tp-ho-chi-minh-32542" },
  { id: 31248, category: "property", name: "Số dự án nhà ở thương mại được chấp thuận chủ trương đầu tư", unit: "Dự án", source: "Bộ Xây dựng", url: "https://dulieukinhte.com/du-lieu-dong/so-du-an-nha-o-thuong-mai-duoc-chap-thuan-chu-truong-dau-tu-31248" },
  { id: 34763, category: "labor", name: "Lao động có việc làm", unit: "Nghìn người", source: "Cục Thống kê (NSO)", url: "https://dulieukinhte.com/du-lieu-dong/lao-dong-co-viec-lam-34763" }
];
function fail(message) { console.error("ERROR:", message); process.exit(1); }
let response;
try { response = JSON.parse(fs.readFileSync("category-response.json", "utf8")); }
catch (error) { fail("Không đọc được phản hồi API: " + error.message); }
if (!response || !Array.isArray(response.data)) fail("API không trả về mảng data.");
const outputData = [];
for (const def of definitions) {
  const series = response.data.find(item => String(item.id) === String(def.id));
  if (!series || series.skipped || !Array.isArray(series.observations)) {
    fail("Thiếu chuỗi dữ liệu " + def.id + ". Không cập nhật snapshot để tránh ghi dữ liệu thiếu.");
  }
  const observations = series.observations
    .filter(item => item && item.date && item.value !== null && item.value !== undefined && Number.isFinite(Number(item.value)))
    .map(item => ({ date: String(item.date), value: Number(item.value) }))
    .sort((a, b) => a.date.localeCompare(b.date));
  if (!observations.length) fail("Không có quan sát hợp lệ cho " + def.id);
  const latest = observations[observations.length - 1];
  outputData.push({ ...def, value: latest.value, date: latest.date, unit: series.unit || def.unit, observations });
}
const output = { source: "DulieuKinhte API", fetchedAt: new Date().toISOString(), data: outputData };
const outputPath = path.join("data", "category-data.json");
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const tempPath = outputPath + ".tmp";
fs.writeFileSync(tempPath, JSON.stringify(output, null, 2) + "\n", "utf8");
fs.renameSync(tempPath, outputPath);
console.log("Đã lưu " + outputData.length + " chuỗi dữ liệu theo danh mục.");
for (const item of outputData) console.log(item.category + " | " + item.name + " | " + item.value + " " + item.unit + " | " + item.date);
