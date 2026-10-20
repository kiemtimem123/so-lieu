#!/usr/bin/env node
/**
 * Validate quarterly financial snapshots sourced from VietstockFinance.
 * This checks data integrity and provenance metadata; it does not claim that
 * every extracted value has passed manual visual review against its PDF.
 */
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const symbols = ["MBB", "ACB", "FPT", "SHB", "TCX", "HCM", "VND", "SHS", "NLG", "BSR", "TCB", "VHM"];
const firstExpectedOrdinal = 2024 * 4 + 1;
const periodOrdinal = period => {
  const match = /^(20\d{2})-Q([1-4])$/.exec(String(period || ""));
  return match ? Number(match[1]) * 4 + Number(match[2]) : null;
};
const periodFromOrdinal = ordinal => `${Math.floor((ordinal - 1) / 4)}-Q${((ordinal - 1) % 4) + 1}`;
const periodsBetween = endOrdinal => {
  const periods = [];
  for (let ordinal = firstExpectedOrdinal; ordinal <= endOrdinal; ordinal++) periods.push(periodFromOrdinal(ordinal));
  return periods;
};
const errors = [];
const warnings = [];
const summary = [];

for (const symbol of symbols) {
  const file = path.join(root, "data", `financials-${symbol}.json`);
  if (!fs.existsSync(file)) {
    errors.push(`${symbol}: missing ${path.relative(root, file)}`);
    continue;
  }

  let snapshot;
  try {
    snapshot = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    errors.push(`${symbol}: invalid JSON (${error.message})`);
    continue;
  }

  if (snapshot.symbol !== symbol) errors.push(`${symbol}: top-level symbol mismatch`);
  if (!Array.isArray(snapshot.items)) {
    errors.push(`${symbol}: items must be an array`);
    continue;
  }

  const byPeriod = new Map();
  const statusCounts = {};
  for (const item of snapshot.items) {
    if (!item || typeof item !== "object") {
      errors.push(`${symbol}: non-object item found`);
      continue;
    }
    if (byPeriod.has(item.period)) errors.push(`${symbol}: duplicate period ${item.period}`);
    byPeriod.set(item.period, item);
    const status = item.verification_status || "missing_status";
    statusCounts[status] = (statusCounts[status] || 0) + 1;

    const pendingExtraction = status === "auto_pending_extraction";
    for (const field of ["total_assets", "total_liabilities", "equity", "pretax_profit", "net_profit"]) {
      if ((typeof item[field] !== "number" || !Number.isFinite(item[field])) && !pendingExtraction) {
        errors.push(`${symbol} ${item.period}: ${field} is missing or non-numeric`);
      }
    }
    if (pendingExtraction) {
      warnings.push(`${symbol} ${item.period}: new VietstockFinance report detected; financial fields await reliable extraction`);
    }
    let sourceHost = "";
    try {
      sourceHost = new URL(item.source_url || "").hostname;
    } catch {}
    if (!(sourceHost === "vietstock.vn" || sourceHost.endsWith(".vietstock.vn"))) {
      errors.push(`${symbol} ${item.period}: report must link to a Vietstock-owned host; got ${item.source_url || "no URL"}`);
    }
    const expectedIndex = `https://finance.vietstock.vn/${symbol}/tai-tai-lieu.htm?doctype=1`;
    if (item.source_index_url !== expectedIndex) {
      errors.push(`${symbol} ${item.period}: source_index_url must be the VietstockFinance document catalog ${expectedIndex}`);
    }
    if (!String(item.report_type || "").toLocaleLowerCase("vi").includes("bctc")) {
      errors.push(`${symbol} ${item.period}: report_type should identify a financial statement (BCTC), not a research report`);
    }
    if (!item.unit) errors.push(`${symbol} ${item.period}: unit missing`);

    if ([item.total_assets, item.total_liabilities, item.equity].every(Number.isFinite)) {
      const delta = item.total_assets - item.total_liabilities - item.equity;
      if (Math.abs(delta) > 3) errors.push(`${symbol} ${item.period}: balance equation differs by ${delta} (${item.unit || "unit"})`);
    }
    if (status.includes("pending_visual_review") || status === "auto_extracted_pending_visual_review" ||
        status.startsWith("ocr_") || status === "missing_status") {
      warnings.push(`${symbol} ${item.period}: requires/should retain review status (${status})`);
    }
  }

  const ordinals = [...byPeriod.keys()].map(periodOrdinal).filter(Number.isFinite);
  const latestOrdinal = ordinals.length ? Math.max(...ordinals) : firstExpectedOrdinal - 1;
  const expectedPeriods = periodsBetween(latestOrdinal);
  for (const period of expectedPeriods) {
    if (!byPeriod.has(period)) errors.push(`${symbol}: missing period ${period} before latest stored period`);
  }
  for (const period of byPeriod.keys()) {
    const ordinal = periodOrdinal(period);
    if (ordinal === null || ordinal < firstExpectedOrdinal) {
      warnings.push(`${symbol}: unexpected or pre-2024 period ${period}`);
    }
  }

  summary.push({
    symbol,
    periods: snapshot.items.length,
    first: snapshot.items[0]?.period || null,
    last: snapshot.items.at(-1)?.period || null,
    statuses: statusCounts
  });
}

console.log("VietstockFinance quarterly snapshot validation");
console.log(`Symbols checked: ${summary.length}/${symbols.length}`);
console.log("Expected coverage per symbol: contiguous periods from 2024-Q1 through that symbol's latest stored quarter.");
console.log(`Errors: ${errors.length}; review warnings: ${warnings.length}`);
for (const row of summary) console.log(`- ${row.symbol}: ${row.periods} periods; status counts ${JSON.stringify(row.statuses)}`);
if (warnings.length) {
  console.log("\nReview warnings (not automatic failures):");
  for (const warning of warnings) console.log(`WARN ${warning}`);
}
if (errors.length) {
  console.error("\nValidation errors:");
  for (const error of errors) console.error(`ERROR ${error}`);
  process.exitCode = 1;
} else {
  console.log("\nPASS: period coverage, required fields, source metadata, and balance equations passed.");
}
