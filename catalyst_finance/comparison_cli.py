"""Command-line interface for reproducible scenario comparison artifacts."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .comparison import evaluate_comparison
from .comparison_models import ComparisonDefinition, ComparisonPublication
from .models import validation_issues


def render_markdown(publication: ComparisonPublication) -> str:
    metric_rows: list[str] = []
    for row in publication.aligned_metrics:
        cells = " | ".join(
            "—" if item.value is None else f"{item.value:,.4f}" for item in row.values
        )
        metric_rows.append(f"| {row.label} | {cells} |")
    headings = " | ".join(item.label for item in publication.alternatives)
    separators = " | ".join("---:" for _ in publication.alternatives)
    ranking_rows = "\n".join(
        f"| {item.rank} | {item.label} | {item.weighted_score:.4f} | "
        f"{', '.join(item.dominates) or '—'} | {', '.join(item.dominated_by) or '—'} |"
        for item in publication.rankings
    )
    threshold_rows = (
        "\n".join(
            f"| {item.threshold_id} | {item.parameter.label} | {item.status} | "
            f"{item.threshold_value if item.threshold_value is not None else '—'} |"
            for item in publication.break_even_results
        )
        or "| — | — | — | — |"
    )
    caveats = "\n".join(
        f"- **{item.label}:** "
        + ("; ".join(item.non_financial_caveats) or "None recorded")
        for item in publication.alternatives
    )
    return f"""# Catalyst Finance Scenario Comparison

## {publication.definition.name}

{publication.definition.description}

## Aligned metrics

| Metric | {headings} |
|---|{separators}|
{chr(10).join(metric_rows)}

## Weighted ranking

| Rank | Alternative | Score | Dominates | Dominated by |
|---:|---|---:|---|---|
{ranking_rows}

## Break-even thresholds

| Definition | Parameter | Status | Threshold |
|---|---|---|---:|
{threshold_rows}

## Non-financial caveats

{caveats}

## Boundary

{publication.metadata.disclaimer}
"""


def render_html(publication: ComparisonPublication) -> str:
    markdown = render_markdown(publication)
    body = "\n".join(f"<p>{html.escape(line)}</p>" for line in markdown.splitlines())
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(publication.definition.name)}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;line-height:1.5}}
p{{margin:.35rem 0;white-space:pre-wrap}}@media print{{body{{margin:0;max-width:none}}}}
</style>
</head>
<body>{body}</body>
</html>
"""


def write_csv(publication: ComparisonPublication, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "record_type",
                "metric_or_analysis_id",
                "alternative_id",
                "label",
                "value",
                "delta_or_score",
                "rank_or_status",
                "source_revision_id",
            ]
        )
        sources = {
            item.alternative_id: item.source for item in publication.alternatives
        }
        for row in publication.aligned_metrics:
            for value in row.values:
                writer.writerow(
                    [
                        "aligned_metric",
                        row.metric_id,
                        value.alternative_id,
                        value.label,
                        value.value,
                        value.delta_from_baseline,
                        value.rank,
                        sources[value.alternative_id].revision_id,
                    ]
                )
        for ranking in publication.rankings:
            writer.writerow(
                [
                    "ranking",
                    "weighted_score",
                    ranking.alternative_id,
                    ranking.label,
                    ranking.weighted_score,
                    "",
                    ranking.rank,
                    sources[ranking.alternative_id].revision_id,
                ]
            )
        for result in publication.one_way_sensitivities:
            for point in result.points:
                writer.writerow(
                    [
                        "one_way_sensitivity",
                        result.sensitivity_id,
                        result.alternative_id,
                        result.parameter.label,
                        point.metric_value,
                        point.parameter_value,
                        "",
                        sources[result.alternative_id].revision_id,
                    ]
                )
        for result in publication.break_even_results:
            writer.writerow(
                [
                    "break_even",
                    result.threshold_id,
                    result.alternative_id,
                    result.parameter.label,
                    result.threshold_value,
                    result.metric_value,
                    result.status,
                    sources[result.alternative_id].revision_id,
                ]
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--html-output", type=Path)
    args = parser.parse_args(argv)
    try:
        raw: Any = json.loads(args.input.read_text(encoding="utf-8"))
        definition = ComparisonDefinition.model_validate(raw)
        publication = evaluate_comparison(definition)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        print(
            json.dumps(
                {"error": "invalid_comparison", "issues": validation_issues(exc)}
            )
        )
        return 2
    payload = publication.model_dump(mode="json")
    if args.json_output:
        args.json_output.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
    else:
        print(json.dumps(payload, indent=2))
    if args.csv_output:
        write_csv(publication, args.csv_output)
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(publication), encoding="utf-8")
    if args.html_output:
        args.html_output.write_text(render_html(publication), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
