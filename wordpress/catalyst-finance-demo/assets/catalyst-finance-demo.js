(function () {
  'use strict';
  function money(value, currency) {
    if (value === null || !Number.isFinite(value)) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency, maximumFractionDigits: 0 }).format(value);
  }
  function pct(value) {
    if (value === null || !Number.isFinite(value)) return '—';
    return value.toFixed(1) + '%';
  }
  function num(form, name) {
    const field = form.elements[name];
    return field ? Number(field.value || 0) : 0;
  }
  function inputFromForm(form) {
    return {
      contract_version: '1.1.0',
      model_id: 'catalyst-finance.screening',
      project: {
        name: (form.elements.projectName.value || 'Untitled initiative').trim(),
        category: (form.elements.category.value || 'Sustainability finance').trim()
      },
      context: CatalystFinanceEngine.defaultContext(),
      assumptions: {
        capital_cost: num(form, 'capitalCost'),
        external_funding: num(form, 'externalFunding'),
        annual_savings: num(form, 'annualSavings'),
        annual_operating_cost: num(form, 'annualOperatingCost'),
        time_horizon_years: num(form, 'timeHorizon'),
        discount_rate_percent: num(form, 'discountRate'),
        annual_emissions_reduced_tons: num(form, 'annualEmissions'),
        carbon_price_per_ton: num(form, 'carbonPrice'),
        confidence_percent: num(form, 'confidence'),
        implementation_risk_percent: num(form, 'implementationRisk')
      }
    };
  }
  function cumulativeSeries(payload) {
    const series = [];
    let running = -payload.results.net_capital_cost;
    series.push({ year: 0, value: running });
    const horizon = Math.max(1, Math.ceil(payload.assumptions.time_horizon_years));
    for (let year = 1; year <= horizon; year += 1) {
      const fraction = Math.min(1, payload.assumptions.time_horizon_years - (year - 1));
      running += payload.results.net_annual_benefit * Math.max(0, fraction);
      series.push({ year: year, value: running });
    }
    return series;
  }
  function drawChart(canvas, series, currency) {
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
    const pad = 36;
    const values = series.map(point => point.value);
    let min = Math.min.apply(null, values.concat([0]));
    let max = Math.max.apply(null, values.concat([0]));
    if (min === max) { min -= 1; max += 1; }
    const x = index => pad + (index / Math.max(1, series.length - 1)) * (w - pad * 2);
    const y = value => h - pad - ((value - min) / (max - min)) * (h - pad * 2);
    ctx.strokeStyle = '#d9d2c4';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, y(0));
    ctx.lineTo(w - pad, y(0));
    ctx.stroke();
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.beginPath();
    series.forEach((point, index) => index === 0 ? ctx.moveTo(x(index), y(point.value)) : ctx.lineTo(x(index), y(point.value)));
    ctx.stroke();
    ctx.fillStyle = '#9b1111';
    series.forEach((point, index) => {
      ctx.beginPath();
      ctx.arc(x(index), y(point.value), 3, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.fillStyle = '#555555';
    ctx.font = '12px sans-serif';
    ctx.fillText('Cumulative undiscounted cash flow', pad, 18);
    ctx.fillText(money(max, currency), pad, pad - 8);
    ctx.fillText(money(min, currency), pad, h - 10);
  }
  function update(root) {
    const form = root.querySelector('[data-scfin-form]');
    const payload = CatalystFinanceEngine.evaluate(inputFromForm(form));
    const currency = payload.context.currency;
    root.querySelector('[data-scfin-confidence-label]').textContent = payload.assumptions.confidence_percent;
    root.querySelector('[data-scfin-risk-label]').textContent = payload.assumptions.implementation_risk_percent;
    root.querySelector('[data-scfin-npv]').textContent = money(payload.results.npv, currency);
    root.querySelector('[data-scfin-payback]').textContent = payload.results.payback_years === null ? '—' : payload.results.payback_years + ' yrs';
    root.querySelector('[data-scfin-roi]').textContent = pct(payload.results.roi_percent);
    root.querySelector('[data-scfin-score]').textContent = payload.results.risk_adjusted_score + '/100';
    root.querySelector('[data-scfin-level]').textContent = payload.interpretation.risk_level;
    root.querySelector('[data-scfin-note]').textContent = payload.narrative.decision_note;
    const flags = root.querySelector('[data-scfin-flags]');
    flags.innerHTML = '';
    payload.interpretation.flags.forEach(flag => {
      const li = document.createElement('li');
      li.textContent = flag;
      flags.appendChild(li);
    });
    const score = root.querySelector('[data-scfin-score-trace]');
    score.innerHTML = '';
    payload.results.score_components.forEach(component => {
      const li = document.createElement('li');
      li.textContent = component.label + ': ' + component.raw_score + ' × ' + Math.round(component.weight * 100) + '% = ' + component.weighted_contribution;
      score.appendChild(li);
    });
    root.querySelector('[data-scfin-json]').textContent = JSON.stringify(payload, null, 2);
    root._scfinPayload = payload;
    drawChart(root.querySelector('[data-scfin-chart]'), cumulativeSeries(payload), currency);
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-scfin-demo]').forEach(root => {
      const form = root.querySelector('[data-scfin-form]');
      form.addEventListener('input', () => update(root));
      root.querySelector('[data-scfin-copy]').addEventListener('click', () => {
        const text = JSON.stringify(root._scfinPayload || CatalystFinanceEngine.evaluate(inputFromForm(form)), null, 2);
        if (navigator.clipboard) navigator.clipboard.writeText(text);
      });
      root.querySelector('[data-scfin-download]').addEventListener('click', () => {
        const text = JSON.stringify(root._scfinPayload || CatalystFinanceEngine.evaluate(inputFromForm(form)), null, 2);
        const blob = new Blob([text], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'catalyst-finance-scenario-v1.1.0.json';
        link.click();
        URL.revokeObjectURL(link.href);
      });
      root.querySelector('[data-scfin-print]').addEventListener('click', () => window.print());
      update(root);
    });
  });
})();
