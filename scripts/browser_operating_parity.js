'use strict';
const fs = require('fs');
const engine = require('../wordpress/catalyst-finance-demo/assets/catalyst-finance-operating-engine.js');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const result = engine.evaluate(input, process.argv[3] || '2026-07-17T00:00:00+00:00');
process.stdout.write(JSON.stringify(result));
