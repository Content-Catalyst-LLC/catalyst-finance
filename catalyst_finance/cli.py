"""Primary Catalyst Finance command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from .engine import evaluate_scenario
from .io import load_scenario, render_markdown
from .models import validation_issues
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a contract-valid Catalyst Finance scenario brief."
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument(
        "--generated-at",
        help="Override the ISO-8601 generation timestamp for reproducible fixtures.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scenario, migration = load_scenario(args.input)
        publication = evaluate_scenario(
            scenario,
            generated_at=args.generated_at,
            migration=migration,
        )
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"error": "invalid_finance_scenario", "issues": validation_issues(exc)},
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    payload = publication.model_dump(mode="json")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(publication), encoding="utf-8")

    if not args.json_out and not args.markdown_out:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
