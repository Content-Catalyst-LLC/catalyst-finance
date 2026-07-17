(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CatalystFinanceOperatingEngine = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const CONTRACT_VERSION = '1.7.0';
  const MODEL_ID = 'catalyst-finance.operating';
  const DISCLAIMER = 'Decision-support output only. Validate accounting classifications, allocation bases, taxes, timing, capacity, and source-system controls before operational use.';
  function round(value, digits) {
    const factor = Math.pow(10, digits);
    return (value < 0 ? -1 : 1) * Math.floor(Math.abs(value) * factor + 0.5 + 1e-12) / factor;
  }
  function status(amount) {
    if (Math.abs(amount) <= 1e-9) return 'neutral';
    return amount > 0 ? 'favorable' : 'unfavorable';
  }
  function variance(id, label, amount, rationale) {
    const value = round(amount, 6);
    return {variance_id:id, label:label, amount:value, status:status(value), rationale:rationale};
  }
  function evaluatePeriod(unit, item, target) {
    const budgetRevenue=item.budget_units*item.budget_unit_price;
    const flexibleRevenue=item.actual_units*item.budget_unit_price;
    const actualRevenue=item.actual_units*item.actual_unit_price;
    const budgetVariable=item.budget_units*item.budget_variable_cost_per_unit;
    const flexibleVariable=item.actual_units*item.budget_variable_cost_per_unit;
    const actualVariable=item.actual_units*item.actual_variable_cost_per_unit;
    const budgetFixed=item.budget_direct_fixed_cost+item.budget_allocated_overhead;
    const actualFixed=item.actual_direct_fixed_cost+item.actual_allocated_overhead;
    const budgetContribution=budgetRevenue-budgetVariable;
    const flexibleContribution=flexibleRevenue-flexibleVariable;
    const actualContribution=actualRevenue-actualVariable;
    const budgetProfit=budgetContribution-budgetFixed;
    const flexibleProfit=flexibleContribution-budgetFixed;
    const actualProfit=actualContribution-actualFixed;
    const budgetCmUnit=item.budget_unit_price-item.budget_variable_cost_per_unit;
    const actualCmUnit=item.actual_unit_price-item.actual_variable_cost_per_unit;
    const cmPercent=actualRevenue<=0?null:actualContribution/actualRevenue*100;
    const breakEven=budgetCmUnit<=0?null:budgetFixed/budgetCmUnit;
    const breakEvenRevenue=breakEven===null?null:breakEven*item.budget_unit_price;
    const margin=breakEven===null?null:item.actual_units-breakEven;
    const marginPercent=margin===null||item.actual_units<=0?null:margin/item.actual_units*100;
    const leverage=Math.abs(actualProfit)<=1e-12?null:actualContribution/actualProfit;
    const targetUnits=budgetCmUnit<=0?null:(budgetFixed+target)/budgetCmUnit;
    const volume=flexibleContribution-budgetContribution;
    const price=actualRevenue-flexibleRevenue;
    const variableSpending=flexibleVariable-actualVariable;
    const fixedSpending=budgetFixed-actualFixed;
    const profitVariance=actualProfit-budgetProfit;
    const variances=[
      variance('sales_volume','Sales volume variance',volume,'Actual versus budget volume valued at the budget contribution margin per unit.'),
      variance('sales_price','Sales price variance',price,'Actual volume multiplied by the difference between actual and budget unit price.'),
      variance('variable_cost_spending','Variable cost spending variance',variableSpending,'Actual volume multiplied by budget variable cost less actual variable cost.'),
      variance('fixed_cost_spending','Fixed cost spending variance',fixedSpending,'Budget direct fixed cost and allocated overhead less the corresponding actual amount.'),
      variance('operating_profit','Operating profit variance',profitVariance,'Actual operating profit less static-budget operating profit.')
    ];
    return {
      unit_id:unit.unit_id, unit_label:unit.label, cost_center:unit.cost_center,
      period:item.period, label:item.label,
      budget_units:round(item.budget_units,6), actual_units:round(item.actual_units,6),
      budget_revenue:round(budgetRevenue,6), flexible_revenue:round(flexibleRevenue,6), actual_revenue:round(actualRevenue,6),
      budget_variable_cost:round(budgetVariable,6), flexible_variable_cost:round(flexibleVariable,6), actual_variable_cost:round(actualVariable,6),
      budget_fixed_cost:round(budgetFixed,6), actual_fixed_cost:round(actualFixed,6),
      budget_contribution:round(budgetContribution,6), flexible_contribution:round(flexibleContribution,6), actual_contribution:round(actualContribution,6),
      budget_operating_profit:round(budgetProfit,6), flexible_operating_profit:round(flexibleProfit,6), actual_operating_profit:round(actualProfit,6),
      budget_contribution_per_unit:round(budgetCmUnit,6), actual_contribution_per_unit:round(actualCmUnit,6),
      contribution_margin_percent:cmPercent===null?null:round(cmPercent,6),
      break_even_units:breakEven===null?null:round(breakEven,6), break_even_revenue:breakEvenRevenue===null?null:round(breakEvenRevenue,6),
      margin_of_safety_units:margin===null?null:round(margin,6), margin_of_safety_percent:marginPercent===null?null:round(marginPercent,6),
      degree_of_operating_leverage:leverage===null?null:round(leverage,6), target_profit_units:targetUnits===null?null:round(targetUnits,6),
      variances:variances, variance_reconciliation:round(volume+price+variableSpending+fixedSpending,6)
    };
  }
  function summary(id,label,rows,target) {
    function sum(key){return rows.reduce((value,row)=>value+row[key],0);}
    const budgetUnits=sum('budget_units'), actualUnits=sum('actual_units');
    const budgetRevenue=sum('budget_revenue'), actualRevenue=sum('actual_revenue');
    const budgetVariable=sum('budget_variable_cost'), actualVariable=sum('actual_variable_cost');
    const budgetFixed=sum('budget_fixed_cost'), actualFixed=sum('actual_fixed_cost');
    const budgetContribution=budgetRevenue-budgetVariable, actualContribution=actualRevenue-actualVariable;
    const budgetProfit=budgetContribution-budgetFixed, actualProfit=actualContribution-actualFixed;
    const budgetCmUnit=budgetUnits<=0?null:budgetContribution/budgetUnits;
    const breakEven=budgetCmUnit===null||budgetCmUnit<=0?null:budgetFixed/budgetCmUnit;
    const margin=breakEven===null?null:actualUnits-breakEven;
    const leverage=Math.abs(actualProfit)<=1e-12?null:actualContribution/actualProfit;
    const targetUnits=budgetCmUnit===null||budgetCmUnit<=0?null:(budgetFixed+target)/budgetCmUnit;
    return {summary_id:id,label:label,budget_units:round(budgetUnits,6),actual_units:round(actualUnits,6),budget_revenue:round(budgetRevenue,6),actual_revenue:round(actualRevenue,6),budget_variable_cost:round(budgetVariable,6),actual_variable_cost:round(actualVariable,6),budget_fixed_cost:round(budgetFixed,6),actual_fixed_cost:round(actualFixed,6),budget_contribution:round(budgetContribution,6),actual_contribution:round(actualContribution,6),budget_operating_profit:round(budgetProfit,6),actual_operating_profit:round(actualProfit,6),operating_profit_variance:round(actualProfit-budgetProfit,6),contribution_margin_percent:actualRevenue<=0?null:round(actualContribution/actualRevenue*100,6),break_even_units:breakEven===null?null:round(breakEven,6),margin_of_safety_units:margin===null?null:round(margin,6),degree_of_operating_leverage:leverage===null?null:round(leverage,6),target_profit_units:targetUnits===null?null:round(targetUnits,6)};
  }
  function evaluate(definition, generatedAt) {
    if (!definition || definition.contract_version!==CONTRACT_VERSION || definition.model_id!==MODEL_ID) throw new Error('Invalid operating contract.');
    const rows=[]; definition.units.forEach(unit=>unit.periods.forEach(period=>rows.push(evaluatePeriod(unit,period,definition.target_operating_profit))));
    const unitSummaries=definition.units.map(unit=>summary(unit.unit_id,unit.label,rows.filter(row=>row.unit_id===unit.unit_id),definition.target_operating_profit));
    const names=Array.from(new Set(rows.map(row=>row.cost_center))).sort();
    const centerSummaries=names.map((name,index)=>summary('cost-center-'+(index+1),name,rows.filter(row=>row.cost_center===name),definition.target_operating_profit));
    const total=summary('total','All operating units',rows,definition.target_operating_profit);
    const flags=[];
    if(rows.some(row=>row.actual_operating_profit<0)) flags.push('One or more operating periods report an actual operating loss.');
    if(rows.some(row=>row.margin_of_safety_units!==null&&row.margin_of_safety_units<0)) flags.push('One or more periods operate below the budget-basis break-even volume.');
    if(rows.some(row=>row.variance_reconciliation!==row.variances[row.variances.length-1].amount)) flags.push('A rounded variance reconciliation differs from the reported operating-profit variance.');
    if(rows.some(row=>row.degree_of_operating_leverage!==null&&Math.abs(row.degree_of_operating_leverage)>=5)) flags.push('One or more periods have high operating leverage and elevated profit sensitivity.');
    if(!flags.length) flags.push('No operating loss, break-even shortfall, or high-leverage flag was detected.');
    return {contract_version:CONTRACT_VERSION,model_id:MODEL_ID,definition:definition,rows:rows,unit_summaries:unitSummaries,cost_center_summaries:centerSummaries,total_summary:total,flags:flags,methodology:{model_id:MODEL_ID,model_version:CONTRACT_VERSION,budget_policy:'static_flexible_actual',variance_sign_policy:'positive_is_favorable',volume_variance_policy:'budget_contribution_margin',fixed_cost_policy:'direct_plus_allocated_overhead',break_even_policy:'budget_contribution_margin_per_unit',aggregation_policy:'sum_rows_then_recompute_ratios'},metadata:{generated_at:generatedAt||new Date().toISOString(),version:CONTRACT_VERSION,row_count:rows.length,unit_count:unitSummaries.length,cost_center_count:centerSummaries.length,disclaimer:DISCLAIMER}};
  }
  return {CONTRACT_VERSION:CONTRACT_VERSION,MODEL_ID:MODEL_ID,evaluate:evaluate,evaluatePeriod:evaluatePeriod};
});
