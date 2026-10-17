const fs = require('node:fs');
const securities = JSON.parse(fs.readFileSync('config/securities.json', 'utf8'));
const queue = JSON.parse(fs.readFileSync('config/report-queue.json', 'utf8'));
if (!Array.isArray(securities.securities)) throw new Error('config/securities.json: securities must be an array');
if (!Array.isArray(queue.jobs)) throw new Error('config/report-queue.json: jobs must be an array');
const allowed = new Set(['queued','searching','downloaded','extracting','verifying','approved','needs_review','failed']);
const seen = new Set();
for (const item of securities.securities) {
  if (!/^[A-Z0-9]{3,10}$/.test(item.symbol || '')) throw new Error('Invalid security symbol: ' + item.symbol);
  if (seen.has(item.symbol)) throw new Error('Duplicate security symbol: ' + item.symbol);
  seen.add(item.symbol);
}
const ids = new Set();
for (const job of queue.jobs) {
  if (!job.id || ids.has(job.id)) throw new Error('Missing or duplicate queue job id');
  ids.add(job.id);
  if (!/^[A-Z0-9]{3,10}$/.test(job.symbol || '')) throw new Error('Invalid job symbol: ' + job.symbol);
  if (!allowed.has(job.status)) throw new Error('Invalid status for ' + job.id + ': ' + job.status);
  if (!Number.isInteger(job.startYear) || job.startYear < 2000 || job.startYear > 2100) throw new Error('Invalid startYear for ' + job.id);
  if (!['consolidated','separate','both'].includes(job.reportType)) throw new Error('Invalid reportType for ' + job.id);
}
console.log('Queue validation passed: securities=' + securities.securities.length + ', jobs=' + queue.jobs.length);
