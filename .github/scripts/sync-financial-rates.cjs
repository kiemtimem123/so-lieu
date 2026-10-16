const fs = require("node:fs");
const path = require("node:path");

const responsePath = "response.json";
const outputPath = path.join("data", "financial-rates.json");

const labels = {
  "36708": { name: "Lợi suất TPCP kỳ hạn 1 năm", category: "bond", unit: "%/năm", source: "HNX" },
  "36711": { name: "Lợi suất TPCP kỳ hạn 2 năm", category: "bond", unit: "%/năm", source: "HNX" },
  "36714": { name: "Lợi suất TPCP kỳ hạn 10 năm", category: "bond", unit: "%/năm", source: "HNX" },
  "36710": { name: "Lợi suất TPCP kỳ hạn 20 năm", category: "bond", unit: "%/năm", source: "HNX" },
  "34248": { name: "Lãi suất liên ngân hàng qua đêm", category: "interest", unit: "%/năm", source: "NHNN" },
  "34249": { name: "Lãi suất liên ngân hàng 1 tuần", category: "interest", unit: "%/năm", source: "NHNN" },
  "34251": { name: "Lãi suất liên ngân hàng 1 tháng", category: "interest", unit: "%/năm", source: "NHNN" }
};

function fail(message) {
  console.error("ERROR:", message);
  process.exit(1);
}

let response;
try {
  response = JSON.parse(fs.readFileSync(responsePath, "utf8"));
} catch (error) {
  fail("Không đọc được phản hồi API: " + error.message);
}
if (!response || !Array.isArray(response.data)) fail("Phản hồi API không có mảng data.");

const data = [];
for (const [id, meta] of Object.entries(labels)) {
  const series = response.data.find(item => String(item.id) === id);
  if (!series || series.skipped || !Array.isArray(series.observations)) {
    fail("Thiếu chuỗi dữ liệu tài chính: " + id);
  }
  const observations = series.observations
    .filter(item => item && item.date && item.value !== null && item.value !== undefined && Number.isFinite(Number(item.value)))
    .map(item => ({ date: String(item.date), value: Number(item.value) }))
    .sort((a, b) => a.date.localeCompare(b.date));
  const latest = observations[observations.length - 1];
  if (!latest) fail("Không có quan sát hợp lệ cho chuỗi: " + id);
  data.push({
    id: Number(id),
    ...meta,
    value: latest.value,
    date: latest.date,
    observations
  });
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
console.log("Đã lưu " + data.length + " chuỗi lãi suất và lợi suất vào " + outputPath);
for (const item of data) console.log(item.name + " | " + item.value + " " + item.unit + " | " + item.date);
