#!/usr/bin/env python3
"""Reproduce the Catalyst Finance v2.0.0 connected-platform publication."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.platform import evaluate_platform  # noqa: E402
from catalyst_finance.platform_migration import normalize_platform  # noqa: E402

GENERATED_AT = "2026-07-17T18:30:00+00:00"


def reproduce(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or (ROOT / "examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    definition = normalize_platform(
        json.loads((ROOT / "data/sample_platform.json").read_text(encoding="utf-8"))
    )
    publication = evaluate_platform(definition, generated_at=GENERATED_AT)
    path = output_dir / "sample_platform.output.json"
    path.write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = output_dir / "sample_platform.integration-manifest.json"
    manifest.write_text(
        json.dumps(publication.integration_manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return [path, manifest]


if __name__ == "__main__":
    reproduce()
