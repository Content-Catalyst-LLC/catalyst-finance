# Uncertainty, Monte Carlo, and Stress Testing

Catalyst Finance v1.5.0 adds a seeded uncertainty model around the canonical period cash-flow engine. It is designed for transparent decision support: every uncertain variable points to an explicit scenario parameter, every distribution is declared, correlation assumptions are reviewable, and the seed makes the simulation reproducible.

## Supported distributions

- **Uniform:** minimum and maximum.
- **Triangular:** minimum, most likely value, and maximum.
- **Normal:** arithmetic mean and standard deviation, with optional truncation.
- **Lognormal:** log-space mean and standard deviation, with optional truncation.
- **Discrete:** explicit values and probabilities that sum to one.

Variables use the same parameter-path contract as sensitivity analysis, including top-level rates, individual cash-flow line fields, category-wide amounts, multipliers, and implementation-period shifts.

## Correlation

Pairwise coefficients populate a symmetric correlation matrix. The engine validates that the matrix is positive semidefinite and applies a Cholesky factor to standard-normal draws. Distribution-specific inverse transforms then create a Gaussian copula. Invalid matrices fail rather than being silently repaired.

## Reproducibility

The simulator uses a documented XorShift32 generator and Box–Muller normal transform in Python and JavaScript. A fixed seed, definition, and engine version produce the same retained samples and summary statistics in both runtimes. The publication records the seed, configured and completed iterations, rejected draws, and a SHA-256 reproducibility key.

## Risk outputs

For every selected metric, the publication includes:

- mean, median, population standard deviation, minimum, and maximum;
- configured percentiles;
- probability above zero;
- probability below a configured downside threshold;
- lower-tail 95% value-at-risk cutoff;
- expected shortfall across the worst 5% of outcomes;
- a deterministic histogram;
- Pearson variable-to-outcome influence rankings.

These values describe the configured model and assumptions. They are not forecasts, guarantees, or investment recommendations.

## Stress tests

Stress cases apply multiple parameter substitutions in sequence and run the deterministic cash-flow engine. Each result reports absolute metrics, deltas from the unmodified base case, the applied adjustments, and downside-threshold flags. Stress cases and Monte Carlo analysis are deliberately separate: stress tests represent named adverse narratives, while Monte Carlo represents a probability model.

## Command line

```bash
catalyst-finance-uncertainty data/sample_uncertainty.json \
  --output outputs/sample_uncertainty.output.json \
  --summary-csv outputs/sample_uncertainty.summary.csv \
  --generated-at 2026-07-17T00:00:00+00:00
```

Use `--seed` to override the checked-in seed without modifying the input definition.

## API

`POST /api/v1/uncertainty/evaluate` accepts the uncertainty definition and returns the complete publication.

Workspace routes preserve uncertainty definitions as append-only revisions:

- `POST /api/v1/workspaces/{workspace_id}/uncertainty-analyses`
- `POST /api/v1/workspaces/{workspace_id}/uncertainty-analyses/{analysis_id}/revisions`
- `DELETE /api/v1/workspaces/{workspace_id}/uncertainty-analyses/{analysis_id}`
