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
const expectedPeriods = [];
for (let year = 2024; year <= 2026; year++) {
  const maxQuarter = year === 2026 ? 2 : 4;
  for (let quarter = 1; quarter <= maxQuarter; quarter++) expectedPeriods.push(`${year}-Q${quarter}`);
}
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

    for (const field of ["total_assets", "total_liabilities", "equity", "pretax_profit", "net_profit"]) {
      if (typeof item[field] !== "number" || !Number.isFinite(item[field])) {
        errors.push(`${symbol} ${item.period}: ${field} is missing or non-numeric`);
      }
    }
    if (!item.source_url || !/^https:\/\//i.test(item.source_url)) {
      errors.push(`${symbol} ${item.period}: source_url missing or not HTTPS`);
    }
    if (!item.source_index_url || !item.source_index_url.startsWith("https://finance.vietstock.vn/")) {
      errors.push(`${symbol} ${item.period}: VietstockFinance source_index_url missing`);
    }
    if (!item.unit) errors.push(`${symbol} ${item.period}: unit missing`);

    if ([item.total_assets, item.total_liabilities, item.equity].every(Number.isFinite)) {
      const delta = item.total_assets - item.total_liabilities - item.equity;
      if (Math.abs(delta) > 3) errors.push(`${symbol} ${item.period}: balance equation differs by ${delta} (${item.unit || "unit"})`);
    }
    if (status.includes("pending_visual_review") || status.startsWith("ocr_") || status === "missing_status") {
      warnings.push(`${symbol} ${item.period}: requires/should retain review status (${status})`);
    }
  }

  for (const period of expectedPeriods) {
    if (!byPeriod.has(period)) errors.push(`${symbol}: missing period ${period}`);
  }
  for (const period of byPeriod.keys()) {
    if (!expectedPeriods.includes(period)) warnings.push(`${symbol}: unexpected period ${period}`);
  }
  if (snapshot.items.length !== expectedPeriods.length) {
    errors.push(`${symbol}: expected ${expectedPeriods.length} periods, found ${snapshot.items.length}`);
  }

  summary.push({ symbol, periods: snapshot.items.length, statuses: statusCounts });
}

console.log("VietstockFinance quarterly snapshot validation");
console.log(`Symbols checked: ${summary.length}/${symbols.length}`);
console.log(`Expected periods per symbol: ${expectedPeriods[0]} through ${expectedPeriods.at(-1)} (${expectedPeriods.length})`);
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
