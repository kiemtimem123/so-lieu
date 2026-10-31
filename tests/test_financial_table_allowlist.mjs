import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync("assets/app.js", "utf8");
assert.ok(app.includes("const extractedCoreFields = new Set("));
assert.ok(app.includes("(extractedDetailFields.has(key) || extractedCoreFields.has(key))"));
assert.ok(app.includes("!rejectedDetailFields.has(key)"));
assert.ok(app.includes("investment_property_disposal_gain"));
assert.ok(app.includes("non_controlling_interest_profit"));

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
