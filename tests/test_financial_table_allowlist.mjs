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
assert.ok(app.includes("num('net_profit') - num('net_profit_attributable')"));

const deriveNci = (netProfit, parentProfit, consolidated) =>
  consolidated && Number.isFinite(netProfit) && Number.isFinite(parentProfit)
    ? netProfit - parentProfit
    : null;
// IDC source-backed NCI rows, using same-period consolidated figures.
assert.equal(deriveNci(175208, 147786, true), 27422);
assert.equal(deriveNci(574345, 511014, true), 63331);
assert.equal(deriveNci(415964, 297573, true), 118391);
assert.equal(deriveNci(1001241, 880406, true), 120835);
// GAS source rows where no separate top-level/alias NCI value is present.
assert.ok(Math.abs(deriveNci(2052338.999441, 2044102.438055, true) - 8236.561386) < 1e-9);
assert.equal(deriveNci(2543605, 2511656, true), 31949);
assert.equal(deriveNci(3416067, 3320817, true), 95250);
assert.equal(deriveNci(175208, 147786, false), null);
assert.equal(deriveNci(null, 147786, true), null);

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
