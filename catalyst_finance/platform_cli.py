"""CLI for the connected financial decision-intelligence platform."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from .models import validation_issues
from .platform import evaluate_platform
from .platform_migration import normalize_platform


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("input", type=Path, help="Platform definition JSON")
    value.add_argument("--output", type=Path, help="Write publication JSON")
    value.add_argument("--generated-at", help="Override publication timestamp")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        publication = evaluate_platform(
            normalize_platform(payload), generated_at=args.generated_at
        )
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        print(
            json.dumps({"error": "invalid_platform", "issues": validation_issues(exc)})
        )
        return 2
    rendered = json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
