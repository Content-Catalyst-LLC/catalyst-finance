"""Scenario input and output helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domain import FinanceInputs, FinanceProject


def load_scenario(path: Path) -> tuple[FinanceProject, FinanceInputs]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    project_data = payload.get("project", {})
    inputs_data = payload.get("inputs", {})
    return FinanceProject(**project_data), FinanceInputs(**inputs_data)


def render_markdown(payload: dict[str, Any]) -> str:
    project = payload["project"]
    results = payload["results"]
    interpretation = payload["interpretation"]
    flags = "\n".join(f"- {flag}" for flag in interpretation["flags"])
    return f"""# Catalyst Finance Scenario Brief

## Project

**{project["name"]}**  
Category: {project.get("category", "Sustainability finance")}

## Results

- Net capital cost: ${results["net_capital_cost"]:,.2f}
- Net annual benefit: ${results["net_annual_benefit"]:,.2f}
- Present value of benefits: ${results["present_value_benefits"]:,.2f}
- NPV: ${results["npv"]:,.2f}
- Payback years: {results["payback_years"]}
- ROI estimate: {results["roi_percent"]}%
- Benefit-cost ratio: {results["benefit_cost_ratio"]}
- Carbon cost per ton: {results["carbon_cost_per_ton"]}
- Risk-adjusted score: {results["risk_adjusted_score"]}/100

## Interpretation

Risk level: **{interpretation["risk_level"]}**

{interpretation["decision_note"]}

## Review flags

{flags}

## Boundary

Educational scenario output only. Not financial, investment, tax, accounting, legal, fiduciary, or assurance advice.
"""
