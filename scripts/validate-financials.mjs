#!/usr/bin/env node
/**
 * Validate quarterly financial snapshots sourced from VietstockFinance.
 * This checks data integrity and provenance metadata; it does not claim that
 * every extracted value has passed manual visual review against its PDF.
 */
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const configFile = path.join(root, "config", "securities.json");
let symbols = ["MBB", "ACB", "FPT", "SHB", "TCX", "HCM", "VND", "SHS", "NLG", "BSR", "TCB", "VHM"];
let defaultStartPeriod = "2024-Q1";
const startPeriodBySymbol = new Map();
try {
  const configuration = JSON.parse(fs.readFileSync(configFile, "utf8"));
  const configuredDefaultYear = Number(configuration.defaultStartYear || 2024);
  if (Number.isInteger(configuredDefaultYear) && configuredDefaultYear >= 2000 && configuredDefaultYear <= 2100) {
    defaultStartPeriod = `${configuredDefaultYear}-Q1`;
  }
  const configured = Array.isArray(configuration.securities)
    ? configuration.securities
        .filter(item => item && item.enabled !== false && item.symbol)
        .map(item => {
          const symbol = String(item.symbol).trim().toUpperCase();
          const configuredStart = /^(20\d{2}-Q[1-4])$/.exec(String(item.startPeriod || "").trim().toUpperCase());
          startPeriodBySymbol.set(symbol, configuredStart ? configuredStart[1] : defaultStartPeriod);
          return symbol;
        })
    : [];
  if (configured.length) symbols = [...new Set(configured)];
} catch (error) {
  console.warn(`Could not read config/securities.json; validating the legacy symbol list (${error.message}).`);
}
const periodOrdinal = period => {
  const match = /^(20\d{2})-Q([1-4])$/.exec(String(period || ""));
  return match ? Number(match[1]) * 4 + Number(match[2]) : null;
};
const periodFromOrdinal = ordinal => `${Math.floor((ordinal - 1) / 4)}-Q${((ordinal - 1) % 4) + 1}`;
const periodsBetween = (startOrdinal, endOrdinal, firstExpectedOrdinal) => {
  const periods = [];
  for (let ordinal = Math.max(firstExpectedOrdinal, startOrdinal); ordinal <= endOrdinal; ordinal++) {
    periods.push(periodFromOrdinal(ordinal));
  }
  return periods;
};
const errors = [];
const warnings = [];
const summary = [];

for (const symbol of symbols) {
  const file = path.join(root, "data", `financials-${symbol}.json`);
  if (!fs.existsSync(file)) {
    warnings.push(`${symbol}: snapshot not created yet; the VietstockFinance bootstrap workflow must create it.`);
    summary.push({ symbol, periods: 0, first: null, last: null, statuses: {}, state: "not_bootstrapped" });
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

  if (snapshot.items.length === 0) {
    warnings.push(`${symbol}: no quarterly reports have been added to this snapshot yet.`);
    summary.push({ symbol, periods: 0, first: null, last: null, statuses: {}, state: "awaiting_reports" });
    continue;
  }

  const symbolStartPeriod = startPeriodBySymbol.get(symbol) || defaultStartPeriod;
  const firstExpectedOrdinal = periodOrdinal(symbolStartPeriod) || periodOrdinal(defaultStartPeriod);
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

    const pendingExtraction = status === "auto_pending_extraction" || status === "manual_review_required_pending_extraction" || status === "auto_extracted_pending_visual_review" || status === "ocr_pending_visual_review";
    // A quarter may have a separately published correction/quarterly income
    // statement while the linked full consolidated report is still unavailable.
    // Permit only the three balance-sheet fields to remain blank in that
    // explicitly documented state; never infer or fabricate those values.
    let pendingBalanceSheet = item.balance_sheet_extraction_status === "pending_full_report_archive_and_extraction";
    try {
      const balanceSourceHost = new URL(item.balance_sheet_source_url || "").hostname;
      pendingBalanceSheet = pendingBalanceSheet &&
        (balanceSourceHost === "vietstock.vn" || balanceSourceHost.endsWith(".vietstock.vn"));
    } catch {
      pendingBalanceSheet = false;
    }
    // Do not fail validation when a quarterly profit figure is intentionally
    // withheld because OCR cannot distinguish standalone-quarter from YTD columns.
    // The item must explicitly document the ambiguity and the missing values.
    const profitBasisAmbiguous =
      item.quarter_profit_extraction_status === "ambiguous_quarter_vs_ytd" &&
      Boolean(String(item.quarter_profit_extraction_note || "").trim());
    for (const field of ["total_assets", "total_liabilities", "equity", "pretax_profit", "net_profit"]) {
      const balanceFieldPending = pendingBalanceSheet && ["total_assets", "total_liabilities", "equity"].includes(field);
      const documentedProfitBlank = profitBasisAmbiguous && ["pretax_profit", "net_profit"].includes(field) &&
        (item[field] === null || item[field] === undefined || item[field] === "");
      if ((typeof item[field] !== "number" || !Number.isFinite(item[field])) &&
          !pendingExtraction && !balanceFieldPending && !documentedProfitBlank) {
        errors.push(`${symbol} ${item.period}: ${field} is missing or non-numeric`);
      }
    }
    if (profitBasisAmbiguous) {
      warnings.push(`${symbol} ${item.period}: quarterly profit withheld because OCR cannot reliably separate quarterly and YTD columns`);
    }
    if (pendingBalanceSheet) {
      warnings.push(`${symbol} ${item.period}: balance-sheet fields remain blank pending extraction of the linked full Vietstock report`);
    }
    if (status === "auto_pending_extraction") {
      warnings.push(`${symbol} ${item.period}: new VietstockFinance report detected; financial fields await reliable extraction`);
    } else if (status === "manual_review_required_pending_extraction") {
      warnings.push(`${symbol} ${item.period}: automatic extraction limit reached; PDF review is required and missing fields remain blank`);
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
  const earliestOrdinal = ordinals.length ? Math.min(...ordinals) : firstExpectedOrdinal;
  const latestOrdinal = ordinals.length ? Math.max(...ordinals) : firstExpectedOrdinal - 1;
  const expectedPeriods = periodsBetween(earliestOrdinal, latestOrdinal, firstExpectedOrdinal);
  if (ordinals.length && earliestOrdinal > firstExpectedOrdinal) {
    warnings.push(`${symbol}: first stored report is ${periodFromOrdinal(earliestOrdinal)}; this is later than its configured start period ${symbolStartPeriod}.`);
  }
  for (const period of expectedPeriods) {
    if (!byPeriod.has(period)) errors.push(`${symbol}: missing period ${period} within the stored reporting span`);
  }
  for (const period of byPeriod.keys()) {
    const ordinal = periodOrdinal(period);
    if (ordinal === null || ordinal < firstExpectedOrdinal) {
      warnings.push(`${symbol}: unexpected or pre-2024 period ${period}`);
    }
  }

  const sortedPeriods = [...byPeriod.keys()].sort();
  summary.push({
    symbol,
    periods: snapshot.items.length,
    first: sortedPeriods[0] || null,
    last: sortedPeriods.at(-1) || null,
    statuses: statusCounts,
    detailQuarters: snapshot.items.filter(item => item.financial_line_items_status).length
  });
}

console.log("VietstockFinance quarterly snapshot validation");
console.log(`Symbols checked: ${summary.length}/${symbols.length}`);
console.log("Expected coverage per symbol: contiguous periods from 2024-Q1 through that symbol's latest stored quarter.");
console.log(`Errors: ${errors.length}; review warnings: ${warnings.length}`);
for (const row of summary) console.log(`- ${row.symbol}: ${row.periods} periods; detail-enriched quarters ${row.detailQuarters ?? 0}; state ${row.state || "active"}; status counts ${JSON.stringify(row.statuses)}`);
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
