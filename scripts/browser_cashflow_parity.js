'use strict';
const fs = require('fs');
const path = require('path');
const engine = require(path.resolve(__dirname, '../wordpress/catalyst-finance-demo/assets/catalyst-finance-cashflow-engine.js'));
if (process.argv.length < 4) {
  console.error('Usage: node scripts/browser_cashflow_parity.js INPUT GENERATED_AT');
  process.exit(2);
}
const payload = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
process.stdout.write(JSON.stringify(engine.evaluate(payload, process.argv[3])) + '\n');
