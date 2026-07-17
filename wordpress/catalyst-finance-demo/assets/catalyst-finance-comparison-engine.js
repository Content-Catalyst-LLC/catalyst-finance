(function (root, factory) {
  const dependency = typeof module === 'object' && module.exports
    ? require('./catalyst-finance-cashflow-engine.js')
    : root.CatalystFinanceCashFlowEngine;
  const engine = factory(dependency);
  if (typeof module === 'object' && module.exports) module.exports = engine;
  else root.CatalystFinanceComparisonEngine = engine;
})(typeof self !== 'undefined' ? self : this, function (cashFlowEngine) {
  'use strict';
  const CONTRACT_VERSION = '1.9.0';
  const MODEL_ID = 'catalyst-finance.comparison';
  const LABELS = {
    npv: 'Net present value', net_cash_flow: 'Net cash flow',
    discounted_payback_periods: 'Discounted payback', irr_percent_annual: 'Internal rate of return',
    mirr_percent_annual: 'Modified internal rate of return', profitability_index: 'Profitability index',
    benefit_cost_ratio: 'Benefit-cost ratio', equivalent_annual_value: 'Equivalent annual value'
  };
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function metric(publication, id) { const value = publication.metrics[id]; return value === undefined ? null : value; }
  function parameterValue(scenario, parameter) {
    if (parameter.operation === 'multiply') return 1;
    if (parameter.operation === 'shift_periods') return 0;
    if (Object.prototype.hasOwnProperty.call(scenario, parameter.path)) return Number(scenario[parameter.path]);
    const parts = parameter.path.split(':');
    if (parts.length === 3 && parts[0] === 'line') {
      const line = scenario.lines.find(item => item.flow_id === parts[1]);
      return line && line[parts[2]] !== null && line[parts[2]] !== undefined ? Number(line[parts[2]]) : null;
    }
    return null;
  }
  function applyParameter(scenario, parameter, rawValue) {
    const payload = clone(scenario); let value = Number(rawValue);
    if (parameter.value_kind === 'integer') value = Math.round(value);
    if (['analysis_horizon_periods','discount_rate_percent_annual','finance_rate_percent_annual','reinvestment_rate_percent_annual'].includes(parameter.path)) {
      payload[parameter.path] = parameter.path === 'analysis_horizon_periods' ? Math.round(value) : value;
      return payload;
    }
    const parts = parameter.path.split(':');
    if (parameter.operation === 'shift_periods') {
      payload.lines.forEach(line => {
        if (line.start_period === 0 || ['residual_value','decommissioning_cost','working_capital_recovery'].includes(line.category)) return;
        line.start_period = Math.min(payload.analysis_horizon_periods, Math.max(0, line.start_period + Math.round(value)));
        if (line.end_period !== null && line.end_period !== undefined) line.end_period = Math.min(payload.analysis_horizon_periods, Math.max(line.start_period, line.end_period + Math.round(value)));
      });
      return payload;
    }
    let matched = false;
    payload.lines.forEach(line => {
      if (parts.length === 3 && parts[0] === 'line' && line.flow_id === parts[1]) {
        const field = parts[2]; line[field] = parameter.operation === 'multiply' ? Number(line[field]) * value : value; matched = true;
      } else if (parts.length === 3 && parts[0] === 'category' && line.category === parts[1] && parts[2] === 'amount') {
        line.amount = parameter.operation === 'multiply' ? Number(line.amount) * value : value; matched = true;
      }
    });
    if (!matched) throw new Error('Sensitivity path did not match: ' + parameter.path);
    return payload;
  }
  function evaluateMetric(scenario, parameter, value, metricId) { return metric(cashFlowEngine.evaluate(applyParameter(scenario, parameter, value)), metricId); }
  function ranks(values, objective) {
    const valid = values.filter(item => item.value !== null).slice().sort((a,b) => objective === 'maximize' ? b.value-a.value : a.value-b.value);
    const out = {}; values.forEach(item => { out[item.id] = null; }); let previous = null; let previousRank = 0;
    valid.forEach((item,index) => { const rank = previous === item.value ? previousRank : index+1; out[item.id]=rank; previous=item.value; previousRank=rank; }); return out;
  }
  function dominance(left, right, selections) {
    let strict=false;
    for (const selection of selections) {
      const l=left.metrics[selection.metric_id], r=right.metrics[selection.metric_id]; if (l===null || r===null) return false;
      if (selection.objective==='maximize') { if (l<r) return false; if (l>r) strict=true; }
      else { if (l>r) return false; if (l<r) strict=true; }
    }
    return strict;
  }
  function aligned(evaluations, definition) {
    const baseline=evaluations.find(item=>item.alternative_id===definition.baseline_alternative_id);
    return definition.selected_metrics.map(selection=>{
      const values=evaluations.map(item=>({id:item.alternative_id,value:item.metrics[selection.metric_id]})); const rankMap=ranks(values,selection.objective); const base=baseline.metrics[selection.metric_id];
      return { metric_id:selection.metric_id,label:LABELS[selection.metric_id],objective:selection.objective,baseline_value:base,values:evaluations.map(item=>({alternative_id:item.alternative_id,label:item.label,value:item.metrics[selection.metric_id],delta_from_baseline:base===null||item.metrics[selection.metric_id]===null?null:cashFlowEngine.roundHalfUp(item.metrics[selection.metric_id]-base,4),rank:rankMap[item.alternative_id]})) };
    });
  }
  function rankings(evaluations, definition) {
    const totals={},weights={}; evaluations.forEach(item=>{totals[item.alternative_id]=0;weights[item.alternative_id]=0;});
    definition.selected_metrics.forEach(selection=>{
      const valid=evaluations.map(item=>item.metrics[selection.metric_id]).filter(value=>value!==null); if(!valid.length)return; const low=Math.min(...valid),high=Math.max(...valid);
      evaluations.forEach(item=>{const value=item.metrics[selection.metric_id];if(value===null)return;let normalized=high===low?1:(selection.objective==='maximize'?(value-low)/(high-low):(high-value)/(high-low));totals[item.alternative_id]+=normalized*selection.weight;weights[item.alternative_id]+=selection.weight;});
    });
    const scored=evaluations.map(item=>({item:item,score:cashFlowEngine.roundHalfUp(weights[item.alternative_id]===0?0:totals[item.alternative_id]/weights[item.alternative_id]*100,4)})).sort((a,b)=>b.score-a.score||a.item.label.localeCompare(b.item.label)||a.item.alternative_id.localeCompare(b.item.alternative_id));
    return scored.map((entry,index)=>({alternative_id:entry.item.alternative_id,label:entry.item.label,rank:index+1,weighted_score:entry.score,dominates:evaluations.filter(other=>other.alternative_id!==entry.item.alternative_id&&dominance(entry.item,other,definition.selected_metrics)).map(other=>other.alternative_id).sort(),dominated_by:evaluations.filter(other=>other.alternative_id!==entry.item.alternative_id&&dominance(other,entry.item,definition.selected_metrics)).map(other=>other.alternative_id).sort(),financial_only:true}));
  }
  function oneWay(item, scenario, baselineScenario) {
    const baseMetric=metric(cashFlowEngine.evaluate(scenario),item.metric_id);
    return {sensitivity_id:item.sensitivity_id,alternative_id:item.alternative_id,metric_id:item.metric_id,parameter:item.parameter,base_parameter_value:parameterValue(scenario,item.parameter),base_metric_value:baseMetric,points:item.values.map(value=>{const mv=evaluateMetric(scenario,item.parameter,value,item.metric_id);const bv=evaluateMetric(baselineScenario,item.parameter,value,item.metric_id);return {parameter_value:value,metric_value:mv,baseline_metric_value:bv,delta_from_baseline:mv===null||bv===null?null:cashFlowEngine.roundHalfUp(mv-bv,4)};})};
  }
  function twoWay(item, scenario) {
    const cells=[]; item.row_values.forEach(row=>{const rowScenario=applyParameter(scenario,item.row_parameter,row);item.column_values.forEach(column=>{cells.push({row_value:row,column_value:column,metric_value:metric(cashFlowEngine.evaluate(applyParameter(rowScenario,item.column_parameter,column)),item.metric_id)});});});
    return {sensitivity_id:item.sensitivity_id,alternative_id:item.alternative_id,metric_id:item.metric_id,row_parameter:item.row_parameter,column_parameter:item.column_parameter,cells:cells};
  }
  function breakEven(item, scenario) {
    const base=metric(cashFlowEngine.evaluate(scenario),item.metric_id);const baseParameter=parameterValue(scenario,item.parameter);
    if(base!==null&&Math.abs(base-item.target_value)<=item.tolerance)return {threshold_id:item.threshold_id,alternative_id:item.alternative_id,metric_id:item.metric_id,parameter:item.parameter,target_value:item.target_value,status:'already_at_target',threshold_value:baseParameter,metric_value:base,crossings:[],iterations:0};
    const samples=[];if(item.parameter.value_kind==='integer'){for(let v=Math.ceil(item.lower_bound);v<=Math.floor(item.upper_bound);v++)samples.push(v);}else{for(let i=0;i<=100;i++)samples.push(item.lower_bound+(item.upper_bound-item.lower_bound)*i/100);}
    const evaluated=[];let iterations=0;samples.forEach(value=>{const mv=evaluateMetric(scenario,item.parameter,value,item.metric_id);iterations++;if(mv!==null)evaluated.push([value,mv-item.target_value]);});const crossings=[];
    for(let i=0;i<evaluated.length-1;i++){let left=evaluated[i][0],ld=evaluated[i][1],right=evaluated[i+1][0],rd=evaluated[i+1][1];if(Math.abs(ld)<=item.tolerance){crossings.push({lower_value:left,upper_value:left,threshold_value:left,metric_value:ld+item.target_value});continue;}if((ld<0)===(rd<0))continue;let chosen,mv=null;if(item.parameter.value_kind==='integer'){chosen=Math.abs(ld)<=Math.abs(rd)?left:right;mv=evaluateMetric(scenario,item.parameter,chosen,item.metric_id);}else{for(let n=0;n<item.max_iterations;n++){chosen=(left+right)/2;mv=evaluateMetric(scenario,item.parameter,chosen,item.metric_id);iterations++;if(mv===null||Math.abs(mv-item.target_value)<=item.tolerance)break;const d=mv-item.target_value;if((ld<0)===(d<0)){left=chosen;ld=d;}else right=chosen;}}crossings.push({lower_value:evaluated[i][0],upper_value:evaluated[i+1][0],threshold_value:cashFlowEngine.roundHalfUp(chosen,6),metric_value:mv===null?null:cashFlowEngine.roundHalfUp(mv,6)});}
    if(!crossings.length)return {threshold_id:item.threshold_id,alternative_id:item.alternative_id,metric_id:item.metric_id,parameter:item.parameter,target_value:item.target_value,status:'no_crossing',threshold_value:null,metric_value:null,crossings:[],iterations:iterations};
    const reference=baseParameter===null?item.lower_bound:baseParameter;crossings.sort((a,b)=>Math.abs(a.threshold_value-reference)-Math.abs(b.threshold_value-reference));return {threshold_id:item.threshold_id,alternative_id:item.alternative_id,metric_id:item.metric_id,parameter:item.parameter,target_value:item.target_value,status:'found',threshold_value:crossings[0].threshold_value,metric_value:crossings[0].metric_value,crossings:crossings,iterations:iterations};
  }
  function evaluate(definition, generatedAt) {
    if(!cashFlowEngine)throw new Error('CatalystFinanceCashFlowEngine is required.');if(!definition||definition.contract_version!==CONTRACT_VERSION||definition.model_id!==MODEL_ID)throw new Error('Invalid comparison contract.');if(!definition.alternatives||definition.alternatives.length<3)throw new Error('At least three alternatives are required.');
    const evaluations=definition.alternatives.map(alternative=>{const publication=cashFlowEngine.evaluate(alternative.scenario,generatedAt);const metrics={};Object.keys(LABELS).forEach(id=>{metrics[id]=metric(publication,id);});return {alternative_id:alternative.alternative_id,label:alternative.label,kind:alternative.kind,source:alternative.source,non_financial_caveats:alternative.non_financial_caveats||[],metrics:metrics,publication:publication};});
    const byId={};definition.alternatives.forEach(item=>{byId[item.alternative_id]=item;});const baselineScenario=byId[definition.baseline_alternative_id].scenario;
    const one=(definition.one_way_sensitivities||[]).map(item=>oneWay(item,byId[item.alternative_id].scenario,baselineScenario));const two=(definition.two_way_sensitivities||[]).map(item=>twoWay(item,byId[item.alternative_id].scenario));const thresholds=(definition.break_even_definitions||[]).map(item=>breakEven(item,byId[item.alternative_id].scenario));
    const tornado=one.map(result=>{const low=result.points.slice().sort((a,b)=>a.parameter_value-b.parameter_value)[0],high=result.points.slice().sort((a,b)=>b.parameter_value-a.parameter_value)[0];const li=low.metric_value===null||result.base_metric_value===null?null:cashFlowEngine.roundHalfUp(low.metric_value-result.base_metric_value,4),hi=high.metric_value===null||result.base_metric_value===null?null:cashFlowEngine.roundHalfUp(high.metric_value-result.base_metric_value,4);return {sensitivity_id:result.sensitivity_id,alternative_id:result.alternative_id,parameter_id:result.parameter.parameter_id,label:result.parameter.label,low_value:low.parameter_value,high_value:high.parameter_value,low_impact:li,high_impact:hi,absolute_swing:li===null||hi===null?null:cashFlowEngine.roundHalfUp(Math.abs(hi-li),4)};}).sort((a,b)=>(b.absolute_swing||0)-(a.absolute_swing||0)||a.label.localeCompare(b.label));
    return {contract_version:CONTRACT_VERSION,model_id:MODEL_ID,definition:definition,alternatives:evaluations,aligned_metrics:aligned(evaluations,definition),rankings:rankings(evaluations,definition),one_way_sensitivities:one,two_way_sensitivities:two,break_even_results:thresholds,tornado:tornado,metadata:{generated_at:generatedAt||new Date().toISOString(),version:CONTRACT_VERSION}};
  }
  return {CONTRACT_VERSION:CONTRACT_VERSION,MODEL_ID:MODEL_ID,applyParameter:applyParameter,evaluate:evaluate};
});
