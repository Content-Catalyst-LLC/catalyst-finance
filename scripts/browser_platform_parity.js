const fs=require('fs');
const engine=require('../wordpress/catalyst-finance-demo/assets/catalyst-finance-platform-engine.js');
const definition=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
process.stdout.write(JSON.stringify(engine.evaluate(definition,process.argv[3])));
