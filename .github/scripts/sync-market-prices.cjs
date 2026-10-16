const fs = require("node:fs");
const path = require("node:path");

const responsePath = "response.json";
const outputPath = path.join("data", "market-prices.json");

const labels = {
  "37826": "WTI",
  "37827": "Brent",
  "37694": "Xăng thường tại Mỹ",
  "37828": "Dầu diesel tại Mỹ",
  "37695": "Khí tự nhiên Henry Hub"
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
    date: latest.date
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

console.log("Đã lưu đủ 5 chuỗi dữ liệu vào " + outputPath);
for (const item of data) {
  console.log(item.name + " | " + item.value + " " + (item.unit || "") + " | " + item.date);
}
