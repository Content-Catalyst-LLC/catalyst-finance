#!/usr/bin/env python3
"""Reproduce the Catalyst Finance v1.9.0 operating publication."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalyst_finance.operating import evaluate_operating  # noqa: E402
from catalyst_finance.operating_models import OperatingDefinition  # noqa: E402

FIXED = "2026-07-17T00:00:00+00:00"


def reproduce() -> None:
    definition = OperatingDefinition.model_validate(
        json.loads((ROOT / "data/sample_operating.json").read_text())
    )
    publication = evaluate_operating(definition, generated_at=FIXED)
    (ROOT / "examples/sample_operating.output.json").write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    )
    with (ROOT / "examples/sample_operating.summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "summary_id",
                "label",
                "budget_profit",
                "actual_profit",
                "profit_variance",
                "break_even_units",
                "margin_of_safety_units",
            ]
        )
        for item in [*publication.unit_summaries, publication.total_summary]:
            writer.writerow(
                [
                    item.summary_id,
                    item.label,
                    item.budget_operating_profit,
                    item.actual_operating_profit,
                    item.operating_profit_variance,
                    item.break_even_units,
                    item.margin_of_safety_units,
                ]
            )


if __name__ == "__main__":
    reproduce()
