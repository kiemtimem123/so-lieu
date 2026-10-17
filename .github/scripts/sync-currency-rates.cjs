const fs = require("node:fs");
const path = require("node:path");

function fail(message) {
  console.error("ERROR:", message);
  process.exit(1);
}

let response;
try {
  response = JSON.parse(fs.readFileSync("currency-response.json", "utf8"));
} catch (error) {
  fail("Không đọc được phản hồi tỷ giá: " + error.message);
}

if (!response || response.result !== "success" || response.base_code !== "USD" ||
    !response.rates || !Number.isFinite(Number(response.rates.VND)) ||
    !response.time_last_update_utc) {
  fail("Phản hồi tỷ giá không hợp lệ hoặc thiếu USD/VND; không ghi đè snapshot.");
}

const names = {
  USD: "Đô la Mỹ",
  EUR: "Euro",
  GBP: "Bảng Anh",
  JPY: "Yên Nhật",
  CNY: "Nhân dân tệ",
  AUD: "Đô la Úc",
  CAD: "Đô la Canada",
  SGD: "Đô la Singapore",
  THB: "Baht Thái",
  KRW: "Won Hàn Quốc",
  CHF: "Franc Thụy Sĩ",
  HKD: "Đô la Hồng Kông",
  NZD: "Đô la New Zealand",
  INR: "Rupee Ấn Độ",
  IDR: "Rupiah Indonesia",
  MYR: "Ringgit Malaysia",
  PHP: "Peso Philippines",
  TWD: "Đô la Đài Loan mới",
  AED: "Dirham UAE",
  SAR: "Riyal Ả Rập Xê Út",
  SEK: "Krona Thụy Điển",
  NOK: "Krone Na Uy",
  DKK: "Krone Đan Mạch",
  ZAR: "Rand Nam Phi",
  MXN: "Peso Mexico",
  BRL: "Real Brazil"
};
const codes = Object.keys(names);
const usdVnd = Number(response.rates.VND);
const data = codes.map(code => {
  const perUsd = Number(response.rates[code]);
  if (!Number.isFinite(perUsd) || perUsd <= 0) fail("Thiếu tỷ giá hợp lệ cho " + code);
  return {
    code,
    name: names[code],
    vndPerUnit: Number((usdVnd / perUsd).toFixed(code === "KRW" || code === "JPY" ? 4 : 2)),
    method: code === "USD" ? "direct" : "calculated_cross_rate"
  };
});

const output = {
  source: "ExchangeRate-API Open Access (open.er-api.com)",
  sourceUrl: "https://open.er-api.com/v6/latest/USD",
  rateType: "Tỷ giá tham khảo thị trường; không phải tỷ giá mua/bán ngân hàng hoặc tỷ giá trung tâm NHNN",
  base: "USD",
  lastUpdatedUtc: response.time_last_update_utc,
  fetchedAt: new Date().toISOString(),
  data
};

const outputPath = path.join("data", "currency-rates.json");
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const tempPath = outputPath + ".tmp";
fs.writeFileSync(tempPath, JSON.stringify(output, null, 2) + "\n", "utf8");
fs.renameSync(tempPath, outputPath);
console.log("Đã lưu " + data.length + " tỷ giá tham khảo vào " + outputPath);
