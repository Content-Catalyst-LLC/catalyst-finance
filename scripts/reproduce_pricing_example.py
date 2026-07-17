#!/usr/bin/env python3
"""Reproduce the checked-in pricing publication and CSV table."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalyst_finance.pricing import evaluate_pricing  # noqa: E402
from catalyst_finance.pricing_models import PricingDefinition  # noqa: E402


def reproduce(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or (ROOT / "examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    definition = PricingDefinition.model_validate_json(
        (ROOT / "data/sample_pricing.json").read_text()
    )
    publication = evaluate_pricing(definition, generated_at="2026-07-17T00:00:00+00:00")
    (output_dir / "sample_pricing.output.json").write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "sample_pricing.curve.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "price",
                "quantity",
                "gross_revenue",
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
                    row.contribution,
                    row.operating_profit,
                    row.average_elasticity,
                    int(row.capacity_constrained),
                ]
            )
    return [
        output_dir / "sample_pricing.output.json",
        output_dir / "sample_pricing.curve.csv",
    ]


if __name__ == "__main__":
    for path in reproduce():
        print(f"Wrote {path}")
