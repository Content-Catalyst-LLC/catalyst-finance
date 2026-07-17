#!/usr/bin/env python3
"""Reproduce the checked-in v1.9.0 uncertainty publication and summary CSV."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.uncertainty import evaluate_uncertainty  # noqa: E402
from catalyst_finance.uncertainty_models import UncertaintyDefinition  # noqa: E402

FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"


def reproduce(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or (ROOT / "examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    definition = UncertaintyDefinition.model_validate_json(
        (ROOT / "data/sample_uncertainty.json").read_text(encoding="utf-8")
    )
    publication = evaluate_uncertainty(definition, generated_at=FIXED_TIMESTAMP)
    json_path = output_dir / "sample_uncertainty.output.json"
    csv_path = output_dir / "sample_uncertainty.summary.csv"
    json_path.write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
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
    return [json_path, csv_path]


if __name__ == "__main__":
    for generated_path in reproduce():
        print(f"Wrote {generated_path}")
