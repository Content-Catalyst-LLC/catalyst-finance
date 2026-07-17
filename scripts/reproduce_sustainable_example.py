#!/usr/bin/env python3
"""Reproduce the Catalyst Finance v1.9.0 sustainable publication."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.sustainable import evaluate_sustainable  # noqa: E402
from catalyst_finance.sustainable_models import SustainableDefinition  # noqa: E402

FIXED = "2026-07-17T00:00:00+00:00"


def reproduce(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or (ROOT / "examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    definition = SustainableDefinition.model_validate(
        json.loads((ROOT / "data/sample_sustainable.json").read_text())
    )
    publication = evaluate_sustainable(definition, generated_at=FIXED)
    json_path = output_dir / "sample_sustainable.output.json"
    csv_path = output_dir / "sample_sustainable.summary.csv"
    json_path.write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["component", "value"])
        summary = publication.summary
        for key in [
            "carbon_value",
            "natural_capital_value",
            "net_transition_value",
            "green_financing_savings_present_value",
            "total_sustainable_value",
            "adjusted_project_npv",
        ]:
            writer.writerow([key, getattr(summary, key)])
    return [json_path, csv_path]


if __name__ == "__main__":
    reproduce()
