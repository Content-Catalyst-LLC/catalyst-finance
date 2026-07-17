# Scenario Comparison, Sensitivity, and Break-Even

Catalyst Finance v1.4.0 compares complete cash-flow scenario revisions rather than untracked spreadsheet columns. Every alternative includes its workspace ID, scenario ID, revision ID, revision number, classification, cash-flow snapshot, and non-financial caveats.

## Aligned comparison

Selected metrics are aligned across alternatives. Each row reports the baseline value, alternative value, delta, and rank. The weighted ranking uses disclosed min-max normalization and explicit metric weights. A Pareto dominance check reports when one alternative is no worse on every selected metric and better on at least one. Dominance is explicitly labeled **financial only**.

## Sensitivity parameters

A parameter declares a stable ID, label, path, operation, value type, and unit. Supported paths include top-level rates and horizons, `line:<flow_id>:<field>`, `category:<category>:amount`, and the synthetic implementation-delay path. Operations can set a value, multiply an existing value, or shift implementation periods.

One-way analysis evaluates an ordered set of values. Two-way analysis evaluates a complete row-by-column grid. Each result includes a reproducibility key derived from the definition and source scenario snapshot.

## Break-even analysis

Threshold definitions declare a metric, target, bounds, tolerance, and maximum iterations. Continuous parameters use a bounded scan followed by bisection. Integer parameters evaluate each integer in range. Multiple crossings are preserved and the crossing nearest the source value is selected for the headline threshold.

## Difference explanations

Alternative explanations change one differing assumption at a time from the baseline and measure the resulting NPV impact. These impacts identify likely drivers but are not additive when assumptions interact.

## Exports

The comparison CLI and API produce contract-valid JSON. The CLI also produces aligned CSV records, Markdown review briefs, and printable standalone HTML.
