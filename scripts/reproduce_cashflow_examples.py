#!/usr/bin/env python3
"""Reproduce Catalyst Finance v1.7.0 cash-flow fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.cashflow import evaluate_cash_flow  # noqa: E402
from catalyst_finance.cashflow_cli import render_markdown, write_csv  # noqa: E402
from catalyst_finance.cashflow_models import CashFlowScenarioInput  # noqa: E402

FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"
FILES = [
    "sample_cash_flow_scenario.json",
    "irregular_cash_flow_scenario.json",
    "negative_cash_flow_scenario.json",
    "zero_cost_cash_flow_scenario.json",
    "multiple_sign_cash_flow_scenario.json",
]


def reproduce(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for filename in FILES:
        raw = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
        scenario = CashFlowScenarioInput.model_validate(raw)
        publication = evaluate_cash_flow(scenario, generated_at=FIXED_TIMESTAMP)
        stem = filename.removesuffix(".json")
        json_path = output_dir / f"{stem}.output.json"
        md_path = output_dir / f"{stem}.output.md"
        csv_path = output_dir / f"{stem}.periods.csv"
        json_path.write_text(
            json.dumps(publication.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(render_markdown(publication), encoding="utf-8")
        write_csv(publication, csv_path)
        generated.extend([json_path, md_path, csv_path])
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
