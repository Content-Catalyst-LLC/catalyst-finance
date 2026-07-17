"""Contract-validating scenario input and publication output helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .migration import normalize_scenario
from .models import FinancePublication, FinanceScenarioInput, MigrationRecord


def load_scenario(path: Path) -> tuple[FinanceScenarioInput, MigrationRecord | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Scenario input must be a JSON object")
    return normalize_scenario(payload)


def render_markdown(payload: FinancePublication | dict[str, Any]) -> str:
    data = (
        payload.model_dump(mode="json")
        if isinstance(payload, FinancePublication)
        else payload
    )
    project = data["project"]
    context = data["context"]
    results = data["results"]
    interpretation = data["interpretation"]
    narrative = data["narrative"]
    methodology = data["methodology"]
    flags = "\n".join(f"- {flag}" for flag in interpretation["flags"])
    score_lines = "\n".join(
        "- {label}: {raw_score}/100 × {weight:.0%} = {weighted_contribution} points".format(
            **component
        )
        for component in results["score_components"]
    )
    currency = context["currency"]
    return f"""# Catalyst Finance Scenario Brief

## Project

**{project["name"]}**  
Category: {project.get("category", "Sustainability finance")}

## Contract

- Contract version: {data["contract_version"]}
- Model: {data["model_id"]} v{methodology["model_version"]}
- Currency: {currency}
- Price and discount-rate basis: {context["price_basis"]}
- Frequency: {context["period_frequency"]}, {context["time_basis"]}

## Results

- Net capital cost: {currency} {results["net_capital_cost"]:,.2f}
- Carbon value per year: {currency} {results["carbon_value_per_year"]:,.2f}
- Net annual benefit: {currency} {results["net_annual_benefit"]:,.2f}
- Present value of benefits: {currency} {results["present_value_benefits"]:,.2f}
- NPV: {currency} {results["npv"]:,.2f}
- Payback years: {results["payback_years"]}
- ROI estimate: {results["roi_percent"]}%
- Benefit-cost ratio: {results["benefit_cost_ratio"]}
- Carbon cost per ton: {results["carbon_cost_per_ton"]}
- Transparent review score: {results["risk_adjusted_score"]}/100

## Score trace

{score_lines}

## Interpretation

Risk level: **{interpretation["risk_level"]}**

{narrative["decision_note"]}

## Review flags

{flags}

## Boundary

{narrative["review_boundary"]}
"""
