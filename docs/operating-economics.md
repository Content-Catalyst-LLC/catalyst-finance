# Cost, Budget, and Operating Economics

Catalyst Finance v1.7.0 evaluates operating performance using a reconciled static-budget, flexible-budget, and actual statement. Every operating row is tied to a unit, cost center, period, and source workspace revision.

## Statement structure

For each period the engine calculates budget, flexible, and actual revenue; variable costs; contribution; fixed costs; allocated overhead; and operating profit. The flexible budget uses actual volume with budget price and budget variable cost assumptions.

## Variances

Positive variance amounts are favorable. The operating-profit change is reconciled through:

- sales volume variance, valued at the budget contribution margin per unit;
- sales price variance, based on actual volume;
- variable cost spending variance, based on actual volume; and
- fixed cost spending variance, including allocated overhead.

The sum of these four components equals actual operating profit less static-budget operating profit, subject only to displayed rounding.

## Unit economics

The publication includes contribution per unit, contribution-margin percentage, break-even units and revenue, margin of safety, degree of operating leverage, and target-profit units. Break-even and target-volume measures are unavailable when the budget contribution margin per unit is zero or negative.

## Aggregation

Rows roll up by operating unit, cost center, and total organization. Amounts are summed first; ratios and break-even measures are then recomputed from the aggregated amounts.

## Boundaries

The model is decision support rather than an accounting system of record. Review cost classification, allocation bases, taxes, period timing, capacity constraints, and source-system controls before relying on a publication.
