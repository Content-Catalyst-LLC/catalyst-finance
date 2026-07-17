#!/usr/bin/env python3
"""Reproduce checked-in scenario outputs with a fixed timestamp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.domain import evaluate  # noqa: E402
from catalyst_finance.io import load_scenario, render_markdown  # noqa: E402

FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"


def reproduce(output_dir: Path) -> tuple[Path, Path]:
    project, inputs = load_scenario(ROOT / "data" / "sample_finance_scenario.json")
    payload = evaluate(project, inputs, generated_at=FIXED_TIMESTAMP)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "sample_finance_scenario.output.json"
    markdown_path = output_dir / "sample_finance_scenario.output.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "examples")
    args = parser.parse_args()
    json_path, markdown_path = reproduce(args.output_dir.resolve())
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
