"""CLI for the Catalyst Finance pricing model."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .pricing import evaluate_pricing
from .pricing_migration import normalize_pricing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a Catalyst Finance pricing definition."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Pricing input must be a JSON object.")
    publication = evaluate_pricing(normalize_pricing(payload))
    rendered = json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "price",
                    "quantity",
                    "gross_revenue",
                    "variable_cost",
                    "contribution",
                    "operating_profit",
                    "average_elasticity",
                    "capacity_constrained",
                ]
            )
            for row in publication.rows:
                writer.writerow(
                    [
                        row.price,
                        row.quantity,
                        row.gross_revenue,
                        row.variable_cost,
                        row.contribution,
                        row.operating_profit,
                        row.average_elasticity,
                        int(row.capacity_constrained),
                    ]
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
