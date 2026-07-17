# Uncertainty and Stress Review Checklist

Before relying on a v1.7.0 uncertainty publication, confirm:

1. The source workspace, scenario, and revision identifiers match the reviewed base case.
2. Every variable path resolves to the intended assumption and does not duplicate another variable unintentionally.
3. Distribution choice and parameters are supported by evidence, expert judgment, or an explicitly documented policy.
4. Normal and lognormal variables use appropriate truncation where the underlying assumption cannot be negative or exceed a physical bound.
5. Discrete probabilities sum to one and represent mutually exclusive outcomes.
6. Pairwise correlations are evidence-based, directionally plausible, and form a valid positive-semidefinite matrix.
7. Iteration count is sufficient for the decision context and the seed is retained in the decision record.
8. Rejected simulations are understood; a high rejection rate usually indicates poorly bounded distributions or incompatible assumptions.
9. Downside thresholds reflect governance criteria rather than being selected after observing the results.
10. Value-at-risk and expected shortfall are interpreted as model-tail statistics, not guaranteed worst cases.
11. Variable influence is treated as association within the configured simulation, not causal attribution.
12. Named stress cases cover material combined failures that independent variable ranges may not express.
13. Financial results are reviewed alongside non-financial, implementation, legal, equity, environmental, and operational considerations.
14. Qualified reviewers approve any investment, accounting, tax, lending, procurement, or fiduciary use.
