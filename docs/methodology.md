# Catalyst Finance v1.1.0 Methodology

## Model identity

- Model ID: `catalyst-finance.screening`
- Model version: `1.1.0`
- Contract version: `1.1.0`
- Calculation basis: annual screening

## Basis policy

The model records ISO 4217 currency, nominal or real price basis, matching discount-rate basis, annual period frequency, end-of-period timing, and half-up rounding. Nominal and real bases may not be mixed within this screening model.

## Fractional horizons

Complete annual benefits are discounted at the end of each full year. A fractional final year is prorated and discounted at the fractional horizon.

## Financial calculations

The engine calculates net capital cost, annual carbon value, net annual benefit, present value of benefits, NPV, simple payback, screening ROI, benefit-cost ratio, and capital cost per lifetime emissions ton. Zero net capital cost produces `null` for ROI and benefit-cost ratio because those ratios are undefined.

External funding above capital cost does not create a negative capital cost. Net capital cost is floored at zero and the condition is flagged.

Missing emissions data excludes carbon value and produces no carbon-cost result. A negative discount rate above -100% is mathematically supported but explicitly flagged for review.

## Transparent review score

The score contains no hidden constant. It is the weighted sum of:

- Financial signal: 35%
- Payback signal: 25%
- Evidence confidence: 20%
- Implementation resilience (`100 - implementation risk`): 20%

Every publication includes the raw score, weight, weighted contribution, and rationale for each component. Interpretation thresholds are lower concern at 70 or above, moderate concern at 45–69.9, and high concern below 45.

## Separation of concerns

`calculation.py` returns model results. `interpretation.py` applies review flags and level rules. `narrative.py` creates explanatory language and the review boundary. This prevents narrative wording from changing the financial calculation.
