#!/usr/bin/env python3
"""Reproduce the Catalyst Finance v1.9.0 comparison bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.comparison import evaluate_comparison  # noqa: E402
from catalyst_finance.comparison_cli import (  # noqa: E402
    render_html,
    render_markdown,
    write_csv,
)
from catalyst_finance.comparison_models import ComparisonDefinition  # noqa: E402

FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"


def reproduce(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = json.loads((ROOT / "data/sample_comparison.json").read_text(encoding="utf-8"))
    publication = evaluate_comparison(
        ComparisonDefinition.model_validate(raw), generated_at=FIXED_TIMESTAMP
    )
    paths = [
        output_dir / "sample_comparison.output.json",
        output_dir / "sample_comparison.output.csv",
        output_dir / "sample_comparison.output.md",
        output_dir / "sample_comparison.output.html",
    ]
    paths[0].write_text(
        json.dumps(publication.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(publication, paths[1])
    paths[2].write_text(render_markdown(publication), encoding="utf-8")
    paths[3].write_text(render_html(publication), encoding="utf-8")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "examples")
    args = parser.parse_args()
    for path in reproduce(args.output_dir.resolve()):
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
