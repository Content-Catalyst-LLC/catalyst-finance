"""Command-line interface for Catalyst Finance cash-flow analysis."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .cashflow import evaluate_cash_flow
from .cashflow_models import CashFlowPublication, CashFlowScenarioInput
from .models import validation_issues


def render_markdown(publication: CashFlowPublication) -> str:
    currency = publication.context.currency
    metrics = publication.metrics
    rows = "\n".join(
        f"| {row.period} | {row.inflows:,.2f} | {row.outflows:,.2f} | {row.net_cash_flow:,.2f} | {row.cumulative_cash_flow:,.2f} |"
        for row in publication.periods
    )
    flags = "\n".join(f"- {flag}" for flag in publication.interpretation.flags)
    return f"""# Catalyst Finance Cash-Flow Analysis

## Project

**{publication.project.name}**  
Category: {publication.project.category}

## Capital-budgeting metrics

- NPV: {currency} {metrics.npv:,.2f}
- Simple payback: {metrics.simple_payback_periods} periods
- Discounted payback: {metrics.discounted_payback_periods} periods
- IRR: {metrics.irr_percent_annual}% ({metrics.irr_status})
- MIRR: {metrics.mirr_percent_annual}%
- Profitability index: {metrics.profitability_index}
- Benefit-cost ratio: {metrics.benefit_cost_ratio}
- Equivalent annual value: {currency} {metrics.equivalent_annual_value:,.2f}
- Terminal value: {currency} {metrics.terminal_value:,.2f}

## Period reconciliation

| Period | Inflows | Outflows | Net | Cumulative |
|---:|---:|---:|---:|---:|
{rows}

## Review flags

{flags}

## Boundary

{publication.metadata.disclaimer}
"""


def write_csv(publication: CashFlowPublication, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "period",
                "period_label",
                "inflows",
                "outflows",
                "net_cash_flow",
                "discounted_net_cash_flow",
                "cumulative_cash_flow",
                "cumulative_discounted_cash_flow",
            ]
        )
        for row in publication.periods:
            writer.writerow(
                [
                    row.period,
                    row.period_label,
                    row.inflows,
                    row.outflows,
                    row.net_cash_flow,
                    row.discounted_net_cash_flow,
                    row.cumulative_cash_flow,
                    row.cumulative_discounted_cash_flow,
                ]
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--csv-output", type=Path)
    args = parser.parse_args(argv)
    try:
        raw: Any = json.loads(args.input.read_text(encoding="utf-8"))
        scenario = CashFlowScenarioInput.model_validate(raw)
        publication = evaluate_cash_flow(scenario)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        print(
            json.dumps({"error": "invalid_cash_flow", "issues": validation_issues(exc)})
        )
        return 2
    payload = publication.model_dump(mode="json")
    if args.json_output:
        args.json_output.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
    else:
        print(json.dumps(payload, indent=2))
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(publication), encoding="utf-8")
    if args.csv_output:
        write_csv(publication, args.csv_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
