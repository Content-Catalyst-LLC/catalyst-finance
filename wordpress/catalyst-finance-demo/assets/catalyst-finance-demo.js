(function () {
  'use strict';

  const WORKSPACE_VERSION = '2.0.0';
  const STORAGE_PREFIX = 'catalyst-finance-workspace-v2.0.0';

  const TEMPLATES = {
    'capital-project': {
      name: 'Capital project', category: 'Capital project', capitalCost: 250000,
      externalFunding: 0, annualSavings: 50000, annualOperatingCost: 5000,
      timeHorizon: 10, discountRate: 6, annualEmissions: 0, carbonPrice: 0,
      confidence: 60, implementationRisk: 40
    },
    'operating-change': {
      name: 'Operating change', category: 'Operating change', capitalCost: 50000,
      externalFunding: 0, annualSavings: 24000, annualOperatingCost: 6000,
      timeHorizon: 5, discountRate: 6, annualEmissions: 0, carbonPrice: 0,
      confidence: 65, implementationRisk: 35
    },
    'pricing-decision': {
      name: 'Pricing decision', category: 'Pricing and revenue', capitalCost: 20000,
      externalFunding: 0, annualSavings: 40000, annualOperatingCost: 10000,
      timeHorizon: 3, discountRate: 8, annualEmissions: 0, carbonPrice: 0,
      confidence: 50, implementationRisk: 50
    },
    'sustainability-investment': {
      name: 'Sustainability investment', category: 'Sustainability investment', capitalCost: 300000,
      externalFunding: 50000, annualSavings: 55000, annualOperatingCost: 8000,
      timeHorizon: 12, discountRate: 5, annualEmissions: 220, carbonPrice: 40,
      confidence: 70, implementationRisk: 30
    },
    'public-value-initiative': {
      name: 'Public-value initiative', category: 'Public value', capitalCost: 180000,
      externalFunding: 90000, annualSavings: 18000, annualOperatingCost: 12000,
      timeHorizon: 8, discountRate: 3, annualEmissions: 80, carbonPrice: 50,
      confidence: 55, implementationRisk: 45
    }
  };

  function now() { return new Date().toISOString(); }
  function newId(prefix) {
    if (window.crypto && window.crypto.randomUUID) return prefix + '_' + window.crypto.randomUUID().replace(/-/g, '');
    return prefix + '_' + Date.now().toString(36) + Math.random().toString(36).slice(2);
  }
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
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
  function tags(form) {
    return String(form.elements.tags.value || '').split(',').map(value => value.trim()).filter(Boolean);
  }
  function inputFromForm(form, currency) {
    const emissions = String(form.elements.annualEmissions.value).trim();
    return {
      contract_version: WORKSPACE_VERSION,
      model_id: 'catalyst-finance.screening',
      project: {
        name: (form.elements.projectName.value || 'Untitled initiative').trim(),
        category: (form.elements.category.value || 'Sustainability finance').trim()
      },
      context: Object.assign(CatalystFinanceEngine.defaultContext(), { currency: currency || 'USD' }),
      assumptions: {
        capital_cost: num(form, 'capitalCost'),
        external_funding: num(form, 'externalFunding'),
        annual_savings: num(form, 'annualSavings'),
        annual_operating_cost: num(form, 'annualOperatingCost'),
        time_horizon_years: num(form, 'timeHorizon'),
        discount_rate_percent: num(form, 'discountRate'),
        annual_emissions_reduced_tons: emissions === '' ? null : Number(emissions),
        carbon_price_per_ton: num(form, 'carbonPrice'),
        confidence_percent: num(form, 'confidence'),
        implementation_risk_percent: num(form, 'implementationRisk')
      }
    };
  }
  function populateForm(form, scenario, record) {
    const a = scenario.assumptions;
    form.elements.projectName.value = scenario.project.name;
    form.elements.category.value = scenario.project.category;
    form.elements.alternativeLabel.value = record ? record.alternative_label : 'Base';
    form.elements.capitalCost.value = a.capital_cost;
    form.elements.externalFunding.value = a.external_funding;
    form.elements.annualSavings.value = a.annual_savings;
    form.elements.annualOperatingCost.value = a.annual_operating_cost;
    form.elements.timeHorizon.value = a.time_horizon_years;
    form.elements.discountRate.value = a.discount_rate_percent;
    form.elements.annualEmissions.value = a.annual_emissions_reduced_tons === null ? '' : a.annual_emissions_reduced_tons;
    form.elements.carbonPrice.value = a.carbon_price_per_ton;
    form.elements.confidence.value = a.confidence_percent;
    form.elements.implementationRisk.value = a.implementation_risk_percent;
    form.elements.tags.value = record ? record.tags.join(', ') : '';
    form.elements.notes.value = record ? record.notes : '';
  }
  function scenarioFromTemplate(templateId, name, currency) {
    const template = TEMPLATES[templateId] || TEMPLATES['capital-project'];
    const fake = document.createElement('form');
    fake.innerHTML = [
      '<input name="projectName"><input name="category"><input name="capitalCost">',
      '<input name="externalFunding"><input name="annualSavings"><input name="annualOperatingCost">',
      '<input name="timeHorizon"><input name="discountRate"><input name="annualEmissions">',
      '<input name="carbonPrice"><input name="confidence"><input name="implementationRisk">',
      '<input name="tags"><input name="notes"><input name="alternativeLabel">'
    ].join('');
    fake.elements.projectName.value = name || template.name;
    fake.elements.category.value = template.category;
    Object.keys(template).forEach(key => { if (fake.elements[key]) fake.elements[key].value = template[key]; });
    return inputFromForm(fake, currency);
  }
  function revision(scenario, number, note) {
    return {
      revision_id: newId('revision'), revision_number: number, created_at: now(),
      model_id: 'catalyst-finance.screening', model_version: WORKSPACE_VERSION,
      change_note: note || '', scenario: clone(scenario)
    };
  }
  function scenarioRecord(name, scenario, templateId) {
    const first = revision(scenario, 1, 'Initial scenario');
    const timestamp = now();
    return {
      scenario_id: newId('scenario'), project_id: null, name: name,
      alternative_label: 'Base', status: 'active', template_id: templateId,
      notes: '', tags: [], created_at: timestamp, updated_at: timestamp,
      archived_at: null, current_revision_id: first.revision_id, revisions: [first]
    };
  }
  function defaultWorkspace() {
    const timestamp = now();
    const scenario = scenarioFromTemplate('sustainability-investment', 'Building efficiency retrofit', 'USD');
    return {
      workspace_contract_version: WORKSPACE_VERSION,
      workspace_id: newId('workspace'), name: 'My finance workspace', description: '', status: 'active',
      defaults: {
        currency: 'USD', locale: 'en-US', time_basis: 'end_of_period', price_basis: 'nominal',
        discount_rate_basis: 'nominal', default_model_id: 'catalyst-finance.screening',
        default_model_version: WORKSPACE_VERSION
      },
      created_at: timestamp, updated_at: timestamp, projects: [],
      scenarios: [scenarioRecord('Building efficiency retrofit', scenario, 'sustainability-investment')]
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
    const w = canvas.width; const h = canvas.height;
    ctx.clearRect(0, 0, w, h); ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, w, h);
    const pad = 36; const values = series.map(point => point.value);
    let min = Math.min.apply(null, values.concat([0])); let max = Math.max.apply(null, values.concat([0]));
    if (min === max) { min -= 1; max += 1; }
    const x = index => pad + (index / Math.max(1, series.length - 1)) * (w - pad * 2);
    const y = value => h - pad - ((value - min) / (max - min)) * (h - pad * 2);
    ctx.strokeStyle = '#d9d2c4'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad, y(0)); ctx.lineTo(w - pad, y(0)); ctx.stroke();
    ctx.strokeStyle = '#000000'; ctx.lineWidth = 2; ctx.beginPath();
    series.forEach((point, index) => index === 0 ? ctx.moveTo(x(index), y(point.value)) : ctx.lineTo(x(index), y(point.value))); ctx.stroke();
    ctx.fillStyle = '#9b1111'; series.forEach((point, index) => { ctx.beginPath(); ctx.arc(x(index), y(point.value), 3, 0, Math.PI * 2); ctx.fill(); });
    ctx.fillStyle = '#555555'; ctx.font = '12px sans-serif'; ctx.fillText('Cumulative undiscounted cash flow', pad, 18);
    ctx.fillText(money(max, currency), pad, pad - 8); ctx.fillText(money(min, currency), pad, h - 10);
  }
  function downloadJson(filename, payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2) + '\n'], { type: 'application/json' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = filename; link.click(); URL.revokeObjectURL(link.href);
  }
  function currentRecord(state) {
    return state.workspace.scenarios.find(item => item.scenario_id === state.currentScenarioId) || state.workspace.scenarios[0];
  }
  function currentScenario(state) {
    const record = currentRecord(state);
    return record.revisions[record.revisions.length - 1].scenario;
  }
  function renderScenarioSelect(root, state) {
    const select = root.querySelector('[data-scfin-scenario-select]');
    if (!select) return;
    select.innerHTML = '';
    state.workspace.scenarios.forEach(record => {
      const option = document.createElement('option'); option.value = record.scenario_id;
      option.textContent = record.name + (record.status === 'archived' ? ' [Archived]' : '') + ' · r' + record.revisions.length;
      option.selected = record.scenario_id === state.currentScenarioId; select.appendChild(option);
    });
  }
  function updateOutput(root, scenario) {
    const payload = CatalystFinanceEngine.evaluate(scenario);
    const currency = payload.context.currency;
    root.querySelector('[data-scfin-confidence-label]').textContent = payload.assumptions.confidence_percent;
    root.querySelector('[data-scfin-risk-label]').textContent = payload.assumptions.implementation_risk_percent;
    root.querySelector('[data-scfin-npv]').textContent = money(payload.results.npv, currency);
    root.querySelector('[data-scfin-payback]').textContent = payload.results.payback_years === null ? '—' : payload.results.payback_years + ' yrs';
    root.querySelector('[data-scfin-roi]').textContent = pct(payload.results.roi_percent);
    root.querySelector('[data-scfin-score]').textContent = payload.results.risk_adjusted_score + '/100';
    root.querySelector('[data-scfin-level]').textContent = payload.interpretation.risk_level;
    root.querySelector('[data-scfin-note]').textContent = payload.narrative.decision_note;
    const flags = root.querySelector('[data-scfin-flags]'); flags.innerHTML = '';
    payload.interpretation.flags.forEach(flag => { const li = document.createElement('li'); li.textContent = flag; flags.appendChild(li); });
    const score = root.querySelector('[data-scfin-score-trace]'); score.innerHTML = '';
    payload.results.score_components.forEach(component => {
      const li = document.createElement('li');
      li.textContent = component.label + ': ' + component.raw_score + ' × ' + Math.round(component.weight * 100) + '% = ' + component.weighted_contribution;
      score.appendChild(li);
    });
    root.querySelector('[data-scfin-json]').textContent = JSON.stringify(payload, null, 2);
    root._scfinPayload = payload;
    drawChart(root.querySelector('[data-scfin-chart]'), cumulativeSeries(payload), currency);
  }
  function storageKeys(index) {
    const suffix = window.location.pathname.replace(/[^a-z0-9]/gi, '_') + '_' + index;
    return { canonical: STORAGE_PREFIX + ':' + suffix, recovery: STORAGE_PREFIX + ':recovery:' + suffix };
  }
  function loadWorkspace(keys) {
    try {
      const recovery = JSON.parse(localStorage.getItem(keys.recovery) || 'null');
      const canonical = JSON.parse(localStorage.getItem(keys.canonical) || 'null');
      if (recovery && (!canonical || recovery.updated_at >= canonical.updated_at)) return { workspace: recovery, recovered: true };
      if (canonical) return { workspace: canonical, recovered: false };
    } catch (error) { console.warn('Catalyst Finance workspace recovery failed.', error); }
    return { workspace: defaultWorkspace(), recovered: false };
  }
  function validateWorkspace(workspace) {
    if (!workspace || workspace.workspace_contract_version !== WORKSPACE_VERSION) throw new Error('Workspace contract_version must be 2.0.0.');
    if (!workspace.workspace_id || !Array.isArray(workspace.scenarios)) throw new Error('Workspace ID and scenarios are required.');
    const scenarioIds = new Set();
    workspace.scenarios.forEach(record => {
      if (scenarioIds.has(record.scenario_id)) throw new Error('Scenario IDs must be unique.');
      scenarioIds.add(record.scenario_id);
      if (!record.revisions || !record.revisions.length) throw new Error('Every scenario requires revision history.');
      const latest = record.revisions[record.revisions.length - 1];
      if (latest.revision_id !== record.current_revision_id) throw new Error('Current revision ID must reference the latest revision.');
    });
    return workspace;
  }
  function initializeWorkspace(root, index) {
    const form = root.querySelector('[data-scfin-form]');
    const mode = root.getAttribute('data-scfin-mode');
    if (mode === 'public') {
      Array.from(form.elements).forEach(field => {
        if (field.tagName !== 'BUTTON') field.disabled = true;
      });
      updateOutput(root, inputFromForm(form, 'USD'));
      root.querySelector('[data-scfin-copy]').addEventListener('click', function () {
        const text = JSON.stringify(root._scfinPayload, null, 2);
        if (navigator.clipboard) navigator.clipboard.writeText(text);
      });
      root.querySelector('[data-scfin-download]').addEventListener('click', function () {
        downloadJson('catalyst-finance-scenario-v2.0.0.json', root._scfinPayload);
      });
      root.querySelector('[data-scfin-print]').addEventListener('click', function () { window.print(); });
      return;
    }

    const keys = storageKeys(index);
    const loaded = loadWorkspace(keys);
    const state = { workspace: validateWorkspace(loaded.workspace), currentScenarioId: loaded.workspace.scenarios[0].scenario_id, dirty: loaded.recovered, timer: null };
    const status = root.querySelector('[data-scfin-save-status]');
    root.querySelector('[data-scfin-workspace-name]').value = state.workspace.name;

    function setStatus(text, kind) {
      status.textContent = text; status.setAttribute('data-status', kind || 'saved');
    }
    function persistCanonical() {
      state.workspace.updated_at = now(); localStorage.setItem(keys.canonical, JSON.stringify(state.workspace)); localStorage.removeItem(keys.recovery);
      state.dirty = false; setStatus('Saved locally', 'saved'); renderScenarioSelect(root, state);
    }
    function scheduleAutosave() {
      state.dirty = true; setStatus('Unsaved changes · autosaving', 'dirty');
      window.clearTimeout(state.timer);
      state.timer = window.setTimeout(function () {
        const record = currentRecord(state); const scenario = inputFromForm(form, state.workspace.defaults.currency);
        const draft = clone(state.workspace); const target = draft.scenarios.find(item => item.scenario_id === record.scenario_id);
        target.name = scenario.project.name; target.alternative_label = form.elements.alternativeLabel.value || 'Base';
        target.notes = form.elements.notes.value || ''; target.tags = tags(form); target.updated_at = now();
        const next = revision(scenario, target.revisions.length + 1, 'Recovered autosave');
        target.revisions.push(next); target.current_revision_id = next.revision_id; draft.updated_at = now();
        localStorage.setItem(keys.recovery, JSON.stringify(draft)); setStatus('Autosaved recovery copy', 'recovery');
      }, 350);
    }
    function loadCurrent() {
      const record = currentRecord(state); if (!record) return;
      state.currentScenarioId = record.scenario_id; populateForm(form, currentScenario(state), record);
      renderScenarioSelect(root, state); updateOutput(root, currentScenario(state));
      root.querySelector('[data-scfin-archive]').disabled = record.status === 'archived';
      root.querySelector('[data-scfin-restore]').disabled = record.status !== 'archived';
    }
    function saveRevision(note) {
      const record = currentRecord(state); const scenario = inputFromForm(form, state.workspace.defaults.currency);
      record.name = scenario.project.name; record.alternative_label = form.elements.alternativeLabel.value || 'Base';
      record.notes = form.elements.notes.value || ''; record.tags = tags(form); record.updated_at = now();
      const next = revision(scenario, record.revisions.length + 1, note || 'Saved revision');
      record.revisions.push(next); record.current_revision_id = next.revision_id; persistCanonical(); updateOutput(root, scenario);
    }

    form.addEventListener('input', function () { updateOutput(root, inputFromForm(form, state.workspace.defaults.currency)); scheduleAutosave(); });
    root.querySelector('[data-scfin-workspace-name]').addEventListener('input', function (event) {
      state.workspace.name = event.target.value || 'Untitled workspace'; scheduleAutosave();
    });
    root.querySelector('[data-scfin-scenario-select]').addEventListener('change', function (event) {
      if (state.dirty && !window.confirm('Switch scenarios and discard the current unsaved form changes?')) { event.target.value = state.currentScenarioId; return; }
      localStorage.removeItem(keys.recovery); state.dirty = false; state.currentScenarioId = event.target.value; loadCurrent(); setStatus('Saved locally', 'saved');
    });
    root.querySelector('[data-scfin-save]').addEventListener('click', function () { saveRevision('Explicit browser save'); });
    root.querySelector('[data-scfin-new]').addEventListener('click', function () {
      const templateId = root.querySelector('[data-scfin-template-select]').value;
      const template = TEMPLATES[templateId]; const name = window.prompt('Scenario name', template.name);
      if (!name) return;
      const record = scenarioRecord(name, scenarioFromTemplate(templateId, name, state.workspace.defaults.currency), templateId);
      state.workspace.scenarios.push(record); state.currentScenarioId = record.scenario_id; persistCanonical(); loadCurrent();
    });
    root.querySelector('[data-scfin-duplicate]').addEventListener('click', function () {
      const source = currentRecord(state); const name = window.prompt('Duplicate scenario name', source.name + ' copy'); if (!name) return;
      const copy = clone(source); copy.scenario_id = newId('scenario'); copy.name = name; copy.created_at = now(); copy.updated_at = copy.created_at;
      const first = revision(source.revisions[source.revisions.length - 1].scenario, 1, 'Duplicated from ' + source.scenario_id);
      copy.revisions = [first]; copy.current_revision_id = first.revision_id; copy.status = 'active'; copy.archived_at = null;
      state.workspace.scenarios.push(copy); state.currentScenarioId = copy.scenario_id; persistCanonical(); loadCurrent();
    });
    root.querySelector('[data-scfin-rename]').addEventListener('click', function () {
      const record = currentRecord(state); const name = window.prompt('Scenario name', record.name); if (!name) return;
      record.name = name; record.updated_at = now(); form.elements.projectName.value = name; persistCanonical(); updateOutput(root, inputFromForm(form, state.workspace.defaults.currency));
    });
    root.querySelector('[data-scfin-archive]').addEventListener('click', function () {
      const record = currentRecord(state); record.status = 'archived'; record.archived_at = now(); record.updated_at = record.archived_at; persistCanonical(); loadCurrent();
    });
    root.querySelector('[data-scfin-restore]').addEventListener('click', function () {
      const record = currentRecord(state); record.status = 'active'; record.archived_at = null; record.updated_at = now(); persistCanonical(); loadCurrent();
    });
    root.querySelector('[data-scfin-delete]').addEventListener('click', function () {
      if (state.workspace.scenarios.length <= 1) { window.alert('A workspace must retain at least one browser scenario.'); return; }
      const record = currentRecord(state); if (!window.confirm('Delete “' + record.name + '”? This cannot be undone unless you exported the workspace.')) return;
      state.workspace.scenarios = state.workspace.scenarios.filter(item => item.scenario_id !== record.scenario_id);
      state.currentScenarioId = state.workspace.scenarios[0].scenario_id; persistCanonical(); loadCurrent();
    });
    root.querySelector('[data-scfin-export-workspace]').addEventListener('click', function () {
      const bundle = { export_contract_version: WORKSPACE_VERSION, exported_at: now(), workspace: state.workspace };
      downloadJson('catalyst-finance-workspace-v2.0.0.json', bundle);
    });
    root.querySelector('[data-scfin-import-workspace]').addEventListener('change', function (event) {
      const file = event.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = function () {
        try {
          const parsed = JSON.parse(reader.result); const imported = validateWorkspace(parsed.workspace || parsed);
          state.workspace = imported; state.currentScenarioId = imported.scenarios[0].scenario_id;
          root.querySelector('[data-scfin-workspace-name]').value = imported.name; persistCanonical(); loadCurrent();
        } catch (error) { window.alert('Workspace import failed: ' + error.message); }
      };
      reader.readAsText(file); event.target.value = '';
    });
    window.addEventListener('beforeunload', function (event) {
      if (!state.dirty) return; event.preventDefault(); event.returnValue = '';
    });

    root.querySelector('[data-scfin-copy]').addEventListener('click', function () {
      const text = JSON.stringify(root._scfinPayload || CatalystFinanceEngine.evaluate(inputFromForm(form, state.workspace.defaults.currency)), null, 2);
      if (navigator.clipboard) navigator.clipboard.writeText(text);
    });
    root.querySelector('[data-scfin-download]').addEventListener('click', function () {
      downloadJson('catalyst-finance-scenario-v2.0.0.json', root._scfinPayload || CatalystFinanceEngine.evaluate(inputFromForm(form, state.workspace.defaults.currency)));
    });
    root.querySelector('[data-scfin-print]').addEventListener('click', function () { window.print(); });

    if (loaded.recovered) setStatus('Recovered unsaved changes', 'recovery'); else persistCanonical();
    loadCurrent();
  }


  function cashFlowScenario(form) {
    const value = function (name) { return Number(form.elements[name].value || 0); };
    const horizon = Math.max(1, Math.floor(value('horizon')));
    const basis = form.elements.basis.value;
    const lines = [
      { flow_id: 'capital', label: 'Initial capital cost', category: 'capital_cost', amount: value('capitalCost'), start_period: 0, price_basis: basis },
      { flow_id: 'grant', label: 'Grant or rebate', category: 'grant', amount: value('grant'), start_period: 0, price_basis: basis },
      { flow_id: 'benefit', label: 'Recurring benefit', category: 'savings', amount: value('benefit'), start_period: 1, end_period: horizon, escalation_rate_percent_annual: value('escalation'), price_basis: basis },
      { flow_id: 'operations', label: 'Recurring operating cost', category: 'operating_cost', amount: value('operatingCost'), start_period: 1, end_period: horizon, escalation_rate_percent_annual: value('escalation'), price_basis: basis },
      { flow_id: 'working-capital', label: 'Working capital', category: 'working_capital', amount: value('workingCapital'), start_period: 0, price_basis: basis },
      { flow_id: 'working-capital-recovery', label: 'Working-capital recovery', category: 'working_capital_recovery', amount: value('workingCapitalRecovery'), start_period: horizon, price_basis: basis },
      { flow_id: 'residual', label: 'Residual value', category: 'residual_value', amount: value('residualValue'), start_period: horizon, price_basis: basis },
      { flow_id: 'decommission', label: 'Decommissioning cost', category: 'decommissioning_cost', amount: value('decommissioningCost'), start_period: horizon, price_basis: basis }
    ];
    if (value('phasedCapital') > 0) lines.push({ flow_id: 'phase-two', label: 'Phased capital', category: 'capital_cost', amount: value('phasedCapital'), start_period: Math.min(2, horizon), price_basis: basis });
    return {
      contract_version: '2.0.0',
      model_id: 'catalyst-finance.cash-flow',
      project: { name: 'Browser capital-budgeting scenario', category: 'Capital project' },
      context: {
        currency: 'USD', price_basis: basis, discount_rate_basis: basis,
        period_frequency: form.elements.frequency.value, time_basis: 'end_of_period',
        rounding_policy: 'half_up', monetary_decimals: 2, ratio_decimals: 4
      },
      analysis_horizon_periods: horizon,
      discount_rate_percent_annual: value('discountRate'),
      finance_rate_percent_annual: value('discountRate'),
      reinvestment_rate_percent_annual: Math.min(value('discountRate'), 3),
      lines: lines
    };
  }

  function drawSeries(canvas, values, waterfall) {
    const context = canvas.getContext('2d');
    const width = canvas.width; const height = canvas.height; const pad = 36;
    context.clearRect(0, 0, width, height);
    const minimum = Math.min(0, ...values); const maximum = Math.max(0, ...values);
    const range = Math.max(1, maximum - minimum);
    const y = function (value) { return pad + (maximum - value) / range * (height - pad * 2); };
    const zero = y(0);
    context.strokeStyle = '#8a8a8a'; context.lineWidth = 1;
    context.beginPath(); context.moveTo(pad, zero); context.lineTo(width - pad, zero); context.stroke();
    if (waterfall) {
      const slot = (width - pad * 2) / Math.max(values.length, 1);
      values.forEach(function (value, index) {
        const top = value >= 0 ? y(value) : zero;
        const barHeight = Math.max(1, Math.abs(y(value) - zero));
        context.fillStyle = value >= 0 ? '#2f6f4e' : '#8a2d2d';
        context.fillRect(pad + index * slot + 2, top, Math.max(2, slot - 4), barHeight);
      });
    } else {
      context.strokeStyle = '#5b1d2a'; context.lineWidth = 3; context.beginPath();
      values.forEach(function (value, index) {
        const x = pad + index * (width - pad * 2) / Math.max(values.length - 1, 1);
        if (index === 0) context.moveTo(x, y(value)); else context.lineTo(x, y(value));
      });
      context.stroke();
    }
  }

  function initializeCapitalBudgeting(root) {
    const section = root.querySelector('[data-scfin-capital-budgeting]');
    if (!section || typeof CatalystFinanceCashFlowEngine === 'undefined') return;
    const form = section.querySelector('[data-scfin-cf-form]');
    const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
    function render() {
      try {
        const result = CatalystFinanceCashFlowEngine.evaluate(cashFlowScenario(form));
        root._scfinCashFlowPayload = result;
        section.querySelector('[data-scfin-cf-npv]').textContent = money.format(result.metrics.npv);
        section.querySelector('[data-scfin-cf-payback]').textContent = result.metrics.simple_payback_periods === null ? 'Not reached' : result.metrics.simple_payback_periods + ' periods';
        const irr = result.metrics.irr_percent_annual === null ? result.metrics.irr_status.replaceAll('_', ' ') : result.metrics.irr_percent_annual + '%';
        const mirr = result.metrics.mirr_percent_annual === null ? '—' : result.metrics.mirr_percent_annual + '%';
        section.querySelector('[data-scfin-cf-irr]').textContent = irr + ' / ' + mirr;
        const bcr = result.metrics.benefit_cost_ratio === null ? '—' : result.metrics.benefit_cost_ratio;
        section.querySelector('[data-scfin-cf-bcr]').textContent = bcr + ' / ' + money.format(result.metrics.equivalent_annual_value);
        const table = section.querySelector('[data-scfin-cf-table]'); table.innerHTML = '';
        result.periods.forEach(function (row) {
          const tr = document.createElement('tr');
          [row.period_label, money.format(row.inflows), money.format(row.outflows), money.format(row.net_cash_flow), money.format(row.discounted_net_cash_flow), money.format(row.cumulative_cash_flow)].forEach(function (text) {
            const td = document.createElement('td'); td.textContent = text; tr.appendChild(td);
          });
          table.appendChild(tr);
        });
        drawSeries(section.querySelector('[data-scfin-cf-curve]'), result.periods.map(function (row) { return row.cumulative_cash_flow; }), false);
        drawSeries(section.querySelector('[data-scfin-cf-waterfall]'), result.periods.map(function (row) { return row.net_cash_flow; }), true);
        const trace = section.querySelector('[data-scfin-cf-trace]'); trace.innerHTML = '';
        result.metrics.metric_trace.forEach(function (metric) {
          const li = document.createElement('li'); li.textContent = metric.label + ': ' + metric.formula + '. ' + metric.notes; trace.appendChild(li);
        });
        result.interpretation.flags.forEach(function (flag) {
          const li = document.createElement('li'); li.textContent = flag; trace.appendChild(li);
        });
        section.querySelector('[data-scfin-cf-json]').textContent = JSON.stringify(result, null, 2);
      } catch (error) {
        section.querySelector('[data-scfin-cf-json]').textContent = String(error.message || error);
      }
    }
    form.addEventListener('input', render); form.addEventListener('change', render);
    section.querySelector('[data-scfin-cf-download]').addEventListener('click', function () { downloadJson('catalyst-finance-cash-flow-v2.0.0.json', root._scfinCashFlowPayload); });
    section.querySelector('[data-scfin-cf-copy]').addEventListener('click', function () {
      if (navigator.clipboard) navigator.clipboard.writeText(JSON.stringify(root._scfinCashFlowPayload, null, 2));
    });
    if (root.getAttribute('data-scfin-mode') === 'public') Array.from(form.elements).forEach(function (field) { if (field.tagName !== 'BUTTON') field.disabled = true; });
    render();
  }


  function comparisonDefinition(root) {
    const form = root.querySelector('[data-scfin-cf-form]');
    const base = cashFlowScenario(form);
    const horizon = base.analysis_horizon_periods;
    base.project.name = 'Browser comparison base case';
    base.lines.splice(5, 0, {
      flow_id: 'carbon-value', label: 'Annual carbon value', category: 'other_benefit', amount: 6300,
      start_period: 1, end_period: horizon, escalation_rate_percent_annual: 2, price_basis: base.context.price_basis
    });
    const downside = clone(base); const upside = clone(base);
    function line(scenario, id) { return scenario.lines.find(function (item) { return item.flow_id === id; }); }
    downside.project.name = 'Browser comparison downside case';
    downside.discount_rate_percent_annual = base.discount_rate_percent_annual + 2;
    downside.finance_rate_percent_annual = base.finance_rate_percent_annual + 2;
    line(downside, 'capital').amount *= 1.16;
    line(downside, 'benefit').amount *= 0.83;
    line(downside, 'benefit').start_period = Math.min(2, horizon);
    line(downside, 'operations').amount *= 1.25;
    line(downside, 'carbon-value').amount = 4500;
    upside.project.name = 'Browser comparison upside case';
    upside.discount_rate_percent_annual = Math.max(-99, base.discount_rate_percent_annual - 1);
    upside.finance_rate_percent_annual = Math.max(-99, base.finance_rate_percent_annual - 1);
    line(upside, 'capital').amount *= 0.94;
    line(upside, 'grant').amount += 20000;
    line(upside, 'benefit').amount *= 1.17;
    line(upside, 'operations').amount *= 0.85;
    line(upside, 'carbon-value').amount = 9000;
    const source = function (id) { return { workspace_id: 'workspace_browser', scenario_id: 'scenario_' + id, revision_id: 'revision_' + id + '_001', revision_number: 1 }; };
    const savings = function (alternativeId, id) { return {
      sensitivity_id: id, alternative_id: alternativeId, metric_id: 'npv',
      parameter: { parameter_id: 'annual-savings', label: 'Recurring benefit', path: 'line:benefit:amount', operation: 'set', value_kind: 'continuous', unit: 'USD/period' },
      values: [line(base, 'benefit').amount * 0.65, line(base, 'benefit').amount * 0.8, line(base, 'benefit').amount, line(base, 'benefit').amount * 1.2, line(base, 'benefit').amount * 1.35]
    }; };
    return {
      contract_version: '2.0.0', model_id: 'catalyst-finance.comparison', comparison_id: 'browser-options',
      name: 'Browser capital project alternatives', description: 'Live downside, base, and upside comparison generated from the capital-budgeting form.', baseline_alternative_id: 'base',
      alternatives: [
        { alternative_id: 'downside', label: 'Downside', kind: 'downside', source: source('downside'), scenario: downside, non_financial_caveats: ['Higher disruption and delivery risk', 'Benefits begin later'] },
        { alternative_id: 'base', label: 'Base', kind: 'base', source: source('base'), scenario: base, non_financial_caveats: ['Requires coordinated implementation access'] },
        { alternative_id: 'upside', label: 'Upside', kind: 'upside', source: source('upside'), scenario: upside, non_financial_caveats: ['Additional grant is not confirmed', 'Higher benefit realization requires verification'] }
      ],
      selected_metrics: [
        { metric_id: 'npv', objective: 'maximize', weight: 0.45 },
        { metric_id: 'discounted_payback_periods', objective: 'minimize', weight: 0.2 },
        { metric_id: 'mirr_percent_annual', objective: 'maximize', weight: 0.2 },
        { metric_id: 'benefit_cost_ratio', objective: 'maximize', weight: 0.15 }
      ],
      one_way_sensitivities: [
        savings('base', 'base-savings'),
        { sensitivity_id: 'base-discount-rate', alternative_id: 'base', metric_id: 'npv', parameter: { parameter_id: 'discount-rate', label: 'Discount rate', path: 'discount_rate_percent_annual', operation: 'set', value_kind: 'continuous', unit: 'percent/year' }, values: [2, 4, 6, 8, 10, 12] },
        { sensitivity_id: 'upside-capital', alternative_id: 'upside', metric_id: 'npv', parameter: { parameter_id: 'capital-cost', label: 'Initial capital cost', path: 'line:capital:amount', operation: 'set', value_kind: 'continuous', unit: 'USD' }, values: [line(base, 'capital').amount * 0.75, line(base, 'capital').amount, line(base, 'capital').amount * 1.25] },
        { sensitivity_id: 'downside-delay', alternative_id: 'downside', metric_id: 'npv', parameter: { parameter_id: 'implementation-delay', label: 'Implementation delay', path: 'all', operation: 'shift_periods', value_kind: 'integer', unit: 'periods' }, values: [0, 1, 2, 3] },
        { sensitivity_id: 'base-carbon', alternative_id: 'base', metric_id: 'npv', parameter: { parameter_id: 'carbon-value', label: 'Annual carbon value', path: 'line:carbon-value:amount', operation: 'set', value_kind: 'continuous', unit: 'USD/year' }, values: [0, 3000, 6300, 9000, 12000] }
      ],
      two_way_sensitivities: [{ sensitivity_id: 'benefit-vs-rate', alternative_id: 'base', metric_id: 'npv', row_parameter: { parameter_id: 'annual-savings', label: 'Recurring benefit', path: 'line:benefit:amount', operation: 'set', value_kind: 'continuous', unit: 'USD/period' }, row_values: [line(base, 'benefit').amount * 0.75, line(base, 'benefit').amount, line(base, 'benefit').amount * 1.25], column_parameter: { parameter_id: 'discount-rate', label: 'Discount rate', path: 'discount_rate_percent_annual', operation: 'set', value_kind: 'continuous', unit: 'percent/year' }, column_values: [4, 6, 8, 10] }],
      break_even_definitions: [
        { threshold_id: 'benefit-break-even', alternative_id: 'base', metric_id: 'npv', parameter: { parameter_id: 'annual-savings', label: 'Recurring benefit', path: 'line:benefit:amount', operation: 'set', value_kind: 'continuous', unit: 'USD/period' }, target_value: 0, lower_bound: 0, upper_bound: Math.max(100000, line(base, 'benefit').amount * 2), tolerance: 0.01, max_iterations: 100 },
        { threshold_id: 'capital-threshold', alternative_id: 'base', metric_id: 'npv', parameter: { parameter_id: 'capital-cost', label: 'Initial capital cost', path: 'line:capital:amount', operation: 'set', value_kind: 'continuous', unit: 'USD' }, target_value: 0, lower_bound: 0, upper_bound: Math.max(700000, line(base, 'capital').amount * 3), tolerance: 0.01, max_iterations: 100 },
        { threshold_id: 'delay-threshold', alternative_id: 'base', metric_id: 'npv', parameter: { parameter_id: 'implementation-delay', label: 'Implementation delay', path: 'all', operation: 'shift_periods', value_kind: 'integer', unit: 'periods' }, target_value: 0, lower_bound: 0, upper_bound: Math.min(10, horizon), tolerance: 0.01, max_iterations: 100 }
      ]
    };
  }

  function drawTornado(canvas, bars) {
    const context = canvas.getContext('2d'); const width = canvas.width; const height = canvas.height;
    context.clearRect(0, 0, width, height); if (!bars.length) return;
    const padLeft = 190; const padRight = 35; const center = padLeft + (width - padLeft - padRight) / 2;
    const maximum = Math.max(1, ...bars.flatMap(function (bar) { return [Math.abs(bar.low_impact || 0), Math.abs(bar.high_impact || 0)]; }));
    const scale = (width - padLeft - padRight) / 2 / maximum; const slot = (height - 20) / bars.length;
    context.strokeStyle = '#777'; context.beginPath(); context.moveTo(center, 8); context.lineTo(center, height - 8); context.stroke();
    bars.forEach(function (bar, index) {
      const y = 12 + index * slot; const low = bar.low_impact || 0; const high = bar.high_impact || 0;
      context.fillStyle = '#222'; context.font = '13px system-ui'; context.textAlign = 'right'; context.fillText(bar.label, padLeft - 12, y + 13);
      context.fillStyle = '#7d2838'; context.fillRect(center + Math.min(0, low) * scale, y, Math.max(2, Math.abs(low) * scale), Math.max(8, slot * 0.32));
      context.fillStyle = '#335f4a'; context.fillRect(center + Math.min(0, high) * scale, y + Math.max(9, slot * 0.35), Math.max(2, Math.abs(high) * scale), Math.max(8, slot * 0.32));
    });
  }

  function initializeComparison(root) {
    const section = root.querySelector('[data-scfin-comparison-studio]');
    if (!section || typeof CatalystFinanceComparisonEngine === 'undefined') return;
    const cashForm = root.querySelector('[data-scfin-cf-form]'); const currency = 'USD';
    function render() {
      try {
        const result = CatalystFinanceComparisonEngine.evaluate(comparisonDefinition(root)); root._scfinComparisonPayload = result;
        const byId = {}; result.alternatives.forEach(function (item) { byId[item.alternative_id] = item; });
        const ranking = section.querySelector('[data-scfin-comparison-ranking]'); ranking.innerHTML = '';
        result.rankings.forEach(function (item) {
          const tr = document.createElement('tr'); const alt = byId[item.alternative_id];
          [item.rank, item.label, item.weighted_score.toFixed(2), money(alt.metrics.npv, currency), alt.metrics.discounted_payback_periods === null ? 'Not reached' : alt.metrics.discounted_payback_periods + ' periods', item.dominates.length ? 'Dominates ' + item.dominates.join(', ') : 'No dominance'].forEach(function (value) { const td = document.createElement('td'); td.textContent = value; tr.appendChild(td); }); ranking.appendChild(tr);
        });
        const metrics = section.querySelector('[data-scfin-comparison-metrics]'); metrics.innerHTML = '';
        result.aligned_metrics.forEach(function (row) {
          const tr = document.createElement('tr'); const label = document.createElement('td'); label.textContent = row.label; tr.appendChild(label);
          ['downside', 'base', 'upside'].forEach(function (id) { const value = row.values.find(function (item) { return item.alternative_id === id; }); const td = document.createElement('td'); td.textContent = value.value === null ? '—' : (['npv', 'equivalent_annual_value', 'net_cash_flow'].includes(row.metric_id) ? money(value.value, currency) : value.value) + (value.delta_from_baseline === null ? '' : ' (' + (value.delta_from_baseline >= 0 ? '+' : '') + value.delta_from_baseline + ')'); tr.appendChild(td); }); metrics.appendChild(tr);
        });
        drawTornado(section.querySelector('[data-scfin-comparison-tornado]'), result.tornado);
        const tornadoList = section.querySelector('[data-scfin-comparison-tornado-list]'); tornadoList.innerHTML = '';
        result.tornado.forEach(function (bar) { const li = document.createElement('li'); li.textContent = bar.label + ': ' + money(bar.low_impact, currency) + ' to ' + money(bar.high_impact, currency) + ' NPV impact'; tornadoList.appendChild(li); });
        const thresholds = section.querySelector('[data-scfin-comparison-thresholds]'); thresholds.innerHTML = '';
        result.break_even_results.forEach(function (item) { const li = document.createElement('li'); li.textContent = item.parameter.label + ': ' + (item.threshold_value === null ? item.status.replaceAll('_', ' ') : item.threshold_value + (item.parameter.unit ? ' ' + item.parameter.unit : '')); thresholds.appendChild(li); });
        const caveats = section.querySelector('[data-scfin-comparison-caveats]'); caveats.innerHTML = '';
        result.alternatives.forEach(function (item) { item.non_financial_caveats.forEach(function (caveat) { const li = document.createElement('li'); li.textContent = item.label + ': ' + caveat; caveats.appendChild(li); }); });
        section.querySelector('[data-scfin-comparison-json]').textContent = JSON.stringify(result, null, 2);
      } catch (error) { section.querySelector('[data-scfin-comparison-json]').textContent = String(error.message || error); }
    }
    let timer = null; function schedule() { window.clearTimeout(timer); timer = window.setTimeout(render, 120); }
    cashForm.addEventListener('input', schedule); cashForm.addEventListener('change', schedule);
    section.querySelector('[data-scfin-comparison-refresh]').addEventListener('click', render);
    section.querySelector('[data-scfin-comparison-download]').addEventListener('click', function () { downloadJson('catalyst-finance-comparison-v2.0.0.json', root._scfinComparisonPayload); });
    render();
  }


  function uncertaintyDefinition(root) {
    const scenario = cashFlowScenario(root.querySelector('[data-scfin-cf-form]'));
    const section = root.querySelector('[data-scfin-uncertainty-studio]');
    const capital = scenario.lines.find(function (line) { return line.flow_id === 'capital'; }).amount;
    const benefit = scenario.lines.find(function (line) { return line.flow_id === 'benefit'; }).amount;
    const operations = scenario.lines.find(function (line) { return line.flow_id === 'operations'; }).amount;
    const capitalRange = Number(section.querySelector('[data-scfin-uncertainty-capital]').value || 20) / 100;
    const benefitStd = Number(section.querySelector('[data-scfin-uncertainty-benefit]').value || 15) / 100;
    const rate = scenario.discount_rate_percent_annual;
    return {
      contract_version: '2.0.0', model_id: 'catalyst-finance.uncertainty', uncertainty_id: 'browser-risk-analysis',
      name: 'Browser uncertainty and stress analysis', description: 'Seeded simulation generated from the live capital-budgeting form.',
      source: { workspace_id: 'workspace_browser', scenario_id: 'scenario_cashflow', revision_id: 'revision_browser_001', revision_number: 1 },
      scenario: scenario, metric_ids: ['npv', 'mirr_percent_annual', 'discounted_payback_periods'],
      variables: [
        { variable_id: 'capital-cost', label: 'Initial capital cost', parameter: { parameter_id: 'capital-cost', label: 'Initial capital cost', path: 'line:capital:amount', operation: 'set', value_kind: 'continuous', unit: 'USD' }, distribution: { kind: 'triangular', minimum: Math.max(0, capital * (1 - capitalRange)), mode: capital, maximum: capital * (1 + capitalRange), truncate_minimum: 0 } },
        { variable_id: 'recurring-benefit', label: 'Recurring benefit', parameter: { parameter_id: 'recurring-benefit', label: 'Recurring benefit', path: 'line:benefit:amount', operation: 'set', value_kind: 'continuous', unit: 'USD/period' }, distribution: { kind: 'normal', mean: benefit, standard_deviation: Math.max(1, benefit * benefitStd), truncate_minimum: 0 } },
        { variable_id: 'operating-cost', label: 'Operating cost', parameter: { parameter_id: 'operating-cost', label: 'Operating cost', path: 'line:operations:amount', operation: 'set', value_kind: 'continuous', unit: 'USD/period' }, distribution: { kind: 'triangular', minimum: Math.max(0, operations * 0.8), mode: operations, maximum: operations * 1.4, truncate_minimum: 0 } },
        { variable_id: 'discount-rate', label: 'Discount rate', parameter: { parameter_id: 'discount-rate', label: 'Discount rate', path: 'discount_rate_percent_annual', operation: 'set', value_kind: 'continuous', unit: 'percent/year' }, distribution: { kind: 'uniform', minimum: Math.max(-99, rate - 2), maximum: rate + 4 } },
        { variable_id: 'implementation-delay', label: 'Implementation delay', parameter: { parameter_id: 'implementation-delay', label: 'Implementation delay', path: 'all', operation: 'shift_periods', value_kind: 'integer', unit: 'periods' }, distribution: { kind: 'discrete', values: [0, 1, 2], probabilities: [0.65, 0.25, 0.1] } }
      ],
      correlations: [
        { left_variable_id: 'capital-cost', right_variable_id: 'implementation-delay', coefficient: 0.35 },
        { left_variable_id: 'recurring-benefit', right_variable_id: 'operating-cost', coefficient: 0.2 }
      ],
      stress_cases: [
        { stress_id: 'cost-overrun-delay', label: 'Cost overrun and delay', description: 'Capital costs rise and implementation is delayed.', adjustments: [
          { parameter: { parameter_id: 'capital-multiplier', label: 'Capital multiplier', path: 'line:capital:amount', operation: 'multiply', value_kind: 'continuous', unit: 'factor' }, value: 1.2 },
          { parameter: { parameter_id: 'delay', label: 'Implementation delay', path: 'all', operation: 'shift_periods', value_kind: 'integer', unit: 'periods' }, value: 2 }
        ] },
        { stress_id: 'benefit-shortfall', label: 'Benefit shortfall', description: 'Recurring benefits are thirty percent below the base case.', adjustments: [
          { parameter: { parameter_id: 'benefit-multiplier', label: 'Benefit multiplier', path: 'line:benefit:amount', operation: 'multiply', value_kind: 'continuous', unit: 'factor' }, value: 0.7 }
        ] },
        { stress_id: 'combined-downside', label: 'Combined downside', description: 'Costs rise, benefits fall, and the discount rate increases.', adjustments: [
          { parameter: { parameter_id: 'capital-multiplier', label: 'Capital multiplier', path: 'line:capital:amount', operation: 'multiply', value_kind: 'continuous', unit: 'factor' }, value: 1.15 },
          { parameter: { parameter_id: 'benefit-multiplier', label: 'Benefit multiplier', path: 'line:benefit:amount', operation: 'multiply', value_kind: 'continuous', unit: 'factor' }, value: 0.8 },
          { parameter: { parameter_id: 'discount-rate', label: 'Discount rate', path: 'discount_rate_percent_annual', operation: 'set', value_kind: 'continuous', unit: 'percent/year' }, value: rate + 4 }
        ] }
      ],
      downside_thresholds: { npv: 0, mirr_percent_annual: rate },
      monte_carlo: { iterations: Math.max(100, Math.min(5000, Math.floor(Number(section.querySelector('[data-scfin-uncertainty-iterations]').value || 500)))), seed: Number(section.querySelector('[data-scfin-uncertainty-seed]').value || 20260717), percentiles: [5, 10, 25, 50, 75, 90, 95], retain_samples: 25, histogram_bins: 12 }
    };
  }

  function drawHistogram(canvas, bins) {
    const context = canvas.getContext('2d'); const width = canvas.width; const height = canvas.height; const pad = 34;
    context.clearRect(0, 0, width, height); if (!bins.length) return;
    const maximum = Math.max(1, ...bins.map(function (item) { return item.count; })); const slot = (width - pad * 2) / bins.length;
    context.strokeStyle = '#777'; context.beginPath(); context.moveTo(pad, height - pad); context.lineTo(width - pad, height - pad); context.stroke();
    bins.forEach(function (item, index) { const barHeight = (height - pad * 2) * item.count / maximum; context.fillStyle = '#5a2635'; context.fillRect(pad + index * slot + 1, height - pad - barHeight, Math.max(2, slot - 2), barHeight); });
  }

  function initializeUncertainty(root) {
    const section = root.querySelector('[data-scfin-uncertainty-studio]');
    if (!section || typeof CatalystFinanceUncertaintyEngine === 'undefined') return;
    function run() {
      try {
        const result = CatalystFinanceUncertaintyEngine.evaluate(uncertaintyDefinition(root)); root._scfinUncertaintyPayload = result;
        const npv = result.summaries.find(function (item) { return item.metric_id === 'npv'; });
        const p5 = npv.percentiles.find(function (item) { return item.percentile === 5; });
        section.querySelector('[data-scfin-uncertainty-mean]').textContent = money(npv.mean, 'USD');
        section.querySelector('[data-scfin-uncertainty-p5]').textContent = money(p5.value, 'USD');
        section.querySelector('[data-scfin-uncertainty-positive]').textContent = (npv.probability_above_zero * 100).toFixed(1) + '%';
        section.querySelector('[data-scfin-uncertainty-shortfall]').textContent = money(npv.expected_shortfall_5, 'USD');
        drawHistogram(section.querySelector('[data-scfin-uncertainty-histogram]'), result.histograms.filter(function (item) { return item.metric_id === 'npv'; }));
        const influence = section.querySelector('[data-scfin-uncertainty-influence]'); influence.innerHTML = '';
        result.variable_influences.filter(function (item) { return item.metric_id === 'npv'; }).forEach(function (item) { const li = document.createElement('li'); li.textContent = item.label + ': ' + (item.pearson_correlation === null ? 'not estimable' : item.pearson_correlation.toFixed(3)); influence.appendChild(li); });
        const stress = section.querySelector('[data-scfin-uncertainty-stress]'); stress.innerHTML = '';
        result.stress_results.forEach(function (item) { const li = document.createElement('li'); li.textContent = item.label + ': NPV ' + money(item.metrics.npv, 'USD') + ' (' + (item.deltas_from_base.npv >= 0 ? '+' : '') + money(item.deltas_from_base.npv, 'USD') + ' vs. base)'; stress.appendChild(li); });
        section.querySelector('[data-scfin-uncertainty-meta]').textContent = 'Seed ' + result.metadata.seed + ' · ' + result.metadata.completed_iterations + ' completed · ' + result.metadata.rejected_iterations + ' rejected draws';
        section.querySelector('[data-scfin-uncertainty-json]').textContent = JSON.stringify(result, null, 2);
      } catch (error) { section.querySelector('[data-scfin-uncertainty-json]').textContent = String(error.message || error); }
    }
    section.querySelector('[data-scfin-uncertainty-run]').addEventListener('click', run);
    section.querySelector('[data-scfin-uncertainty-download]').addEventListener('click', function () { if (root._scfinUncertaintyPayload) downloadJson('catalyst-finance-uncertainty-v2.0.0.json', root._scfinUncertaintyPayload); });
    run();
  }


  function pricingDefinition(section) {
    const form = section.querySelector('[data-scfin-pricing-form]');
    const value = function (name) { return Number(form.elements[name].value); };
    const current = value('currentPrice');
    return {
      contract_version: '2.0.0', model_id: 'catalyst-finance.pricing', pricing_id: 'browser-pricing',
      name: 'Browser pricing analysis', description: 'Interactive segmented demand and pricing analysis.',
      source: { workspace_id: 'workspace_browser', scenario_id: 'scenario_pricing', revision_id: 'revision_browser', revision_number: 1 },
      currency: 'USD', objective: form.elements.objective.value, current_price: current,
      segments: [
        { segment_id: 'commuter', label: 'Daily commuters', quantity_multiplier: 1, curve: { kind: 'linear', intercept: value('intercept'), slope: value('slope'), reference_price: null, reference_quantity: null, elasticity: null, observed_points: [] } },
        { segment_id: 'hybrid', label: 'Hybrid workers', quantity_multiplier: 1, curve: { kind: 'constant_elasticity', intercept: null, slope: null, reference_price: current, reference_quantity: value('referenceQuantity'), elasticity: value('elasticity'), observed_points: [] } },
        { segment_id: 'student', label: 'Students', quantity_multiplier: 1, curve: { kind: 'observed', intercept: null, slope: null, reference_price: null, reference_quantity: null, elasticity: null, observed_points: [ {price:30,quantity:5500}, {price:45,quantity:4200}, {price:60,quantity:3000}, {price:80,quantity:1800} ] } }
      ],
      costs: { fixed_cost: value('fixedCost'), unit_variable_cost: value('unitCost'), unit_fulfillment_cost: 0, channel_fee_percent: 2.5 },
      grid: { minimum_price: value('minimumPrice'), maximum_price: value('maximumPrice'), steps: 51 },
      constraints: { capacity_units: value('capacity'), minimum_volume_units: 9000, maximum_price_change_percent: value('maxChange') }
    };
  }

  function drawPricingChart(canvas, result) {
    const context = canvas.getContext('2d'), width = canvas.width, height = canvas.height, pad = 42;
    context.clearRect(0, 0, width, height);
    const values = result.rows.map(function (row) { return result.definition.objective === 'revenue' ? row.gross_revenue : (result.definition.objective === 'contribution' ? row.contribution : row.operating_profit); });
    const minimum = Math.min.apply(null, values), maximum = Math.max.apply(null, values), span = Math.max(1, maximum - minimum);
    context.strokeStyle = '#777'; context.beginPath(); context.moveTo(pad, height-pad); context.lineTo(width-pad, height-pad); context.stroke();
    context.strokeStyle = '#5a2635'; context.lineWidth = 3; context.beginPath();
    result.rows.forEach(function (row, index) { const x = pad + index * (width-pad*2)/(result.rows.length-1); const y = height-pad-(values[index]-minimum)*(height-pad*2)/span; if(index===0) context.moveTo(x,y); else context.lineTo(x,y); });
    context.stroke();
    const selected = result.recommendation.recommended_price; const index = result.rows.findIndex(function (row) { return row.price === selected; });
    if(index >= 0) { const x = pad + index*(width-pad*2)/(result.rows.length-1); const y = height-pad-(values[index]-minimum)*(height-pad*2)/span; context.fillStyle='#000'; context.beginPath(); context.arc(x,y,5,0,Math.PI*2); context.fill(); }
  }

  function initializePricing(root) {
    const section = root.querySelector('[data-scfin-pricing-studio]');
    if (!section || typeof CatalystFinancePricingEngine === 'undefined') return;
    function run() {
      try {
        const result = CatalystFinancePricingEngine.evaluate(pricingDefinition(section)); root._scfinPricingPayload = result;
        const row = result.rows[result.recommendation.recommended_price === null ? 0 : result.rows.findIndex(function (item) { return item.price === result.recommendation.recommended_price; })];
        section.querySelector('[data-scfin-pricing-price]').textContent = money(result.recommendation.recommended_price, result.definition.currency);
        section.querySelector('[data-scfin-pricing-gain]').textContent = result.recommendation.expected_objective_gain === null ? '—' : money(result.recommendation.expected_objective_gain, result.definition.currency);
        section.querySelector('[data-scfin-pricing-volume]').textContent = row.quantity.toLocaleString('en-US', {maximumFractionDigits:0});
        section.querySelector('[data-scfin-pricing-elasticity]').textContent = row.average_elasticity === null ? '—' : row.average_elasticity.toFixed(2);
        section.querySelector('[data-scfin-pricing-note]').textContent = result.recommendation.narrative;
        drawPricingChart(section.querySelector('[data-scfin-pricing-chart]'), result);
        const table = section.querySelector('[data-scfin-pricing-table]'); table.innerHTML='';
        result.rows.filter(function (_, index) { return index % 5 === 0 || index === result.rows.length - 1; }).forEach(function (item) { const tr=document.createElement('tr'); tr.innerHTML='<td>'+money(item.price,'USD')+'</td><td>'+item.quantity.toLocaleString('en-US',{maximumFractionDigits:0})+'</td><td>'+money(item.gross_revenue,'USD')+'</td><td>'+money(item.contribution,'USD')+'</td><td>'+money(item.operating_profit,'USD')+'</td><td>'+(item.average_elasticity===null?'—':item.average_elasticity.toFixed(2))+'</td>'; table.appendChild(tr); });
        const flags = section.querySelector('[data-scfin-pricing-flags]'); flags.innerHTML=''; result.flags.forEach(function(item){const li=document.createElement('li');li.textContent=item;flags.appendChild(li);});
        section.querySelector('[data-scfin-pricing-json]').textContent=JSON.stringify(result,null,2);
      } catch(error) { section.querySelector('[data-scfin-pricing-json]').textContent=String(error.message||error); }
    }
    section.querySelector('[data-scfin-pricing-run]').addEventListener('click', run);
    section.querySelector('[data-scfin-pricing-download]').addEventListener('click', function(){ if(root._scfinPricingPayload) downloadJson('catalyst-finance-pricing-v2.0.0.json', root._scfinPricingPayload); });
    run();
  }

  function operatingDefinition(section) {
    const form = section.querySelector('[data-scfin-operating-form]');
    const value = function (name) { return Number(form.elements[name].value); };
    const budgetFixed = value('budgetFixed'), actualFixed = value('actualFixed');
    return {
      contract_version: '2.0.0', model_id: 'catalyst-finance.operating', operating_id: 'browser-operations',
      name: 'Browser operating analysis', description: 'Interactive budget, variance, and operating-economics analysis.',
      source: { workspace_id: 'workspace_browser', scenario_id: 'scenario_operations', revision_id: 'revision_browser', revision_number: 1 },
      currency: 'USD', period_frequency: 'monthly', target_operating_profit: value('targetProfit'),
      units: [{ unit_id: 'delivery', label: 'Implementation services', cost_center: 'Delivery', periods: [{
        period: 1, label: 'Current period', budget_units: value('budgetUnits'), actual_units: value('actualUnits'),
        budget_unit_price: value('budgetPrice'), actual_unit_price: value('actualPrice'),
        budget_variable_cost_per_unit: value('budgetVariable'), actual_variable_cost_per_unit: value('actualVariable'),
        budget_direct_fixed_cost: budgetFixed, actual_direct_fixed_cost: actualFixed,
        budget_allocated_overhead: 0, actual_allocated_overhead: 0
      }]}]
    };
  }

  function initializeOperating(root) {
    const section = root.querySelector('[data-scfin-operating-studio]');
    if (!section || typeof CatalystFinanceOperatingEngine === 'undefined') return;
    function run() {
      try {
        const result = CatalystFinanceOperatingEngine.evaluate(operatingDefinition(section)); root._scfinOperatingPayload = result;
        const row = result.rows[0], variance = row.variances[row.variances.length - 1];
        section.querySelector('[data-scfin-operating-profit]').textContent = money(row.actual_operating_profit, result.definition.currency);
        const varianceNode = section.querySelector('[data-scfin-operating-variance]');
        varianceNode.textContent = (variance.amount >= 0 ? '+' : '') + money(variance.amount, result.definition.currency);
        varianceNode.dataset.status = variance.status;
        section.querySelector('[data-scfin-operating-breakeven]').textContent = row.break_even_units === null ? '—' : row.break_even_units.toLocaleString('en-US', {maximumFractionDigits:1});
        section.querySelector('[data-scfin-operating-safety]').textContent = row.margin_of_safety_units === null ? '—' : row.margin_of_safety_units.toLocaleString('en-US', {maximumFractionDigits:1}) + ' units';
        const table = section.querySelector('[data-scfin-operating-table]'); table.innerHTML = '';
        row.variances.slice(0, 4).forEach(function (item) { const tr = document.createElement('tr'); tr.innerHTML = '<td>'+item.label+'</td><td>'+money(item.amount,'USD')+'</td><td>'+item.status+'</td>'; table.appendChild(tr); });
        const flags = section.querySelector('[data-scfin-operating-flags]'); flags.innerHTML = ''; result.flags.forEach(function (item) { const li=document.createElement('li');li.textContent=item;flags.appendChild(li); });
        section.querySelector('[data-scfin-operating-json]').textContent = JSON.stringify(result, null, 2);
      } catch (error) { section.querySelector('[data-scfin-operating-json]').textContent = String(error.message || error); }
    }
    section.querySelector('[data-scfin-operating-run]').addEventListener('click', run);
    section.querySelector('[data-scfin-operating-download]').addEventListener('click', function () { if (root._scfinOperatingPayload) downloadJson('catalyst-finance-operating-v2.0.0.json', root._scfinOperatingPayload); });
    run();
  }


  function sustainableDefinition(section) {
    const form = section.querySelector('[data-scfin-sustainable-form]');
    const value = function (name) { return Number(form.elements[name].value); };
    const baseline = value('baselineEmissions'), project = value('projectEmissions');
    const uplift = value('naturalUplift');
    return {
      contract_version:'2.0.0', model_id:'catalyst-finance.sustainable', analysis_id:'browser-sustainable',
      name:'Browser sustainable-value analysis', description:'Interactive carbon, natural-capital, transition, and financing analysis.',
      source:{workspace_id:'workspace_browser',scenario_id:'scenario_sustainable',revision_id:'revision_browser',revision_number:1},
      currency:'USD', reporting_period:'Interactive case', horizon_years:10, discount_rate_percent:5, base_project_npv:value('baseNpv'),
      baseline_emissions_tco2e:baseline, project_emissions_tco2e:project, carbon_price_per_tco2e:value('carbonPrice'),
      carbon_credit_quantity_tco2e:value('creditQuantity'), carbon_credit_price_per_tco2e:value('creditPrice'), carbon_credit_discount_percent:value('creditDiscount'), verification_cost:18000, carbon_valuation_method:'higher_of',
      natural_capital_assets:[{asset_id:'combined-assets',label:'Combined natural-capital assets',category:'ecosystem_service',quantity:1,unit:'portfolio',baseline_unit_value:0,projected_unit_value:uplift,annual_service_value:value('annualServices'),restoration_cost:195000,confidence_percent:75}],
      transition_items:[{item_id:'assurance-cost',label:'Measurement and assurance',kind:'cost',amount:90000,probability_percent:100,timing_years:1}],
      green_financing_principal:value('greenPrincipal'), conventional_interest_rate_percent:6.2, green_interest_rate_percent:Math.max(0,6.2-value('rateSavings')), financing_term_years:8
    };
  }

  function initializeSustainable(root) {
    const section=root.querySelector('[data-scfin-sustainable-studio]');
    if(!section||typeof CatalystFinanceSustainableEngine==='undefined')return;
    function run(){
      try{
        const result=CatalystFinanceSustainableEngine.evaluate(sustainableDefinition(section)); root._scfinSustainablePayload=result;
        section.querySelector('[data-scfin-sustainable-emissions]').textContent=result.carbon.avoided_emissions_tco2e.toLocaleString('en-US')+' tCO₂e';
        section.querySelector('[data-scfin-sustainable-carbon]').textContent=money(result.summary.carbon_value,result.definition.currency);
        section.querySelector('[data-scfin-sustainable-total]').textContent=money(result.summary.total_sustainable_value,result.definition.currency);
        section.querySelector('[data-scfin-sustainable-npv]').textContent=money(result.summary.adjusted_project_npv,result.definition.currency);
        const table=section.querySelector('[data-scfin-sustainable-table]'); table.innerHTML='';
        [['Carbon value',result.summary.carbon_value],['Natural capital',result.summary.natural_capital_value],['Net transition value',result.summary.net_transition_value],['Green-financing savings',result.summary.green_financing_savings_present_value]].forEach(function(item){const tr=document.createElement('tr');tr.innerHTML='<td>'+item[0]+'</td><td>'+money(item[1],result.definition.currency)+'</td>';table.appendChild(tr);});
        const flags=section.querySelector('[data-scfin-sustainable-flags]');flags.innerHTML='';result.flags.forEach(function(item){const li=document.createElement('li');li.textContent=item;flags.appendChild(li);});
        section.querySelector('[data-scfin-sustainable-json]').textContent=JSON.stringify(result,null,2);
      }catch(error){section.querySelector('[data-scfin-sustainable-json]').textContent=String(error.message||error);}
    }
    section.querySelector('[data-scfin-sustainable-run]').addEventListener('click',run);
    section.querySelector('[data-scfin-sustainable-download]').addEventListener('click',function(){if(root._scfinSustainablePayload)downloadJson('catalyst-finance-sustainable-v2.0.0.json',root._scfinSustainablePayload);});
    run();
  }


  function governanceDefinition(section) {
    const form=section.querySelector('[data-scfin-governance-form]');
    const objection=form.elements.includeObjection.checked;
    const events=[
      {event_id:'event_review',reviewer_id:'user_reviewer',reviewer_name:'Independent Reviewer',role:'reviewer',action:'comment',subject_id:'gov_browser',created_at:'2026-07-16T09:00:00+00:00',comment:'Reviewed metric and evidence links.',resolves_event_id:null,private:false},
      {event_id:'event_approval',reviewer_id:'user_approver',reviewer_name:'Finance Approver',role:'approver',action:'approve',subject_id:'gov_browser',created_at:'2026-07-16T16:00:00+00:00',comment:'Approved with configured redactions.',resolves_event_id:null,private:false}
    ];
    if(objection) events.push({event_id:'event_objection',reviewer_id:'user_reviewer',reviewer_name:'Independent Reviewer',role:'reviewer',action:'object',subject_id:'claim_adjusted_npv',created_at:'2026-07-17T08:00:00+00:00',comment:'Additional cost evidence is required.',resolves_event_id:null,private:false});
    return {
      contract_version:'2.0.0',model_id:'catalyst-finance.governance',governance_id:'gov_browser',name:'Browser governed finance case',description:'Interactive evidence, review, and publication example.',
      source:{workspace_id:'workspace_browser',scenario_id:'scenario_sustainable',revision_id:'revision_browser',revision_number:1},
      artifact:{artifact_id:'artifact_browser',model_id:'catalyst-finance.sustainable',model_version:'2.0.0',revision_id:'revision_browser',title:'Browser sustainable-value analysis',headline_metrics:{adjusted_project_npv:Number(form.elements.adjustedNpv.value),avoided_emissions_tco2e:Number(form.elements.avoidedEmissions.value)}},
      assumptions:[{assumption_id:'assumption_carbon',label:'Shadow carbon price',value:'75',unit:'USD/tCO2e',owner:'Finance team',confidence_percent:85,applicability:'Applied to avoided emissions.',review_status:'verified',source_ids:['source_policy'],evidence_ids:['evidence_policy'],private:false,rationale:'Approved planning value.'},{assumption_id:'assumption_private',label:'Confidential vendor cost',value:'Confidential',unit:'USD',owner:'Procurement',confidence_percent:90,applicability:'Internal estimate.',review_status:'verified',source_ids:['source_private'],evidence_ids:['evidence_private'],private:true,rationale:'Commercially sensitive.'}],
      sources:[{source_id:'source_policy',title:'Carbon valuation policy',source_type:'policy',citation:'Institutional carbon valuation policy, 2026.',url:null,published_date:'2026-03-01',accessed_date:'2026-07-17',owner:'Finance governance',confidence_percent:95,applicability:'Approved internal planning value.',review_status:'verified',private:false,attachment_ids:[],notes:''},{source_id:'source_private',title:'Vendor quotation',source_type:'document',citation:'Confidential vendor quotation, 2026.',url:null,published_date:'2026-06-30',accessed_date:'2026-07-17',owner:'Procurement',confidence_percent:90,applicability:'Current implementation scope.',review_status:'verified',private:true,attachment_ids:['attachment_private'],notes:'Do not publish.'}],
      evidence:[{evidence_id:'evidence_policy',source_id:'source_policy',evidence_type:'methodology',summary:'Policy supports the carbon valuation assumption.',locator:'Section 4.2',confidence_percent:95,private:false},{evidence_id:'evidence_private',source_id:'source_private',evidence_type:'quantitative',summary:'Quotation supports internal costs.',locator:'Commercial schedule',confidence_percent:90,private:true}],
      claims:[{claim_id:'claim_adjusted_npv',text:'The governed analysis reports the displayed adjusted project NPV.',classification:'headline',metric_paths:['summary.adjusted_project_npv'],calculation_ids:['calculation_total'],assumption_ids:['assumption_carbon'],source_ids:['source_policy'],evidence_ids:['evidence_policy'],review_status:'verified',public:true},{claim_id:'claim_private_cost',text:'A confidential quotation supports internal project costs.',classification:'supporting',metric_paths:['definition.base_project_npv'],calculation_ids:['calculation_base'],assumption_ids:['assumption_private'],source_ids:['source_private'],evidence_ids:['evidence_private'],review_status:'verified',public:false}],
      methodologies:[{methodology_id:'method_browser',name:'Catalyst Finance governed publication',version:'2.0.0',purpose:'Connect finance claims to evidence and review.',model_ids:['catalyst-finance.sustainable','catalyst-finance.governance'],data_quality_notes:['Public source is verified.'],conflicts:['Procurement owns a confidential source.'],limitations:['Illustrative browser data.'],excluded_factors:['Tax effects.']}],
      review_events:events,attachments:[{attachment_id:'attachment_private',filename:'vendor-quote.pdf',media_type:'application/pdf',checksum_sha256:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',owner:'Procurement',private:true,retention_note:'Internal only.'}],
      publication:{state:form.elements.publicationState.value,audience:form.elements.audience.value,title:form.elements.publicationTitle.value,summary:form.elements.publicationSummary.value,redaction_policy:'exclude_private',knowledge_library_collection_id:'collection_finance_briefs',decision_studio_packet_id:'packet_browser'}
    };
  }

  function initializeGovernance(root) {
    const section=root.querySelector('[data-scfin-governance-studio]');
    if(!section||typeof CatalystFinanceGovernanceEngine==='undefined')return;
    function run(){
      try{
        const result=CatalystFinanceGovernanceEngine.evaluate(governanceDefinition(section));root._scfinGovernancePayload=result;
        section.querySelector('[data-scfin-governance-status]').textContent=result.readiness.status.replaceAll('_',' ');
        section.querySelector('[data-scfin-governance-trace]').textContent=result.readiness.fully_traced_headline_count+' / '+result.readiness.headline_claim_count;
        section.querySelector('[data-scfin-governance-approvals]').textContent=String(result.readiness.approval_count);
        section.querySelector('[data-scfin-governance-private]').textContent=String(result.readiness.private_record_count);
        const table=section.querySelector('[data-scfin-governance-table]');table.innerHTML='';result.trace_matrix.forEach(function(item){const tr=document.createElement('tr');tr.innerHTML='<td>'+item.claim_text+'</td><td>'+item.metric_paths.join(', ')+'</td><td>'+item.source_ids.join(', ')+'</td><td>'+(item.complete?'Yes':'No')+'</td>';table.appendChild(tr);});
        const flags=section.querySelector('[data-scfin-governance-flags]');flags.innerHTML='';result.flags.forEach(function(item){const li=document.createElement('li');li.textContent=item;flags.appendChild(li);});
        section.querySelector('[data-scfin-governance-brief]').textContent=result.decision_brief_markdown;
        section.querySelector('[data-scfin-governance-json]').textContent=JSON.stringify(result,null,2);
      }catch(error){section.querySelector('[data-scfin-governance-json]').textContent=String(error.message||error);}
    }
    section.querySelector('[data-scfin-governance-run]').addEventListener('click',run);
    section.querySelector('[data-scfin-governance-download]').addEventListener('click',function(){if(root._scfinGovernancePayload)downloadJson('catalyst-finance-governance-v2.0.0.json',root._scfinGovernancePayload);});
    section.querySelector('[data-scfin-governance-public]').addEventListener('click',function(){if(root._scfinGovernancePayload)downloadJson('catalyst-finance-governance-public-v2.0.0.json',root._scfinGovernancePayload.public_payload);});
    run();
  }


  function platformDefinition(section) {
    const form = section.querySelector('[data-scfin-platform-form]');
    const retrofitNpv = Number(form.elements.retrofitNpv.value);
    const pricingNpv = Number(form.elements.pricingNpv.value);
    const retrofitConfidence = Number(form.elements.retrofitConfidence.value);
    const pricingConfidence = Number(form.elements.pricingConfidence.value);
    const products = [
      {product_id:'catalyst-finance',name:'Catalyst Finance',version:'2.0.0',role:'finance',status:'online',artifact_kinds:['finance-publication','platform'],supported_contracts:['catalyst-finance/2.0.0'],accepted_classifications:['public','internal','confidential'],api_base:null},
      {product_id:'decision-studio',name:'Decision Studio',version:'2.0.0',role:'decision',status:'online',artifact_kinds:['decision-packet'],supported_contracts:['sustainable-catalyst/decision-handoff/2.0.0'],accepted_classifications:['public','internal','confidential'],api_base:null},
      {product_id:'knowledge-library',name:'Knowledge Library',version:'4.0.0',role:'knowledge',status:'online',artifact_kinds:['public-brief'],supported_contracts:['sustainable-catalyst/knowledge-handoff/2.0.0'],accepted_classifications:['public'],api_base:null},
      {product_id:'site-intelligence',name:'Site Intelligence',version:'3.0.0',role:'intelligence',status:form.elements.intelligenceStatus.value,artifact_kinds:['market-signal'],supported_contracts:['sustainable-catalyst/intelligence-handoff/2.0.0'],accepted_classifications:['public','internal'],api_base:null}
    ];
    function artifact(id,source,model,title,kind,status,governance,classification,include,base,adjusted,capital,annual,confidence,downside,metrics) {
      return {artifact_id:id,revision_id:'revision_'+id.split('_')[1],source_product_id:source,model_id:model,model_version:'2.0.0',title:title,artifact_kind:kind,status:status,governance_status:governance,classification:classification,include_in_portfolio:include,checksum_sha256:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',financial:{currency:'USD',base_npv:base,adjusted_npv:adjusted,capital_required:capital,annual_value:annual,confidence_percent:confidence,downside_probability_percent:downside},headline_metrics:metrics||{},source_uri:null};
    }
    const artifacts = [
      artifact('artifact_market','site-intelligence','site-intelligence.market-signals','Regional market signal','market-signal','approved','approved','internal',false,0,0,0,0,90,10,{energy_price_growth_percent:4.2}),
      artifact('artifact_retrofit','catalyst-finance','catalyst-finance.sustainable','Retrofit sustainable-value case','sustainable-finance','published','published','public',true,125000,retrofitNpv,1800000,78000,retrofitConfidence,20,{adjusted_project_npv:retrofitNpv}),
      artifact('artifact_governance','catalyst-finance','catalyst-finance.governance','Governed retrofit brief','governance-publication','published','published','public',false,0,0,0,0,100,0,{fully_traced_headline_claims:2}),
      artifact('artifact_pricing','catalyst-finance','catalyst-finance.pricing','Advisory pricing case','pricing','approved','approved','confidential',true,210000,pricingNpv,180000,92000,pricingConfidence,25,{recommended_price:55})
    ];
    const handoffs = [
      {handoff_id:'handoff_market_finance',source_product_id:'site-intelligence',target_product_id:'catalyst-finance',artifact_id:'artifact_market',artifact_revision_id:'revision_market',contract_id:'sustainable-catalyst/intelligence-handoff/2.0.0',classification:'internal',status:'completed',payload_hash_sha256:'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',requested_at:'2026-07-17T18:00:00+00:00',updated_at:'2026-07-17T18:05:00+00:00',destination_id:'signal_retrofit',error_code:null,note:''},
      {handoff_id:'handoff_retrofit_decision',source_product_id:'catalyst-finance',target_product_id:'decision-studio',artifact_id:'artifact_retrofit',artifact_revision_id:'revision_retrofit',contract_id:'sustainable-catalyst/decision-handoff/2.0.0',classification:'internal',status:'completed',payload_hash_sha256:'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',requested_at:'2026-07-17T18:00:00+00:00',updated_at:'2026-07-17T18:05:00+00:00',destination_id:'packet_retrofit',error_code:null,note:''},
      {handoff_id:'handoff_governance_library',source_product_id:'catalyst-finance',target_product_id:'knowledge-library',artifact_id:'artifact_governance',artifact_revision_id:'revision_governance',contract_id:'sustainable-catalyst/knowledge-handoff/2.0.0',classification:'public',status:'completed',payload_hash_sha256:'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',requested_at:'2026-07-17T18:00:00+00:00',updated_at:'2026-07-17T18:05:00+00:00',destination_id:'collection_retrofit',error_code:null,note:''},
      {handoff_id:'handoff_pricing_decision',source_product_id:'catalyst-finance',target_product_id:'decision-studio',artifact_id:'artifact_pricing',artifact_revision_id:'revision_pricing',contract_id:'sustainable-catalyst/decision-handoff/2.0.0',classification:'confidential',status:'completed',payload_hash_sha256:'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',requested_at:'2026-07-17T18:00:00+00:00',updated_at:'2026-07-17T18:05:00+00:00',destination_id:'packet_pricing',error_code:null,note:''}
    ];
    if (form.elements.includeRejectedHandoff.checked) handoffs.push({handoff_id:'handoff_pricing_library',source_product_id:'catalyst-finance',target_product_id:'knowledge-library',artifact_id:'artifact_pricing',artifact_revision_id:'revision_pricing',contract_id:'sustainable-catalyst/knowledge-handoff/2.0.0',classification:'confidential',status:'rejected',payload_hash_sha256:'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',requested_at:'2026-07-17T18:00:00+00:00',updated_at:'2026-07-17T18:05:00+00:00',destination_id:null,error_code:'classification_not_accepted',note:'Confidential pricing case cannot enter the public library.'});
    return {contract_version:'2.0.0',model_id:'catalyst-finance.platform',platform_id:'platform_browser',name:'Connected Financial Decision Intelligence Platform',description:'Browser demonstration of governed cross-product finance handoffs.',source:{workspace_id:'workspace_browser',scenario_id:'scenario_platform',revision_id:'revision_platform',revision_number:1},products:products,artifacts:artifacts,cases:[{case_id:'case_retrofit',name:'Institutional efficiency retrofit',objective:'Publish a governed retrofit decision.',owner:'Capital Planning',status:'decided',priority:'high',artifact_ids:['artifact_market','artifact_retrofit','artifact_governance'],required_product_ids:['decision-studio','knowledge-library'],decision_packet_id:'packet_retrofit',knowledge_collection_id:'collection_retrofit'},{case_id:'case_pricing',name:'Advisory service pricing expansion',objective:'Choose a contribution-improving price.',owner:'Advisory Operations',status:'in_review',priority:'normal',artifact_ids:['artifact_pricing'],required_product_ids:['decision-studio'],decision_packet_id:'packet_pricing',knowledge_collection_id:null}],dependencies:[{edge_id:'edge_market_retrofit',upstream_artifact_id:'artifact_market',downstream_artifact_id:'artifact_retrofit',relationship:'informs',required:true,note:'Market signal informs finance assumptions.'},{edge_id:'edge_retrofit_governance',upstream_artifact_id:'artifact_retrofit',downstream_artifact_id:'artifact_governance',relationship:'evidence_for',required:true,note:'Finance publication supports governed claims.'}],handoffs:handoffs,policy:{require_governance_for_completed_handoffs:true,require_approved_artifact_for_completed_handoffs:true,require_checksums:true,minimum_case_confidence_percent:Number(form.elements.minimumConfidence.value),allowed_public_statuses:['approved','published']}};
  }

  function initializePlatform(root) {
    const section = root.querySelector('[data-scfin-platform-studio]');
    if (!section || typeof CatalystFinancePlatformEngine === 'undefined') return;
    function run() {
      try {
        const result = CatalystFinancePlatformEngine.evaluate(platformDefinition(section));
        root._scfinPlatformPayload = result;
        section.querySelector('[data-scfin-platform-npv]').textContent = money(result.portfolio.total_adjusted_npv, result.portfolio.currency);
        section.querySelector('[data-scfin-platform-risk]').textContent = money(result.portfolio.risk_adjusted_value, result.portfolio.currency);
        section.querySelector('[data-scfin-platform-cases]').textContent = String(result.case_assessments.filter(function(item){return item.status === 'decision_ready' || item.status === 'decided';}).length) + ' / ' + result.case_assessments.length;
        section.querySelector('[data-scfin-platform-handoffs]').textContent = String(result.handoffs.completed) + ' / ' + result.handoffs.total;
        const table = section.querySelector('[data-scfin-platform-table]'); table.innerHTML = '';
        result.case_assessments.forEach(function(item){const tr=document.createElement('tr');tr.innerHTML='<td>'+item.name+'</td><td>'+item.status.replaceAll('_',' ')+'</td><td>'+item.readiness_score.toFixed(1)+'%</td><td>'+money(item.risk_adjusted_value,result.portfolio.currency)+'</td>';table.appendChild(tr);});
        const flags = section.querySelector('[data-scfin-platform-flags]'); flags.innerHTML = '';
        result.flags.forEach(function(item){const li=document.createElement('li');li.textContent=item;flags.appendChild(li);});
        section.querySelector('[data-scfin-platform-manifest]').textContent = JSON.stringify(result.integration_manifest, null, 2);
        section.querySelector('[data-scfin-platform-json]').textContent = JSON.stringify(result, null, 2);
      } catch (error) {
        section.querySelector('[data-scfin-platform-json]').textContent = String(error.message || error);
      }
    }
    section.querySelector('[data-scfin-platform-run]').addEventListener('click', run);
    section.querySelector('[data-scfin-platform-download]').addEventListener('click', function(){if(root._scfinPlatformPayload)downloadJson('catalyst-finance-platform-v2.0.0.json',root._scfinPlatformPayload);});
    run();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-scfin-demo]').forEach(function (root, index) {
      initializeWorkspace(root, index);
      initializeCapitalBudgeting(root);
      initializeComparison(root);
      initializeUncertainty(root);
      initializePricing(root);
      initializeOperating(root);
      initializeSustainable(root);
      initializeGovernance(root);
      initializePlatform(root);
    });
  });
})();
