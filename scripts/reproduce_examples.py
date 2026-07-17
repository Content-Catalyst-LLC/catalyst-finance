#!/usr/bin/env python3
"""Reproduce checked-in contract fixtures with a fixed timestamp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.engine import evaluate_scenario  # noqa: E402
from catalyst_finance.io import load_scenario, render_markdown  # noqa: E402

FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"


def _write(input_path: Path, output_dir: Path, stem: str) -> tuple[Path, Path]:
    scenario, migration = load_scenario(input_path)
    publication = evaluate_scenario(
        scenario,
        generated_at=FIXED_TIMESTAMP,
        migration=migration,
    )
    payload = publication.model_dump(mode="json")
    json_path = output_dir / f"{stem}.output.json"
    markdown_path = output_dir / f"{stem}.output.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(publication), encoding="utf-8")
    return json_path, markdown_path


def reproduce(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    generated.extend(
        _write(
            ROOT / "data" / "sample_finance_scenario.json",
            output_dir,
            "sample_finance_scenario",
        )
    )
    generated.extend(
        _write(
            ROOT / "data" / "legacy_v1.0.0_scenario.json",
            output_dir,
            "legacy_v1.0.0_scenario.migrated",
        )
    )
    generated.extend(
        _write(
            ROOT / "data" / "legacy_v1.1.0_scenario.json",
            output_dir,
            "legacy_v1.1.0_scenario.migrated",
        )
    )
    generated.extend(
        _write(
            ROOT / "data" / "legacy_v1.2.0_scenario.json",
            output_dir,
            "legacy_v1.2.0_scenario.migrated",
        )
    )
    generated.extend(
        _write(
            ROOT / "data" / "legacy_v1.3.0_scenario.json",
            output_dir,
            "legacy_v1.3.0_scenario.migrated",
        )
    )
    return generated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "examples")
    args = parser.parse_args()
    for path in reproduce(args.output_dir.resolve()):
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
