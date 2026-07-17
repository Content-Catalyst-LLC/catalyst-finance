"""Command-line interface for operating-economics publications."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .operating import evaluate_operating
from .operating_migration import normalize_operating


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a Catalyst Finance operating definition."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    definition = normalize_operating(json.loads(args.input.read_text(encoding="utf-8")))
    publication = evaluate_operating(definition)
    text = json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "unit_id",
                    "period",
                    "label",
                    "budget_profit",
                    "actual_profit",
                    "profit_variance",
                    "break_even_units",
                    "margin_of_safety_units",
                ]
            )
            for row in publication.rows:
                writer.writerow(
                    [
                        row.unit_id,
                        row.period,
                        row.label,
                        row.budget_operating_profit,
                        row.actual_operating_profit,
                        row.variances[-1].amount,
                        row.break_even_units,
                        row.margin_of_safety_units,
                    ]
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
