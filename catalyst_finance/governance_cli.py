"""Command-line interface for governed finance publications."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .governance import evaluate_governance
from .governance_migration import normalize_governance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile evidence, review, governance, and publication records."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--public-json", type=Path)
    args = parser.parse_args()
    definition = normalize_governance(
        json.loads(args.input.read_text(encoding="utf-8"))
    )
    publication = evaluate_governance(definition)
    text = json.dumps(publication.model_dump(mode="json"), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
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
                writer.writerow(
                    [
                        item.claim_id,
                        item.classification,
                        item.complete,
                        "|".join(item.metric_paths),
                        "|".join(item.source_ids),
                        "|".join(item.evidence_ids),
                    ]
                )
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(publication.decision_brief_markdown, encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(publication.decision_brief_html, encoding="utf-8")
    if args.public_json:
        args.public_json.parent.mkdir(parents=True, exist_ok=True)
        args.public_json.write_text(
            json.dumps(publication.public_payload, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
