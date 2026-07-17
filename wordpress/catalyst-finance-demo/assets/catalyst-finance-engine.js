(function (root, factory) {
  const engine = factory();
  if (typeof module === 'object' && module.exports) module.exports = engine;
  else root.CatalystFinanceEngine = engine;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CONTRACT_VERSION = '1.4.0';
  const MODEL_ID = 'catalyst-finance.screening';
  const DISCLAIMER = 'Educational software only; not financial, investment, legal, accounting, tax, fiduciary, procurement, funding, lending, or assurance advice.';
  const REVIEW_BOUNDARY = 'Educational scenario output only. Validate assumptions and obtain qualified human review before financial, investment, tax, accounting, legal, fiduciary, procurement, funding, or assurance decisions.';
  const LEGACY_FIELDS = [
    'project.name', 'project.category', 'inputs.capital_cost', 'inputs.external_funding',
    'inputs.annual_savings', 'inputs.annual_operating_cost', 'inputs.time_horizon_years',
    'inputs.discount_rate_percent', 'inputs.annual_emissions_reduced_tons',
    'inputs.carbon_price_per_ton', 'inputs.confidence_percent',
    'inputs.implementation_risk_percent'
  ];

  const V110_FIELDS = [
    'model_id', 'project.name', 'project.category', 'context.currency',
    'context.price_basis', 'context.discount_rate_basis', 'context.period_frequency',
    'context.time_basis', 'context.rounding_policy', 'context.monetary_decimals',
    'context.ratio_decimals', 'context.score_decimals', 'assumptions.capital_cost',
    'assumptions.external_funding', 'assumptions.annual_savings',
    'assumptions.annual_operating_cost', 'assumptions.time_horizon_years',
    'assumptions.discount_rate_percent', 'assumptions.annual_emissions_reduced_tons',
    'assumptions.carbon_price_per_ton', 'assumptions.confidence_percent',
    'assumptions.implementation_risk_percent'
  ];

  function roundHalfUp(value, decimals) {
    const factor = Math.pow(10, decimals);
    const sign = value < 0 ? -1 : 1;
    return sign * Math.round(Math.abs(value) * factor + Number.EPSILON) / factor;
  }

  function presentValueAnnuity(annualValue, years, discountRatePercent) {
    if (years <= 0) return 0;
    const rate = discountRatePercent / 100;
    const fullPeriods = Math.floor(years);
    const fraction = years - fullPeriods;
    let total = 0;
    for (let period = 1; period <= fullPeriods; period += 1) {
      total += annualValue / Math.pow(1 + rate, period);
    }
    if (fraction > 1e-12) {
      total += (annualValue * fraction) / Math.pow(1 + rate, years);
    }
    return total;
  }

  function defaultContext() {
    return {
      currency: 'USD', price_basis: 'nominal', discount_rate_basis: 'nominal',
      period_frequency: 'annual', time_basis: 'end_of_period', rounding_policy: 'half_up',
      monetary_decimals: 2, ratio_decimals: 2, score_decimals: 1
    };
  }

  function migrateLegacy(payload) {
    if (!payload || typeof payload !== 'object' || !payload.project || !payload.inputs) {
      throw new Error('Legacy scenario requires project and inputs objects');
    }
    return {
      scenario: {
        contract_version: CONTRACT_VERSION,
        model_id: MODEL_ID,
        project: Object.assign({}, payload.project),
        context: defaultContext(),
        assumptions: Object.assign({}, payload.inputs)
      },
      migration: {
        source_contract_version: '1.0.0',
        target_contract_version: CONTRACT_VERSION,
        preserved_fields: LEGACY_FIELDS.slice()
      }
    };
  }

  function migrateVersioned(payload, sourceVersion) {
    const scenario = JSON.parse(JSON.stringify(payload));
    scenario.contract_version = CONTRACT_VERSION;
    return {
      scenario: scenario,
      migration: {
        source_contract_version: sourceVersion,
        target_contract_version: CONTRACT_VERSION,
        preserved_fields: V110_FIELDS.slice()
      }
    };
  }

  function migrateV110(payload) { return migrateVersioned(payload, '1.1.0'); }
  function migrateV120(payload) { return migrateVersioned(payload, '1.2.0'); }
  function migrateV130(payload) { return migrateVersioned(payload, '1.3.0'); }

  function normalizeScenario(payload) {
    if (payload && !payload.contract_version && payload.inputs) return migrateLegacy(payload);
    if (payload && payload.contract_version === '1.1.0') return migrateV110(payload);
    if (payload && payload.contract_version === '1.2.0') return migrateV120(payload);
    if (payload && payload.contract_version === '1.3.0') return migrateV130(payload);
    return { scenario: payload, migration: null };
  }

  function validateScenario(scenario) {
    const issues = [];
    if (!scenario || typeof scenario !== 'object') issues.push('scenario must be an object');
    if (!scenario || scenario.contract_version !== CONTRACT_VERSION) issues.push('contract_version must be 1.4.0');
    if (!scenario || scenario.model_id !== MODEL_ID) issues.push('model_id must be catalyst-finance.screening');
    if (!scenario || !scenario.project || !String(scenario.project.name || '').trim()) issues.push('project.name is required');
    if (!scenario || !scenario.context) issues.push('context is required');
    if (!scenario || !scenario.assumptions) issues.push('assumptions are required');
    if (issues.length) throw new Error(issues.join('; '));
    const context = scenario.context;
    const a = scenario.assumptions;
    if (context.price_basis !== context.discount_rate_basis) issues.push('price and discount-rate basis must match');
    ['capital_cost', 'external_funding', 'annual_savings', 'annual_operating_cost', 'carbon_price_per_ton'].forEach(key => {
      if (!Number.isFinite(a[key]) || a[key] < 0) issues.push(key + ' must be non-negative');
    });
    if (!Number.isFinite(a.time_horizon_years) || a.time_horizon_years <= 0 || a.time_horizon_years > 100) issues.push('time_horizon_years must be greater than 0 and at most 100');
    if (!Number.isFinite(a.discount_rate_percent) || a.discount_rate_percent <= -100 || a.discount_rate_percent > 100) issues.push('discount_rate_percent must be greater than -100 and at most 100');
    ['confidence_percent', 'implementation_risk_percent'].forEach(key => {
      if (!Number.isFinite(a[key]) || a[key] < 0 || a[key] > 100) issues.push(key + ' must be between 0 and 100');
    });
    if (a.annual_emissions_reduced_tons !== null && (!Number.isFinite(a.annual_emissions_reduced_tons) || a.annual_emissions_reduced_tons < 0)) issues.push('annual_emissions_reduced_tons must be null or non-negative');
    if (a.annual_emissions_reduced_tons === null && a.carbon_price_per_ton !== 0) issues.push('carbon_price_per_ton must be 0 when emissions are missing');
    if (issues.length) throw new Error(issues.join('; '));
  }

  function scoreComponents(npv, payback, netCapitalCost, netAnnualBenefit, horizon, confidence, implementationRisk, decimals) {
    let financialScore;
    let financialReason;
    if (npv > 0) { financialScore = 80; financialReason = 'NPV is positive under the current assumptions.'; }
    else if (Math.abs(npv) < 1e-12) { financialScore = 50; financialReason = 'NPV is approximately zero under the current assumptions.'; }
    else { financialScore = 20; financialReason = 'NPV is negative under the current assumptions.'; }
    let paybackScore;
    let paybackReason;
    if (netCapitalCost === 0 && netAnnualBenefit > 0) { paybackScore = 100; paybackReason = 'No net upfront capital remains and annual benefit is positive.'; }
    else if (payback === null) { paybackScore = 10; paybackReason = 'No simple payback exists because annual benefit is non-positive.'; }
    else if (payback <= 3) { paybackScore = 90; paybackReason = 'Simple payback is three years or less.'; }
    else if (payback <= horizon) { paybackScore = 70; paybackReason = 'Simple payback occurs within the selected horizon.'; }
    else { paybackScore = 30; paybackReason = 'Simple payback exceeds the selected horizon.'; }
    const raw = [
      ['financial_signal', 'Financial signal', financialScore, 0.35, financialReason],
      ['payback_signal', 'Payback signal', paybackScore, 0.25, paybackReason],
      ['evidence_confidence', 'Evidence confidence', confidence, 0.20, 'Uses the disclosed evidence-confidence assumption directly.'],
      ['implementation_resilience', 'Implementation resilience', 100 - implementationRisk, 0.20, 'Equals 100 minus the disclosed implementation-risk assumption.']
    ];
    return raw.map(item => ({
      component_id: item[0], label: item[1], raw_score: roundHalfUp(item[2], decimals),
      weight: item[3], weighted_contribution: roundHalfUp(item[2] * item[3], decimals), rationale: item[4]
    }));
  }

  function evaluate(inputPayload, generatedAt) {
    const normalized = normalizeScenario(inputPayload);
    const scenario = normalized.scenario;
    validateScenario(scenario);
    const context = scenario.context;
    const a = scenario.assumptions;
    const moneyDecimals = context.monetary_decimals;
    const ratioDecimals = context.ratio_decimals;
    const scoreDecimals = context.score_decimals;
    const netCapitalCost = Math.max(0, a.capital_cost - a.external_funding);
    const carbonValue = a.annual_emissions_reduced_tons === null ? 0 : a.annual_emissions_reduced_tons * a.carbon_price_per_ton;
    const netAnnualBenefit = a.annual_savings + carbonValue - a.annual_operating_cost;
    const pvBenefits = presentValueAnnuity(netAnnualBenefit, a.time_horizon_years, a.discount_rate_percent);
    const npv = pvBenefits - netCapitalCost;
    const payback = netAnnualBenefit <= 0 ? null : netCapitalCost / netAnnualBenefit;
    const roi = netCapitalCost === 0 ? null : (((netAnnualBenefit * a.time_horizon_years) - netCapitalCost) / netCapitalCost) * 100;
    const bcr = netCapitalCost === 0 ? null : pvBenefits / netCapitalCost;
    const lifetimeTons = a.annual_emissions_reduced_tons === null ? null : a.annual_emissions_reduced_tons * a.time_horizon_years;
    const carbonCost = lifetimeTons === null || lifetimeTons <= 0 ? null : netCapitalCost / lifetimeTons;
    const components = scoreComponents(npv, payback, netCapitalCost, netAnnualBenefit, a.time_horizon_years, a.confidence_percent, a.implementation_risk_percent, scoreDecimals);
    const totalScore = components.reduce((sum, component) => sum + component.raw_score * component.weight, 0);
    const results = {
      net_capital_cost: roundHalfUp(netCapitalCost, moneyDecimals),
      carbon_value_per_year: roundHalfUp(carbonValue, moneyDecimals),
      net_annual_benefit: roundHalfUp(netAnnualBenefit, moneyDecimals),
      present_value_benefits: roundHalfUp(pvBenefits, moneyDecimals),
      npv: roundHalfUp(npv, moneyDecimals),
      payback_years: payback === null ? null : roundHalfUp(payback, ratioDecimals),
      roi_percent: roi === null ? null : roundHalfUp(roi, ratioDecimals),
      benefit_cost_ratio: bcr === null ? null : roundHalfUp(bcr, ratioDecimals),
      carbon_cost_per_ton: carbonCost === null ? null : roundHalfUp(carbonCost, moneyDecimals),
      risk_adjusted_score: roundHalfUp(totalScore, scoreDecimals),
      score_components: components
    };
    const flags = [];
    if (results.npv < 0) flags.push('Negative NPV under current assumptions');
    if (results.net_annual_benefit <= 0) flags.push('No payback because net annual benefit is non-positive');
    else if (results.payback_years !== null && results.payback_years > a.time_horizon_years) flags.push('Payback exceeds selected time horizon');
    if (a.confidence_percent < 60) flags.push('Evidence confidence is below review threshold');
    if (a.implementation_risk_percent > 60) flags.push('Implementation risk is high');
    if (a.discount_rate_percent < 0) flags.push('Negative discount rate requires explicit review');
    else if (a.discount_rate_percent > 20) flags.push('Discount rate exceeds the screening review range');
    if (a.external_funding > a.capital_cost) flags.push('External funding exceeds capital cost; net capital cost is floored at zero');
    if (a.annual_emissions_reduced_tons === null) flags.push('Emissions data not provided; carbon value is excluded');
    if (a.time_horizon_years !== Math.floor(a.time_horizon_years)) flags.push('Fractional horizon uses a prorated final period');
    if (!flags.length) flags.push('No major screening flags under current assumptions');
    let riskLevel = 'High concern';
    if (results.risk_adjusted_score >= 70) riskLevel = 'Lower concern';
    else if (results.risk_adjusted_score >= 45) riskLevel = 'Moderate concern';
    let decisionNote = 'Current assumptions do not support a strong financial case; revisit costs, benefits, risks, timing, or alternatives.';
    if (results.npv > 0 && results.risk_adjusted_score >= 60) decisionNote = 'Current assumptions support further review; validate inputs and alternatives before making a decision.';
    else if (results.npv > 0) decisionNote = 'The financial signal is positive, but disclosed risk or evidence concerns require deeper review.';
    return {
      contract_version: CONTRACT_VERSION,
      model_id: MODEL_ID,
      project: scenario.project,
      context: scenario.context,
      assumptions: scenario.assumptions,
      results: results,
      interpretation: { risk_level: riskLevel, flags: flags },
      narrative: { decision_note: decisionNote, review_boundary: REVIEW_BOUNDARY },
      methodology: {
        model_id: MODEL_ID, model_version: '1.4.0', calculation_basis: 'annual_screening',
        fractional_horizon_policy: 'prorated_final_period', overfunding_policy: 'net_capital_cost_floor_zero',
        zero_cost_ratio_policy: 'undefined_null', missing_emissions_policy: 'exclude_carbon_value',
        score_policy: 'transparent_weighted_components'
      },
      metadata: {
        generated_at: generatedAt || new Date().toISOString(),
        tool: 'Catalyst Finance scenario engine', version: CONTRACT_VERSION,
        disclaimer: DISCLAIMER, migration: normalized.migration
      }
    };
  }

  return {
    CONTRACT_VERSION: CONTRACT_VERSION,
    MODEL_ID: MODEL_ID,
    defaultContext: defaultContext,
    evaluate: evaluate,
    migrateLegacy: migrateLegacy,
    migrateV110: migrateV110,
    migrateV120: migrateV120,
    migrateV130: migrateV130,
    presentValueAnnuity: presentValueAnnuity,
    roundHalfUp: roundHalfUp
  };
});
