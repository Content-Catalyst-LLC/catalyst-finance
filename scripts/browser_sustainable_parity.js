'use strict';
const fs=require('fs');
const engine=require('../wordpress/catalyst-finance-demo/assets/catalyst-finance-sustainable-engine.js');
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
process.stdout.write(JSON.stringify(engine.evaluate(input,process.argv[3]||'2026-07-17T00:00:00+00:00')));
