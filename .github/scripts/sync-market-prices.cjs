const fs = require("node:fs");
const path = require("node:path");

const responsePath = "response.json";
const outputPath = path.join("data", "market-prices.json");

const labels = {
  "37826": "WTI",
  "37827": "Brent",
  "37694": "Xăng thường tại Mỹ",
  "37828": "Dầu diesel tại Mỹ",
  "37695": "Khí tự nhiên Henry Hub",
  "29387": "Bạc thế giới",
  "29388": "Đồng thế giới",
  "29380": "Thép thanh thế giới",
  "29406": "Giá gạo thế giới",
  "66457": "Cao su TSR20 thế giới",
  "33392": "Giá xuất khẩu bình quân cao su",
  "33408": "Giá nhập khẩu bình quân cao su",
  "33414": "Giá nhập khẩu bình quân kim loại thường khác"
};

const sources = {
  "37826": { name: "Dữ Liệu Kinh Tế · chuỗi giá WTI" },
  "37827": { name: "Dữ Liệu Kinh Tế · chuỗi giá Brent" },
  "37694": { name: "Dữ Liệu Kinh Tế · giá xăng bán lẻ tại Mỹ" },
  "37828": { name: "Dữ Liệu Kinh Tế · giá diesel tại Mỹ" },
  "37695": { name: "Dữ Liệu Kinh Tế · Henry Hub" },
  "29387": { name: "Dữ Liệu Kinh Tế · bạc thế giới" },
  "29388": { name: "Dữ Liệu Kinh Tế · đồng thế giới" },
  "29380": { name: "Dữ Liệu Kinh Tế · thép thanh thế giới", url: "https://dulieukinhte.com/du-lieu-dong/gia-thep-thanh-the-gioi-29380" },
  "29406": { name: "Dữ Liệu Kinh Tế · giá gạo thế giới", url: "https://dulieukinhte.com/du-lieu-dong/gia-gao-the-gioi-29406" },
  "66457": { name: "Dữ Liệu Kinh Tế · cao su TSR20 thế giới", url: "https://dulieukinhte.com/du-lieu-dong/gia-cao-su-tsr20-ine-the-gioi-66457" },
  "33392": { name: "Tổng cục Hải quan · qua Dữ Liệu Kinh Tế", url: "https://dulieukinhte.com/du-lieu-dong/gia-xuat-khau-binh-quan-cao-su-33392" },
  "33408": { name: "Tổng cục Hải quan · qua Dữ Liệu Kinh Tế", url: "https://dulieukinhte.com/du-lieu-dong/gia-nhap-khau-binh-quan-cao-su-33408" },
  "33414": { name: "Dữ Liệu Kinh Tế · giá nhập khẩu kim loại thường khác" }
};

const groups = {
  "37826":"energy","37827":"energy","37694":"energy","37828":"energy","37695":"energy",
  "29387":"metals","29388":"metals","29380":"metals","33414":"metals",
  "29406":"agriculture","66457":"agriculture","33392":"agriculture","33408":"agriculture"
};

function fail(message) {
  console.error("ERROR:", message);
  process.exit(1);
}

let response;
try {
  response = JSON.parse(fs.readFileSync(responsePath, "utf8"));
} catch (error) {
  fail("Không đọc được JSON từ API: " + error.message);
}

if (!response || typeof response !== "object" || response.error) {
  const apiError = response && response.error;
  fail(apiError
    ? String(apiError.code || "API error") + " | " + String(apiError.message || "Không có thông báo")
    : "Phản hồi API không hợp lệ.");
}

if (!Array.isArray(response.data)) {
  fail("Phản hồi API không có mảng data.");
}

const ids = Object.keys(labels);
const data = [];

for (const id of ids) {
  const series = response.data.find(item => String(item.id) === id);

  if (!series || series.skipped) {
    fail("Thiếu chuỗi dữ liệu hoặc chuỗi bị bỏ qua: " + id);
  }

  if (!Array.isArray(series.observations) || series.observations.length === 0) {
    fail("Không có quan sát cho chuỗi: " + id);
  }

  const valid = series.observations
    .filter(item => item && item.date && item.value !== null && item.value !== undefined)
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));

  const latest = valid[valid.length - 1];
  if (!latest) {
    fail("Không tìm thấy giá trị hợp lệ cho chuỗi: " + id);
  }

  data.push({
    id: Number(id),
    name: labels[id],
    value: latest.value,
    unit: series.unit || null,
    group: groups[id] || "other",
    date: latest.date,
    observations: valid.map(point => ({ date: point.date, value: point.value })),\n    source: sources[id]?.name || "Dữ Liệu Kinh Tế API",\n    ...(sources[id]?.url ? { sourceUrl: sources[id].url } : {})
  });
}

if (data.length !== ids.length) {
  fail("Số chuỗi dữ liệu không đủ; không ghi đè dữ liệu hiện tại.");
}

const output = {
  source: "DulieuKinhte API",
  fetchedAt: new Date().toISOString(),
  data
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const tempPath = outputPath + ".tmp";
fs.writeFileSync(tempPath, JSON.stringify(output, null, 2) + "\n", "utf8");
fs.renameSync(tempPath, outputPath);

console.log("Đã lưu đủ " + data.length + " chuỗi dữ liệu vào " + outputPath);
for (const item of data) {
  console.log(item.name + " | " + item.value + " " + (item.unit || "") + " | " + item.date);
}
