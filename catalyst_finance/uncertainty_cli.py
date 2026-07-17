"""Command-line interface for seeded uncertainty and stress analysis."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Sequence
from pathlib import Path

from .uncertainty import evaluate_uncertainty
from .uncertainty_models import UncertaintyDefinition


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Catalyst Finance uncertainty analysis."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--seed", type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    definition = UncertaintyDefinition.model_validate(payload)
    if args.seed is not None:
        definition = definition.model_copy(
            update={
                "monte_carlo": definition.monte_carlo.model_copy(
                    update={"seed": args.seed}
                )
            }
        )
    publication = evaluate_uncertainty(definition, generated_at=args.generated_at)
    rendered = json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.summary_csv:
        args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "metric_id",
                    "mean",
                    "median",
                    "standard_deviation",
                    "minimum",
                    "maximum",
                    "probability_above_zero",
                    "probability_below_threshold",
                    "value_at_risk_95",
                    "expected_shortfall_5",
                ]
            )
            for item in publication.summaries:
                writer.writerow(
                    [
                        item.metric_id,
                        item.mean,
                        item.median,
                        item.standard_deviation,
                        item.minimum,
                        item.maximum,
                        item.probability_above_zero,
                        item.probability_below_threshold,
                        item.value_at_risk_95,
                        item.expected_shortfall_5,
                    ]
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
