import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync("assets/app.js", "utf8");
assert.ok(app.includes("const extractedCoreFields = new Set("));
assert.ok(app.includes("(extractedDetailFields.has(key) || extractedCoreFields.has(key))"));
assert.ok(app.includes("!rejectedDetailFields.has(key)"));
assert.ok(app.includes("investment_property_disposal_gain"));
assert.ok(app.includes("non_controlling_interest_profit"));

assert.ok(app.includes("key === 'non_controlling_interest_profit'"));
assert.ok(app.includes("/hợp nhất|consolidated/i.test(String(item.report_type || ''))"));
assert.ok(app.includes("nciCheck === 0 || rawNciMatches"));
assert.ok(app.includes("item.income_statement_source_raw_vnd?.nci_profit"));

const deriveNci = (netProfit, parentProfit, consolidated, sourceCheck, rawNciVnd) => {
  if (!consolidated || !Number.isFinite(netProfit) || !Number.isFinite(parentProfit)) return null;
  const difference = netProfit - parentProfit;
  const rawNciMillion = Number.isFinite(rawNciVnd) ? rawNciVnd / 1_000_000 : null;
  const rawMatches = rawNciMillion !== null &&
    Math.abs(difference - rawNciMillion) <= Math.max(0.000001, Math.abs(rawNciMillion) * 0.0001);
  return sourceCheck === 0 || rawMatches ? difference : null;
};
// IDC: source check or independently matching raw NCI line confirms the same-period bridge.
assert.equal(deriveNci(175208, 147786, true, 0, 27421352041), 27422);
assert.equal(deriveNci(574345, 511014, true, undefined, 63331304360), 63331);
assert.equal(deriveNci(415964, 297573, true, 0, 118390806095), 118391);
assert.equal(deriveNci(1001241, 880406, true, 0, 120834657407), 120835);
// Do not expose a residual where the source bridge/raw NCI has not been verified.
assert.equal(deriveNci(2052338.999441, 2044102.438055, true), null); // GAS no raw NCI/check for this quarter
assert.equal(deriveNci(612081, 254, true), null); // PLX has no independent NCI reconciliation
assert.equal(deriveNci(770051, 263, true), null); // KDH OCR parent-profit candidate is not reconciled
assert.equal(deriveNci(175208, 147786, false, 0), null);
assert.equal(deriveNci(null, 147786, true, 0), null);

const allowed = (key, detail, core, rejected) =>
  (detail.has(key) || core.has(key)) && !rejected.has(key);
const detail = new Set(["current_assets", "gross_profit"]);
const core = new Set(["total_assets", "net_profit_attributable", "eps"]);
const rejected = new Set(["gross_profit"]);

for (const field of ["current_assets", "total_assets", "net_profit_attributable", "eps"]) {
  assert.equal(allowed(field, detail, core, rejected), true, field);
}
for (const field of ["gross_profit", "cash_and_equivalents"]) {
  assert.equal(allowed(field, detail, core, rejected), false, field);
}

const grossProfitFromSource = (revenue, signedCogs) => revenue - signedCogs;
const revenueFromSource = (grossProfit, signedCogs) => grossProfit + signedCogs;

// Positive-expense and negative-deduction source conventions must both reconcile.
assert.equal(grossProfitFromSource(950374, 590717), 359657);
assert.equal(revenueFromSource(359657, 590717), 950374);
assert.equal(grossProfitFromSource(578664, -9920), 588584);
assert.equal(revenueFromSource(588584, -9920), 578664);
assert.ok(app.includes("num('revenue') - num('cost_of_goods_sold')"));
assert.ok(app.includes("num('gross_profit') + num('cost_of_goods_sold')"));

console.log("Financial table source allow-list and signed-COGS regression checks passed.");
