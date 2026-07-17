(function () {
  'use strict';

  const WORKSPACE_VERSION = '1.2.0';
  const STORAGE_PREFIX = 'catalyst-finance-workspace-v1.2.0';

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
    if (!workspace || workspace.workspace_contract_version !== WORKSPACE_VERSION) throw new Error('Workspace contract_version must be 1.2.0.');
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
        downloadJson('catalyst-finance-scenario-v1.2.0.json', root._scfinPayload);
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
      downloadJson('catalyst-finance-workspace-v1.2.0.json', bundle);
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
      downloadJson('catalyst-finance-scenario-v1.2.0.json', root._scfinPayload || CatalystFinanceEngine.evaluate(inputFromForm(form, state.workspace.defaults.currency)));
    });
    root.querySelector('[data-scfin-print]').addEventListener('click', function () { window.print(); });

    if (loaded.recovered) setStatus('Recovered unsaved changes', 'recovery'); else persistCanonical();
    loadCurrent();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-scfin-demo]').forEach(initializeWorkspace);
  });
})();
