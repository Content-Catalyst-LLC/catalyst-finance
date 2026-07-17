"""Command-line interface for sustainable-finance publications."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .sustainable import evaluate_sustainable
from .sustainable_migration import normalize_sustainable


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate sustainable finance and natural capital."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    definition = normalize_sustainable(
        json.loads(args.input.read_text(encoding="utf-8"))
    )
    publication = evaluate_sustainable(definition)
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
            writer.writerow(["component", "value"])
            summary = publication.summary
            writer.writerows(
                [
                    ["carbon_value", summary.carbon_value],
                    ["natural_capital_value", summary.natural_capital_value],
                    ["net_transition_value", summary.net_transition_value],
                    [
                        "green_financing_savings_present_value",
                        summary.green_financing_savings_present_value,
                    ],
                    ["total_sustainable_value", summary.total_sustainable_value],
                    ["adjusted_project_npv", summary.adjusted_project_npv],
                ]
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
