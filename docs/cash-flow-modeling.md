# Cash-Flow Modeling and Capital Budgeting

Catalyst Finance v1.5.0 models cash flows from period 0 through a declared analysis horizon. Period 0 is undiscounted; later flows occur at the end of each selected monthly, quarterly, or annual period.

## Sign convention

Users enter non-negative amounts and select a category. Revenue, savings, avoided costs, grants, rebates, residual value, working-capital recovery, and other benefits are inflows. Capital cost, operating cost, decommissioning cost, working capital, and other costs are outflows.

## Scheduling

Each line has a start period, optional end period, interval, and annual escalation rate. One-time and irregular flows use a single period. Recurring lines expand through the end period. Annual escalation is converted by elapsed years, preserving the selected frequency.

## Basis controls

The cash-flow price basis and discount-rate basis must both be nominal or both be real. Every line must use the same basis. A mismatch is a contract error rather than a silent warning.

## Metrics

- NPV includes every modeled category.
- Simple and discounted payback use linear interpolation within the first crossing period.
- IRR reports every detected root. Multiple sign changes mark IRR as ambiguous and suppress a single headline IRR.
- MIRR uses disclosed finance and reinvestment rates.
- Profitability index includes all inflows, including grants and rebates.
- Benefit-cost ratio excludes grants and rebates as transfers.
- Equivalent annual value annualizes NPV over the declared horizon.
- Terminal value includes residual value, working-capital recovery, and decommissioning in the final period.

Every metric includes a machine-readable trace of included categories, excluded categories, source flow IDs, formula, and interpretation notes.
