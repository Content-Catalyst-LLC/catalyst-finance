#!/usr/bin/env node
const fs=require('fs');
global.CatalystFinanceCashFlowEngine=require('../wordpress/catalyst-finance-demo/assets/catalyst-finance-cashflow-engine.js');
const engine=require('../wordpress/catalyst-finance-demo/assets/catalyst-finance-comparison-engine.js');
const definition=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
process.stdout.write(JSON.stringify(engine.evaluate(definition,process.argv[3])));
