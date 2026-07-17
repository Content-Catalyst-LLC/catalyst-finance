"""Built-in Catalyst Finance workspace templates."""

from __future__ import annotations

from .models import FinanceInputs, FinanceProject, FinanceScenarioInput
from .workspace_models import ScenarioTemplate, WorkspaceDefaults


def _template(
    template_id: str,
    name: str,
    description: str,
    category: str,
    assumptions: FinanceInputs,
    defaults: WorkspaceDefaults | None = None,
) -> ScenarioTemplate:
    selected = defaults or WorkspaceDefaults()
    return ScenarioTemplate(
        template_id=template_id,
        name=name,
        description=description,
        category=category,
        scenario=FinanceScenarioInput(
            project=FinanceProject(name=name, category=category),
            context=selected.finance_context(),
            assumptions=assumptions,
        ),
    )


def list_templates(defaults: WorkspaceDefaults | None = None) -> list[ScenarioTemplate]:
    """Return fresh template records using the requested workspace defaults."""
    common = {
        "time_horizon_years": 10,
        "discount_rate_percent": 6,
        "annual_emissions_reduced_tons": 0,
        "carbon_price_per_ton": 0,
        "confidence_percent": 60,
        "implementation_risk_percent": 40,
    }
    return [
        _template(
            "capital-project",
            "Capital project",
            "Screen a conventional capital investment with annual savings.",
            "Capital project",
            FinanceInputs(
                capital_cost=250000,
                external_funding=0,
                annual_savings=50000,
                annual_operating_cost=5000,
                **common,
            ),
            defaults,
        ),
        _template(
            "operating-change",
            "Operating change",
            "Compare an operating process change with limited upfront investment.",
            "Operating change",
            FinanceInputs(
                capital_cost=50000,
                external_funding=0,
                annual_savings=24000,
                annual_operating_cost=6000,
                time_horizon_years=5,
                discount_rate_percent=6,
                annual_emissions_reduced_tons=0,
                carbon_price_per_ton=0,
                confidence_percent=65,
                implementation_risk_percent=35,
            ),
            defaults,
        ),
        _template(
            "pricing-decision",
            "Pricing decision",
            "Create a screening case for a pricing or revenue intervention.",
            "Pricing and revenue",
            FinanceInputs(
                capital_cost=20000,
                external_funding=0,
                annual_savings=40000,
                annual_operating_cost=10000,
                time_horizon_years=3,
                discount_rate_percent=8,
                annual_emissions_reduced_tons=0,
                carbon_price_per_ton=0,
                confidence_percent=50,
                implementation_risk_percent=50,
            ),
            defaults,
        ),
        _template(
            "sustainability-investment",
            "Sustainability investment",
            "Value operating savings and disclosed emissions reductions together.",
            "Sustainability investment",
            FinanceInputs(
                capital_cost=300000,
                external_funding=50000,
                annual_savings=55000,
                annual_operating_cost=8000,
                time_horizon_years=12,
                discount_rate_percent=5,
                annual_emissions_reduced_tons=220,
                carbon_price_per_ton=40,
                confidence_percent=70,
                implementation_risk_percent=30,
            ),
            defaults,
        ),
        _template(
            "public-value-initiative",
            "Public-value initiative",
            "Document a public-value case while keeping monetized assumptions explicit.",
            "Public value",
            FinanceInputs(
                capital_cost=180000,
                external_funding=90000,
                annual_savings=18000,
                annual_operating_cost=12000,
                time_horizon_years=8,
                discount_rate_percent=3,
                annual_emissions_reduced_tons=80,
                carbon_price_per_ton=50,
                confidence_percent=55,
                implementation_risk_percent=45,
            ),
            defaults,
        ),
    ]


def get_template(
    template_id: str, defaults: WorkspaceDefaults | None = None
) -> ScenarioTemplate | None:
    return next(
        (item for item in list_templates(defaults) if item.template_id == template_id),
        None,
    )
