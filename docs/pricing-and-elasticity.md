# Demand, Elasticity, Pricing, and Revenue

Catalyst Finance v1.9.0 evaluates declared demand assumptions across an inclusive price grid. It supports three curve forms:

- **Linear:** `Q = a - bP`, constrained to non-negative quantity.
- **Constant elasticity:** `Q = Qref × (P / Pref)^e`, where `e < 0`.
- **Observed:** piecewise-linear interpolation between measured points, with explicit endpoint clamping outside the observed range.

Multiple segments are evaluated independently and aggregated. When demand exceeds capacity, quantity is allocated proportionally across segments. Each price row records gross revenue, variable cost, contribution, operating profit, contribution margin, quantity-weighted elasticity, capacity status, minimum-volume status, and break-even quantity.

The engine reports separate optima for revenue, contribution, and operating profit. A selected recommendation may be limited by the configured maximum price-change constraint. Ties use the lowest price. The model does not infer causality, competitor reaction, taxes, regulation, customer fairness, or long-term retention effects.
