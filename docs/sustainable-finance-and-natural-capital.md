# Sustainable Finance, Carbon, and Natural-Capital Accounting

Catalyst Finance v1.9.0 adds a transparent sustainable-value layer that remains separate from the base project NPV until the final reconciliation.

## Carbon accounting

The model records baseline and project emissions, computes avoided emissions, and exposes both shadow-price value and net market-credit value. The selected `carbon_valuation_method` chooses one basis (`shadow_price`, `market_credit`, `higher_of`, or `lower_of`) for the total. The two values are never added together. Eligible credit quantity is capped at avoided emissions.

## Natural capital

Each asset records category, quantity, unit, baseline and projected unit values, annual ecosystem-service value, restoration cost, and confidence. The model calculates confidence-adjusted stock uplift plus discounted services less restoration cost. This is a decision-support valuation, not a substitute for ecological condition assessment, title, rights, or assurance.

## Transition and financing value

Transition benefits and costs are probability-adjusted and discounted from their stated timing. Green-financing savings are the present value of the annual interest-rate differential over the financing term.

## Reconciliation

`total_sustainable_value` equals selected carbon value, natural-capital value, net transition value, and green-financing savings. `adjusted_project_npv` adds that amount to the disclosed base project NPV. Every publication retains the source workspace, scenario, and revision identifiers.
