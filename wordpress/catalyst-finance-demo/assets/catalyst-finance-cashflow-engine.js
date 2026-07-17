(function (root, factory) {
  const engine = factory();
  if (typeof module === 'object' && module.exports) module.exports = engine;
  else root.CatalystFinanceCashFlowEngine = engine;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CONTRACT_VERSION = '1.8.0';
  const MODEL_ID = 'catalyst-finance.cash-flow';
  const DISCLAIMER = 'Educational software only; not financial, investment, legal, accounting, tax, fiduciary, procurement, funding, lending, or assurance advice.';
  const INFLOW = new Set(['revenue', 'savings', 'avoided_cost', 'grant', 'rebate', 'residual_value', 'working_capital_recovery', 'other_benefit']);
  const COST = new Set(['capital_cost', 'operating_cost', 'decommissioning_cost', 'working_capital', 'other_cost']);
  const BCR_BENEFIT = new Set(['revenue', 'savings', 'avoided_cost', 'residual_value', 'working_capital_recovery', 'other_benefit']);
  const TERMINAL = new Set(['residual_value', 'decommissioning_cost', 'working_capital_recovery']);
  const ALL = ['capital_cost', 'operating_cost', 'revenue', 'savings', 'avoided_cost', 'grant', 'rebate', 'residual_value', 'decommissioning_cost', 'working_capital', 'working_capital_recovery', 'other_benefit', 'other_cost'];

  function roundHalfUp(value, decimals) {
    const factor = Math.pow(10, decimals);
    const sign = value < 0 ? -1 : 1;
    const result = sign * Math.round(Math.abs(value) * factor + Number.EPSILON) / factor;
    return Object.is(result, -0) ? 0 : result;
  }

  function periodsPerYear(frequency) {
    return { monthly: 12, quarterly: 4, annual: 1 }[frequency];
  }

  function effectivePeriodRate(annualPercent, frequency) {
    return Math.pow(1 + annualPercent / 100, 1 / periodsPerYear(frequency)) - 1;
  }

  function validate(scenario) {
    const issues = [];
    if (!scenario || scenario.contract_version !== CONTRACT_VERSION) issues.push('contract_version must be 1.8.0');
    if (!scenario || scenario.model_id !== MODEL_ID) issues.push('model_id must be catalyst-finance.cash-flow');
    if (!scenario || !scenario.context) issues.push('context is required');
    if (!scenario || !scenario.project || !String(scenario.project.name || '').trim()) issues.push('project.name is required');
    if (!scenario || !Array.isArray(scenario.lines) || !scenario.lines.length) issues.push('lines are required');
    if (issues.length) throw new Error(issues.join('; '));
    if (scenario.context.price_basis !== scenario.context.discount_rate_basis) throw new Error('price_basis and discount_rate_basis must match for cash-flow analysis');
    const ids = new Set();
    scenario.lines.forEach(line => {
      if (ids.has(line.flow_id)) throw new Error('cash-flow line IDs must be unique');
      ids.add(line.flow_id);
      const end = line.end_period === null || line.end_period === undefined ? line.start_period : line.end_period;
      if (end > scenario.analysis_horizon_periods) throw new Error('cash-flow line ' + line.flow_id + ' exceeds the analysis horizon');
      if (line.price_basis !== scenario.context.price_basis) throw new Error('cash-flow line ' + line.flow_id + ' price_basis must match context');
    });
  }

  function normalizeScenario(input) {
    const scenario = JSON.parse(JSON.stringify(input));
    scenario.lines = scenario.lines.map(line => Object.assign({
      end_period: null,
      interval_periods: 1,
      escalation_rate_percent_annual: 0,
      notes: ''
    }, line));
    return scenario;
  }

  function periodLabel(period, frequency) {
    if (period === 0) return 'Period 0';
    return ({ monthly: 'Month', quarterly: 'Quarter', annual: 'Year' }[frequency]) + ' ' + period;
  }

  function expand(scenario) {
    const rows = Array.from({ length: scenario.analysis_horizon_periods + 1 }, () => []);
    const perYear = periodsPerYear(scenario.context.period_frequency);
    scenario.lines.forEach(line => {
      const end = line.end_period === null || line.end_period === undefined ? line.start_period : line.end_period;
      const interval = line.interval_periods || 1;
      const annualRate = (line.escalation_rate_percent_annual || 0) / 100;
      for (let period = line.start_period; period <= end; period += interval) {
        const amount = line.amount * Math.pow(1 + annualRate, period / perYear);
        const signed = INFLOW.has(line.category) ? amount : -amount;
        rows[period].push({
          flow_id: line.flow_id,
          label: line.label,
          category: line.category,
          period: period,
          amount: amount,
          signed_amount: signed,
          direction: signed >= 0 ? 'inflow' : 'outflow'
        });
      }
    });
    return rows;
  }

  function signChanges(values) {
    const signs = values.filter(value => Math.abs(value) > 1e-12).map(value => value > 0 ? 1 : -1);
    let count = 0;
    for (let i = 1; i < signs.length; i += 1) if (signs[i] !== signs[i - 1]) count += 1;
    return count;
  }

  function npvAtRate(values, rate) {
    if (rate <= -1) return Infinity;
    return values.reduce((sum, value, period) => sum + value / Math.pow(1 + rate, period), 0);
  }

  function bisect(values, left, right) {
    let leftValue = npvAtRate(values, left);
    for (let i = 0; i < 100; i += 1) {
      const middle = (left + right) / 2;
      const value = npvAtRate(values, middle);
      if (Math.abs(value) < 1e-10) return middle;
      if ((leftValue < 0) === (value < 0)) { left = middle; leftValue = value; } else right = middle;
    }
    return (left + right) / 2;
  }

  function irrRoots(values) {
    if (!values.some(value => value > 0) || !values.some(value => value < 0)) return [];
    const grid = [];
    for (let i = 0; i <= 250; i += 1) grid.push(-0.9999 + i * (0.9999 / 250));
    const maximum = Math.log10(1001);
    for (let i = 1; i <= 500; i += 1) grid.push(Math.pow(10, maximum * i / 500) - 1);
    const roots = [];
    let previousRate = grid[0];
    let previousValue = npvAtRate(values, previousRate);
    for (let i = 1; i < grid.length; i += 1) {
      const rate = grid[i];
      const value = npvAtRate(values, rate);
      let candidate = null;
      if (Math.abs(value) < 1e-8) candidate = rate;
      else if ((previousValue < 0) !== (value < 0)) candidate = bisect(values, previousRate, rate);
      if (candidate !== null && !roots.some(existing => Math.abs(candidate - existing) < 1e-7)) roots.push(candidate);
      previousRate = rate;
      previousValue = value;
    }
    return roots;
  }

  function payback(values) {
    let cumulative = 0;
    if (values.length && values[0] >= 0) return 0;
    for (let period = 0; period < values.length; period += 1) {
      const previous = cumulative;
      cumulative += values[period];
      if (period > 0 && previous < 0 && cumulative >= 0 && values[period] > 0) return (period - 1) + (-previous / values[period]);
    }
    return null;
  }

  function annualize(periodicRate, frequency) {
    return (Math.pow(1 + periodicRate, periodsPerYear(frequency)) - 1) * 100;
  }

  function mirr(values, financeRate, reinvestmentRate, frequency) {
    const horizon = values.length - 1;
    if (horizon <= 0) return null;
    let negativePv = 0;
    let positiveFv = 0;
    values.forEach((value, period) => {
      if (value < 0) negativePv += -value / Math.pow(1 + financeRate, period);
      if (value > 0) positiveFv += value * Math.pow(1 + reinvestmentRate, horizon - period);
    });
    if (negativePv <= 0 || positiveFv <= 0) return null;
    return annualize(Math.pow(positiveFv / negativePv, 1 / horizon) - 1, frequency);
  }

  function eav(npv, annualPercent, years) {
    if (years <= 0) return 0;
    const rate = annualPercent / 100;
    if (Math.abs(rate) < 1e-12) return npv / years;
    return npv * (rate * Math.pow(1 + rate, years) / (Math.pow(1 + rate, years) - 1));
  }

  function trace(metricId, label, value, included, flowIds, formula, notes) {
    return {
      metric_id: metricId,
      label: label,
      value: value,
      included_categories: ALL.filter(item => included.has(item)),
      excluded_categories: ALL.filter(item => !included.has(item)),
      included_flow_ids: flowIds,
      formula: formula,
      notes: notes
    };
  }

  function evaluate(inputScenario, generatedAt) {
    const scenario = normalizeScenario(inputScenario);
    validate(scenario);
    const frequency = scenario.context.period_frequency;
    const periodicDiscount = effectivePeriodRate(scenario.discount_rate_percent_annual, frequency);
    const periodicFinance = effectivePeriodRate(scenario.finance_rate_percent_annual, frequency);
    const periodicReinvestment = effectivePeriodRate(scenario.reinvestment_rate_percent_annual, frequency);
    const expanded = expand(scenario);
    const moneyDecimals = scenario.context.monetary_decimals;
    const ratioDecimals = scenario.context.ratio_decimals;
    let cumulative = 0;
    let cumulativeDiscounted = 0;
    let totalInflows = 0;
    let totalOutflows = 0;
    let pvInflows = 0;
    let pvOutflows = 0;
    let bcrBenefits = 0;
    let bcrCosts = 0;
    let terminalValue = 0;
    const netValues = [];
    const discountedValues = [];
    const periods = expanded.map((lineItems, period) => {
      const inflows = lineItems.filter(item => item.signed_amount >= 0).reduce((sum, item) => sum + item.signed_amount, 0);
      const outflows = -lineItems.filter(item => item.signed_amount < 0).reduce((sum, item) => sum + item.signed_amount, 0);
      const net = inflows - outflows;
      const discounted = net / Math.pow(1 + periodicDiscount, period);
      cumulative += net;
      cumulativeDiscounted += discounted;
      totalInflows += inflows;
      totalOutflows += outflows;
      pvInflows += inflows / Math.pow(1 + periodicDiscount, period);
      pvOutflows += outflows / Math.pow(1 + periodicDiscount, period);
      lineItems.forEach(item => {
        const discountedItem = item.signed_amount / Math.pow(1 + periodicDiscount, period);
        if (BCR_BENEFIT.has(item.category)) bcrBenefits += discountedItem;
        else if (COST.has(item.category)) bcrCosts += -discountedItem;
        if (period === scenario.analysis_horizon_periods && TERMINAL.has(item.category)) terminalValue += item.signed_amount;
      });
      netValues.push(net);
      discountedValues.push(discounted);
      return {
        period: period,
        period_label: periodLabel(period, frequency),
        inflows: roundHalfUp(inflows, moneyDecimals),
        outflows: roundHalfUp(outflows, moneyDecimals),
        net_cash_flow: roundHalfUp(net, moneyDecimals),
        discounted_net_cash_flow: roundHalfUp(discounted, moneyDecimals),
        cumulative_cash_flow: roundHalfUp(cumulative, moneyDecimals),
        cumulative_discounted_cash_flow: roundHalfUp(cumulativeDiscounted, moneyDecimals),
        line_items: lineItems.map(item => Object.assign({}, item, {
          amount: roundHalfUp(item.amount, moneyDecimals),
          signed_amount: roundHalfUp(item.signed_amount, moneyDecimals)
        }))
      };
    });
    const npv = discountedValues.reduce((sum, value) => sum + value, 0);
    const changes = signChanges(netValues);
    const periodicRoots = irrRoots(netValues);
    const annualRoots = periodicRoots.map(root => annualize(root, frequency));
    let irrStatus;
    let irr = null;
    if (changes > 1) irrStatus = 'ambiguous_multiple_sign_changes';
    else if (annualRoots.length) { irrStatus = 'unique'; irr = annualRoots[0]; }
    else if (netValues.some(value => value > 0) && netValues.some(value => value < 0)) irrStatus = 'no_root';
    else irrStatus = 'not_applicable';
    const simplePayback = payback(netValues);
    const discountedPayback = payback(discountedValues);
    const modifiedIrr = mirr(netValues, periodicFinance, periodicReinvestment, frequency);
    const profitabilityIndex = pvOutflows <= 0 ? null : pvInflows / pvOutflows;
    const benefitCostRatio = bcrCosts <= 0 ? null : bcrBenefits / bcrCosts;
    const equivalentAnnualValue = eav(npv, scenario.discount_rate_percent_annual, scenario.analysis_horizon_periods / periodsPerYear(frequency));
    const allFlowIds = scenario.lines.map(line => line.flow_id);
    const bcrFlowIds = scenario.lines.filter(line => BCR_BENEFIT.has(line.category) || COST.has(line.category)).map(line => line.flow_id);
    const terminalFlowIds = scenario.lines.filter(line => TERMINAL.has(line.category)).map(line => line.flow_id);
    const allSet = new Set(ALL);
    const bcrSet = new Set(Array.from(BCR_BENEFIT).concat(Array.from(COST)));
    const metricTrace = [
      trace('npv', 'Net present value', roundHalfUp(npv, moneyDecimals), allSet, allFlowIds, 'Σ net cash flow_t / (1 + periodic discount rate)^t', 'Includes every modeled cash-flow category.'),
      trace('simple_payback', 'Simple payback', simplePayback === null ? null : roundHalfUp(simplePayback, ratioDecimals), allSet, allFlowIds, 'First undiscounted cumulative crossing, interpolated within period', 'Does not discount cash flows after the recovery point.'),
      trace('discounted_payback', 'Discounted payback', discountedPayback === null ? null : roundHalfUp(discountedPayback, ratioDecimals), allSet, allFlowIds, 'First discounted cumulative crossing, interpolated within period', 'Uses the disclosed annual discount rate converted to the selected frequency.'),
      trace('irr', 'Internal rate of return', irr === null ? null : roundHalfUp(irr, ratioDecimals), allSet, allFlowIds, 'Rate where NPV equals zero', 'All detected roots are reported; multiple sign changes suppress a single IRR.'),
      trace('mirr', 'Modified internal rate of return', modifiedIrr === null ? null : roundHalfUp(modifiedIrr, ratioDecimals), allSet, allFlowIds, '(FV positive flows / PV negative flows)^(1/n) - 1', 'Uses disclosed finance and reinvestment rates.'),
      trace('profitability_index', 'Profitability index', profitabilityIndex === null ? null : roundHalfUp(profitabilityIndex, ratioDecimals), allSet, allFlowIds, 'PV of all inflows / PV of all outflows', 'Includes grants and rebates as project inflows.'),
      trace('benefit_cost_ratio', 'Benefit-cost ratio', benefitCostRatio === null ? null : roundHalfUp(benefitCostRatio, ratioDecimals), bcrSet, bcrFlowIds, 'PV of benefits / PV of costs', 'Grants and rebates are excluded as transfers rather than treated as benefits.'),
      trace('equivalent_annual_value', 'Equivalent annual value', roundHalfUp(equivalentAnnualValue, moneyDecimals), allSet, allFlowIds, 'NPV × annual capital-recovery factor', 'Expresses NPV as an equivalent annual amount over the analysis horizon.'),
      trace('terminal_value', 'Terminal value', roundHalfUp(terminalValue, moneyDecimals), TERMINAL, terminalFlowIds, 'Residual value + working-capital recovery - decommissioning cost in final period', 'Reports only terminal categories occurring in the final analysis period.')
    ];
    const flags = [
      'Nominal/real price and discount-rate bases match.',
      'Cash-flow table reconciles across ' + periods.length + ' periods including period 0.'
    ];
    if (changes > 1) flags.push('IRR is ambiguous because the cash-flow series has multiple sign changes; use NPV, MIRR, and the listed roots instead.');
    else if (irrStatus === 'no_root') flags.push('No IRR root was detected in the supported search range.');
    else if (irrStatus === 'not_applicable') flags.push('IRR is not applicable because cash flows do not include both signs.');
    if (simplePayback === null) flags.push('Simple payback is not achieved within the selected horizon.');
    if (discountedPayback === null) flags.push('Discounted payback is not achieved within the selected horizon.');
    if (scenario.lines.some(line => line.category === 'working_capital') && !scenario.lines.some(line => line.category === 'working_capital_recovery')) flags.push('Working capital is modeled without an explicit recovery flow.');
    if (terminalValue === 0) flags.push('No net terminal value is modeled in the final period.');
    return {
      contract_version: CONTRACT_VERSION,
      model_id: MODEL_ID,
      project: scenario.project,
      context: scenario.context,
      assumptions: scenario,
      periods: periods,
      metrics: {
        total_inflows: roundHalfUp(totalInflows, moneyDecimals),
        total_outflows: roundHalfUp(totalOutflows, moneyDecimals),
        net_cash_flow: roundHalfUp(netValues.reduce((sum, value) => sum + value, 0), moneyDecimals),
        present_value_inflows: roundHalfUp(pvInflows, moneyDecimals),
        present_value_outflows: roundHalfUp(pvOutflows, moneyDecimals),
        npv: roundHalfUp(npv, moneyDecimals),
        simple_payback_periods: simplePayback === null ? null : roundHalfUp(simplePayback, ratioDecimals),
        discounted_payback_periods: discountedPayback === null ? null : roundHalfUp(discountedPayback, ratioDecimals),
        irr_percent_annual: irr === null ? null : roundHalfUp(irr, ratioDecimals),
        irr_roots_percent_annual: annualRoots.map(root => roundHalfUp(root, ratioDecimals)),
        irr_status: irrStatus,
        mirr_percent_annual: modifiedIrr === null ? null : roundHalfUp(modifiedIrr, ratioDecimals),
        profitability_index: profitabilityIndex === null ? null : roundHalfUp(profitabilityIndex, ratioDecimals),
        benefit_cost_ratio: benefitCostRatio === null ? null : roundHalfUp(benefitCostRatio, ratioDecimals),
        equivalent_annual_value: roundHalfUp(equivalentAnnualValue, moneyDecimals),
        terminal_value: roundHalfUp(terminalValue, moneyDecimals),
        sign_changes: changes,
        metric_trace: metricTrace
      },
      interpretation: { basis_status: 'matched', flags: flags },
      methodology: {
        model_id: MODEL_ID,
        model_version: CONTRACT_VERSION,
        timing_policy: 'period_zero_then_end_of_period',
        annual_to_period_rate_policy: 'effective_rate_conversion',
        escalation_policy: 'effective_annual_compounding',
        payback_policy: 'linear_interpolation_within_crossing_period',
        irr_policy: 'all_detected_roots_and_ambiguity_flag',
        transfer_policy: 'grants_and_rebates_excluded_from_bcr'
      },
      metadata: {
        generated_at: generatedAt || new Date().toISOString(),
        tool: 'Catalyst Finance cash-flow engine',
        version: CONTRACT_VERSION,
        disclaimer: DISCLAIMER
      }
    };
  }

  return {
    CONTRACT_VERSION: CONTRACT_VERSION,
    MODEL_ID: MODEL_ID,
    effectivePeriodRate: effectivePeriodRate,
    evaluate: evaluate,
    expand: expand,
    roundHalfUp: roundHalfUp
  };
});
