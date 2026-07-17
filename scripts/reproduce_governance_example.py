#!/usr/bin/env python3
"""Reproduce the Catalyst Finance v1.9.0 governance publication."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalyst_finance.governance import evaluate_governance  # noqa: E402
from catalyst_finance.governance_models import GovernanceDefinition  # noqa: E402

FIXED = "2026-07-17T00:00:00+00:00"


def reproduce(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or ROOT / "examples"
    output_dir.mkdir(parents=True, exist_ok=True)
    definition = GovernanceDefinition.model_validate(
        json.loads((ROOT / "data/sample_governance.json").read_text())
    )
    publication = evaluate_governance(definition, generated_at=FIXED)
    paths = [
        output_dir / "sample_governance.output.json",
        output_dir / "sample_governance.trace.csv",
        output_dir / "sample_governance.brief.md",
        output_dir / "sample_governance.brief.html",
        output_dir / "sample_governance.public.json",
    ]
    paths[0].write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    )
    with paths[1].open("w", newline="", encoding="utf-8") as h:
        w = csv.writer(h)
        w.writerow(
            [
                "claim_id",
                "classification",
                "complete",
                "metric_paths",
                "source_ids",
                "evidence_ids",
            ]
        )
        for item in publication.trace_matrix:
            w.writerow(
                [
                    item.claim_id,
                    item.classification,
                    item.complete,
                    "|".join(item.metric_paths),
                    "|".join(item.source_ids),
                    "|".join(item.evidence_ids),
                ]
            )
    paths[2].write_text(publication.decision_brief_markdown)
    paths[3].write_text(publication.decision_brief_html)
    paths[4].write_text(json.dumps(publication.public_payload, indent=2) + "\n")
    return paths


if __name__ == "__main__":
    reproduce()
