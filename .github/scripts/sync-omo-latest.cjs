const fs = require("node:fs");

function fail(message) {
  console.error("ERROR:", message);
  process.exit(1);
}

function readLatest(file, category, name, url) {
  let html;
  try {
    html = fs.readFileSync(file, "utf8");
  } catch (error) {
    fail("Không đọc được HTML nguồn " + file + ": " + error.message);
  }
  const text = html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;|&#xA0;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/\s+/g, " ");
  const match = text.match(/kỳ\s+(\d{2})-(\d{2})-(\d{4})\s+đạt\s+([\d.]+(?:,[\d]+)?)\s*Tỷ/i);
  if (!match) fail("Không tìm thấy kỳ dữ liệu và giá trị trong nguồn " + url + ". Không ghi snapshot.");
  const date = match[3] + "-" + match[2] + "-" + match[1];
  const value = Number(match[4].replace(/\./g, "").replace(",", "."));
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(value)) {
    fail("Ngày hoặc giá trị không hợp lệ từ " + url);
  }
  const observed = new Date(date + "T00:00:00Z");
  const today = new Date(new Date().toISOString().slice(0, 10) + "T00:00:00Z");
  if (observed > today) fail("Nguồn trả về ngày tương lai: " + date);
  return { category, name, value, unit: "Tỷ đồng", date, source: "Ngân hàng Nhà nước Việt Nam (NHNN), qua Dữ Liệu Kinh Tế", url };
}

const data = [
  readLatest("omo-buy.html", "omo-buy-total", "Tổng khối lượng trúng thầu mua (bơm tiền) nghiệp vụ thị trường mở OMO", "https://dulieukinhte.com/du-lieu-dong/tong-mua-bom-tien-nghiep-vu-thi-truong-mo-omo-27690"),
  readLatest("omo-outstanding.html", "omo-net-outstanding", "Chênh lệch lưu hành OMO và tín phiếu NHNN", "https://dulieukinhte.com/du-lieu-dong/chenh-lech-luu-hanh-omo-va-tin-phieu-nhnn-53631")
];
const output = { source: "Dữ Liệu Kinh Tế; nguồn chỉ tiêu: NHNN", fetchedAt: new Date().toISOString(), data };
fs.mkdirSync("data", { recursive: true });
const temp = "data/omo-latest.json.tmp";
fs.writeFileSync(temp, JSON.stringify(output, null, 2) + "\n", "utf8");
fs.renameSync(temp, "data/omo-latest.json");
console.log("OMO snapshot hợp lệ:");
for (const item of data) console.log(item.category + " | " + item.value + " " + item.unit + " | " + item.date);
