(function () {
  function money(value) {
    if (!isFinite(value)) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
  }
  function pct(value) {
    if (!isFinite(value)) return '—';
    return value.toFixed(1) + '%';
  }
  function num(form, name) {
    const field = form.elements[name];
    return field ? Number(field.value || 0) : 0;
  }
  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }
  function pvAnnuity(annual, years, discountRate) {
    const n = Math.max(0, Math.round(years));
    const r = discountRate / 100;
    let total = 0;
    for (let y = 1; y <= n; y++) total += annual / Math.pow(1 + r, y);
    return total;
  }
  function evaluate(form) {
    const projectName = (form.elements.projectName.value || 'Untitled initiative').trim();
    const category = (form.elements.category.value || 'Sustainability finance').trim();
    const capitalCost = num(form, 'capitalCost');
    const externalFunding = num(form, 'externalFunding');
    const annualSavings = num(form, 'annualSavings');
    const annualOperatingCost = num(form, 'annualOperatingCost');
    const timeHorizon = num(form, 'timeHorizon');
    const discountRate = num(form, 'discountRate');
    const annualEmissions = num(form, 'annualEmissions');
    const carbonPrice = num(form, 'carbonPrice');
    const confidence = clamp(num(form, 'confidence'), 0, 100);
    const implementationRisk = clamp(num(form, 'implementationRisk'), 0, 100);
    const netCapitalCost = Math.max(0, capitalCost - externalFunding);
    const carbonValue = annualEmissions * carbonPrice;
    const netAnnualBenefit = annualSavings + carbonValue - annualOperatingCost;
    const presentValueBenefits = pvAnnuity(netAnnualBenefit, timeHorizon, discountRate);
    const npv = presentValueBenefits - netCapitalCost;
    const paybackYears = netAnnualBenefit > 0 ? netCapitalCost / netAnnualBenefit : null;
    const roiPercent = netCapitalCost > 0 ? (((netAnnualBenefit * timeHorizon) - netCapitalCost) / netCapitalCost) * 100 : 0;
    const benefitCostRatio = netCapitalCost > 0 ? presentValueBenefits / netCapitalCost : null;
    const lifetimeTons = annualEmissions * timeHorizon;
    const carbonCostPerTon = lifetimeTons > 0 ? netCapitalCost / lifetimeTons : null;
    let npvSignal = npv > 0 ? 60 : 30;
    let paybackSignal = 50;
    if (paybackYears !== null) {
      if (paybackYears <= 3) paybackSignal = 75;
      else if (paybackYears <= timeHorizon) paybackSignal = 60;
      else paybackSignal = 35;
    }
    const riskAdjustedScore = clamp((npvSignal * 0.35) + (paybackSignal * 0.25) + (confidence * 0.25) - (implementationRisk * 0.25) + 20, 0, 100);
    const flags = [];
    if (npv < 0) flags.push('Negative NPV under current assumptions.');
    if (paybackYears === null) flags.push('No payback because net annual benefit is non-positive.');
    else if (paybackYears > timeHorizon) flags.push('Payback exceeds the selected time horizon.');
    if (confidence < 60) flags.push('Evidence confidence is below review threshold.');
    if (implementationRisk > 60) flags.push('Implementation risk is high.');
    if (discountRate < 0 || discountRate > 20) flags.push('Discount rate needs review.');
    if (!flags.length) flags.push('No major screening flags under current assumptions.');
    let riskLevel = 'High concern';
    if (riskAdjustedScore >= 70) riskLevel = 'Lower concern';
    else if (riskAdjustedScore >= 45) riskLevel = 'Moderate concern';
    let decisionNote = 'Current assumptions do not support a strong financial case; revisit costs, benefits, risks, or alternatives.';
    if (npv > 0 && riskAdjustedScore >= 60) decisionNote = 'Current assumptions support further review; validate inputs before making a decision.';
    else if (npv > 0) decisionNote = 'Financial signal is positive, but risk or confidence concerns require deeper review.';
    const cumulative = [];
    let running = -netCapitalCost;
    cumulative.push({ year: 0, value: running });
    for (let y = 1; y <= Math.max(1, Math.round(timeHorizon)); y++) {
      running += netAnnualBenefit;
      cumulative.push({ year: y, value: running });
    }
    return {
      project: { name: projectName, category: category },
      inputs: { capital_cost: capitalCost, external_funding: externalFunding, annual_savings: annualSavings, annual_operating_cost: annualOperatingCost, time_horizon_years: timeHorizon, discount_rate_percent: discountRate, annual_emissions_reduced_tons: annualEmissions, carbon_price_per_ton: carbonPrice, confidence_percent: confidence, implementation_risk_percent: implementationRisk },
      results: { net_capital_cost: Math.round(netCapitalCost), net_annual_benefit: Math.round(netAnnualBenefit), present_value_benefits: Math.round(presentValueBenefits), npv: Math.round(npv), payback_years: paybackYears === null ? null : Number(paybackYears.toFixed(2)), roi_percent: Number(roiPercent.toFixed(1)), benefit_cost_ratio: benefitCostRatio === null ? null : Number(benefitCostRatio.toFixed(2)), carbon_cost_per_ton: carbonCostPerTon === null ? null : Number(carbonCostPerTon.toFixed(2)), risk_adjusted_score: Number(riskAdjustedScore.toFixed(1)) },
      interpretation: { risk_level: riskLevel, flags: flags, decision_note: decisionNote },
      series: cumulative,
      metadata: { generated_at: new Date().toISOString(), tool: 'Catalyst Finance Demo', version: '1.0.1', disclaimer: 'Educational scenario tool only; not financial, investment, tax, accounting, legal, assurance, or fiduciary advice.' }
    };
  }
  function drawChart(canvas, series) {
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
    const pad = 36;
    const values = series.map(p => p.value);
    let min = Math.min.apply(null, values.concat([0]));
    let max = Math.max.apply(null, values.concat([0]));
    if (min === max) { min -= 1; max += 1; }
    const x = i => pad + (i / Math.max(1, series.length - 1)) * (w - pad * 2);
    const y = v => h - pad - ((v - min) / (max - min)) * (h - pad * 2);
    ctx.strokeStyle = '#d9d2c4';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, y(0));
    ctx.lineTo(w - pad, y(0));
    ctx.stroke();
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.beginPath();
    series.forEach((p, i) => {
      if (i === 0) ctx.moveTo(x(i), y(p.value));
      else ctx.lineTo(x(i), y(p.value));
    });
    ctx.stroke();
    ctx.fillStyle = '#9b1111';
    series.forEach((p, i) => {
      ctx.beginPath();
      ctx.arc(x(i), y(p.value), 3, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.fillStyle = '#555555';
    ctx.font = '12px sans-serif';
    ctx.fillText('Cumulative cash flow', pad, 18);
    ctx.fillText(money(max), pad, pad - 8);
    ctx.fillText(money(min), pad, h - 10);
  }
  function update(root) {
    const form = root.querySelector('[data-scfin-form]');
    const payload = evaluate(form);
    root.querySelector('[data-scfin-confidence-label]').textContent = payload.inputs.confidence_percent;
    root.querySelector('[data-scfin-risk-label]').textContent = payload.inputs.implementation_risk_percent;
    root.querySelector('[data-scfin-npv]').textContent = money(payload.results.npv);
    root.querySelector('[data-scfin-payback]').textContent = payload.results.payback_years === null ? '—' : payload.results.payback_years + ' yrs';
    root.querySelector('[data-scfin-roi]').textContent = pct(payload.results.roi_percent);
    root.querySelector('[data-scfin-score]').textContent = payload.results.risk_adjusted_score + '/100';
    root.querySelector('[data-scfin-level]').textContent = payload.interpretation.risk_level;
    root.querySelector('[data-scfin-note]').textContent = payload.interpretation.decision_note;
    const flags = root.querySelector('[data-scfin-flags]');
    flags.innerHTML = '';
    payload.interpretation.flags.forEach(flag => {
      const li = document.createElement('li');
      li.textContent = flag;
      flags.appendChild(li);
    });
    root.querySelector('[data-scfin-json]').textContent = JSON.stringify(payload, null, 2);
    root._scfinPayload = payload;
    drawChart(root.querySelector('[data-scfin-chart]'), payload.series);
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-scfin-demo]').forEach(root => {
      const form = root.querySelector('[data-scfin-form]');
      form.addEventListener('input', () => update(root));
      root.querySelector('[data-scfin-copy]').addEventListener('click', () => {
        const text = JSON.stringify(root._scfinPayload || evaluate(form), null, 2);
        navigator.clipboard && navigator.clipboard.writeText(text);
      });
      root.querySelector('[data-scfin-download]').addEventListener('click', () => {
        const text = JSON.stringify(root._scfinPayload || evaluate(form), null, 2);
        const blob = new Blob([text], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'catalyst-finance-scenario.json';
        a.click();
        URL.revokeObjectURL(a.href);
      });
      root.querySelector('[data-scfin-print]').addEventListener('click', () => window.print());
      update(root);
    });
  });
})();
