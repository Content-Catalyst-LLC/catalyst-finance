(function (root, factory) {
  const engine = factory();
  if (typeof module === 'object' && module.exports) module.exports = engine;
  root.CatalystFinancePricingEngine = engine;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const CONTRACT_VERSION = '2.0.0';
  const MODEL_ID = 'catalyst-finance.pricing';
  const DISCLAIMER = 'Decision-support output only. Validate demand assumptions, cost-to-serve, market response, legal constraints, taxes, and implementation effects before use.';
  function round(value, decimals) {
    const scale = Math.pow(10, decimals);
    const result = Math.sign(value) * Math.floor(Math.abs(value) * scale + 0.5 + 1e-12) / scale;
    return Object.is(result, -0) ? 0 : result;
  }
  function classify(elasticity) {
    if (elasticity === null || elasticity === undefined) return 'undefined';
    const magnitude = Math.abs(elasticity);
    if (Math.abs(magnitude - 1) <= 1e-9) return 'unit_elastic';
    return magnitude > 1 ? 'elastic' : 'inelastic';
  }
  function observed(curve, price) {
    const points = curve.observed_points;
    let left, right, quantity, policy;
    if (price <= points[0].price) {
      left = points[0]; right = points[1]; quantity = points[0].quantity; policy = 'clamped_below_range';
    } else if (price >= points[points.length - 1].price) {
      left = points[points.length - 2]; right = points[points.length - 1]; quantity = points[points.length - 1].quantity; policy = 'clamped_above_range';
    } else {
      left = points[0]; right = points[1];
      for (let i = 1; i < points.length; i++) {
        if (price <= points[i].price) { left = points[i - 1]; right = points[i]; break; }
      }
      const fraction = (price - left.price) / (right.price - left.price);
      quantity = left.quantity + fraction * (right.quantity - left.quantity);
      policy = 'interpolated';
    }
    const slope = (right.quantity - left.quantity) / (right.price - left.price);
    const elasticity = quantity <= 0 ? null : slope * price / quantity;
    return [Math.max(0, quantity), elasticity, policy];
  }
  function segmentDemand(segment, price) {
    const curve = segment.curve;
    let quantity, elasticity, policy;
    if (curve.kind === 'linear') {
      quantity = Math.max(0, curve.intercept - curve.slope * price);
      elasticity = quantity <= 0 ? null : -curve.slope * price / quantity;
      policy = 'analytical_linear';
    } else if (curve.kind === 'constant_elasticity') {
      quantity = curve.reference_quantity * Math.pow(price / curve.reference_price, curve.elasticity);
      elasticity = curve.elasticity;
      policy = 'analytical_constant_elasticity';
    } else {
      [quantity, elasticity, policy] = observed(curve, price);
    }
    return [quantity * segment.quantity_multiplier, elasticity, policy];
  }
  function evaluatePrice(definition, price) {
    const raw = definition.segments.map(segment => [segment].concat(segmentDemand(segment, price)));
    const unconstrained = raw.reduce((sum, item) => sum + item[1], 0);
    const capacity = definition.constraints.capacity_units;
    const capacityConstrained = capacity !== null && capacity !== undefined && unconstrained > capacity;
    const scale = capacityConstrained && unconstrained > 0 ? capacity / unconstrained : 1;
    const segments = raw.map(item => ({
      segment_id: item[0].segment_id,
      label: item[0].label,
      unconstrained_quantity: round(item[1], 6),
      quantity: round(item[1] * scale, 6),
      elasticity: item[2] === null ? null : round(item[2], 6),
      demand_classification: classify(item[2]),
      interpolation_policy: item[3]
    }));
    const quantity = segments.reduce((sum, item) => sum + item.quantity, 0);
    const revenue = price * quantity;
    const costs = definition.costs;
    const unitCost = costs.unit_variable_cost + costs.unit_fulfillment_cost;
    const variableCost = quantity * unitCost + revenue * costs.channel_fee_percent / 100;
    const contribution = revenue - variableCost;
    const profit = contribution - costs.fixed_cost;
    let weightedElasticity = 0, weightedQuantity = 0;
    segments.forEach(item => {
      if (item.elasticity !== null) { weightedElasticity += item.quantity * item.elasticity; weightedQuantity += item.quantity; }
    });
    const averageElasticity = weightedQuantity <= 0 ? null : weightedElasticity / weightedQuantity;
    const contributionPerUnit = quantity <= 0 ? 0 : contribution / quantity;
    const breakEvenQuantity = contributionPerUnit <= 0 ? null : costs.fixed_cost / contributionPerUnit;
    const minimum = definition.constraints.minimum_volume_units;
    return {
      price: round(price, 6), segments: segments,
      unconstrained_quantity: round(unconstrained, 6), quantity: round(quantity, 6),
      gross_revenue: round(revenue, 6), variable_cost: round(variableCost, 6),
      contribution: round(contribution, 6), operating_profit: round(profit, 6),
      contribution_margin_percent: revenue <= 0 ? null : round(contribution / revenue * 100, 6),
      average_elasticity: averageElasticity === null ? null : round(averageElasticity, 6),
      capacity_constrained: capacityConstrained,
      minimum_volume_met: minimum === null || minimum === undefined ? null : quantity >= minimum,
      break_even_quantity: breakEvenQuantity === null ? null : round(breakEvenQuantity, 6),
      break_even_met: breakEvenQuantity === null ? null : quantity >= breakEvenQuantity
    };
  }
  function objectiveValue(row, objective) {
    return objective === 'revenue' ? row.gross_revenue : (objective === 'contribution' ? row.contribution : row.operating_profit);
  }
  function optimum(rows, objective) {
    let best = 0;
    for (let i = 1; i < rows.length; i++) {
      const candidate = objectiveValue(rows[i], objective), current = objectiveValue(rows[best], objective);
      if (candidate > current || (candidate === current && rows[i].price < rows[best].price)) best = i;
    }
    return {objective: objective, price: rows[best].price, quantity: rows[best].quantity, value: objectiveValue(rows[best], objective), row_index: best};
  }
  function priceAllowed(definition, candidate) {
    const current = definition.current_price, limit = definition.constraints.maximum_price_change_percent;
    if (current === null || current === undefined || limit === null || limit === undefined) return true;
    return Math.abs(candidate - current) / current * 100 <= limit + 1e-9;
  }
  function evaluate(definition, generatedAt) {
    if (!definition || definition.contract_version !== CONTRACT_VERSION || definition.model_id !== MODEL_ID) throw new Error('Invalid pricing contract.');
    const grid = definition.grid, increment = (grid.maximum_price - grid.minimum_price) / (grid.steps - 1);
    const rows = Array.from({length: grid.steps}, (_, i) => evaluatePrice(definition, grid.minimum_price + increment * i));
    const optima = ['revenue', 'contribution', 'profit'].map(objective => optimum(rows, objective));
    let selected = optima.find(item => item.objective === definition.objective), constrained = false;
    const allowed = rows.filter(row => priceAllowed(definition, row.price));
    if (allowed.length) {
      let constrainedRow = allowed[0];
      allowed.slice(1).forEach(row => {
        const candidate = objectiveValue(row, definition.objective), current = objectiveValue(constrainedRow, definition.objective);
        if (candidate > current || (candidate === current && row.price < constrainedRow.price)) constrainedRow = row;
      });
      if (constrainedRow.price !== selected.price) {
        constrained = true;
        selected = {objective: definition.objective, price: constrainedRow.price, quantity: constrainedRow.quantity, value: objectiveValue(constrainedRow, definition.objective), row_index: rows.indexOf(constrainedRow)};
      }
    }
    const current = definition.current_price === null || definition.current_price === undefined ? null : evaluatePrice(definition, definition.current_price);
    const currentValue = current === null ? null : objectiveValue(current, definition.objective);
    const absoluteChange = current === null ? null : round(selected.price - current.price, 6);
    const percentChange = current === null ? null : round((selected.price - current.price) / current.price * 100, 6);
    const gain = currentValue === null ? null : round(selected.value - currentValue, 6);
    let direction = 'maintain';
    if (absoluteChange !== null && absoluteChange > 1e-9) direction = 'increase';
    else if (absoluteChange !== null && absoluteChange < -1e-9) direction = 'decrease';
    const flags = [];
    if (rows.some(row => row.capacity_constrained)) flags.push('Capacity constrains demand at one or more evaluated prices.');
    if (rows.some(row => row.segments.some(segment => segment.interpolation_policy.indexOf('clamped') === 0))) flags.push('Observed demand is endpoint-clamped outside its measured price range.');
    if (rows.some(row => row.minimum_volume_met === false)) flags.push('One or more evaluated prices fall below the configured minimum volume.');
    if (constrained) flags.push('The recommended price is limited by the maximum price-change constraint.');
    if (!flags.length) flags.push('No configured capacity, volume, or price-change constraint is binding.');
    return {
      contract_version: CONTRACT_VERSION, model_id: MODEL_ID, definition: definition, rows: rows,
      current_position: current, optima: optima,
      recommendation: {
        objective: definition.objective, current_price: current === null ? null : current.price,
        recommended_price: selected.price, absolute_price_change: absoluteChange,
        percent_price_change: percentChange, current_objective_value: currentValue,
        recommended_objective_value: selected.value, expected_objective_gain: gain,
        constraint_limited: constrained,
        narrative: direction.charAt(0).toUpperCase() + direction.slice(1) + ' price to ' + definition.currency + ' ' + selected.price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' to maximize ' + definition.objective + ' within the declared grid and constraints.'
      },
      flags: flags,
      methodology: {
        model_id: MODEL_ID, model_version: CONTRACT_VERSION,
        grid_policy: 'inclusive_even_price_grid',
        observed_policy: 'piecewise_linear_with_endpoint_clamping',
        capacity_policy: 'proportional_segment_allocation',
        optimum_tie_policy: 'lowest_price',
        elasticity_policy: 'point_linear_constant_or_local_observed_quantity_weighted'
      },
      metadata: {
        generated_at: generatedAt || new Date().toISOString(), version: CONTRACT_VERSION,
        grid_rows: rows.length, constrained_rows: rows.filter(row => row.capacity_constrained).length,
        disclaimer: DISCLAIMER
      }
    };
  }
  return {CONTRACT_VERSION: CONTRACT_VERSION, MODEL_ID: MODEL_ID, evaluate: evaluate, evaluatePrice: evaluatePrice};
});
