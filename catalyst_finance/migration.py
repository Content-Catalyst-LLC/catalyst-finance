"""Migration into the Catalyst Finance v1.2.0 input contract."""

from __future__ import annotations

from typing import Any

from .models import (
    CONTRACT_VERSION,
    MODEL_ID,
    FinanceContext,
    FinanceInputs,
    FinanceProject,
    FinanceScenarioInput,
    MigrationRecord,
)

LEGACY_FIELDS = [
    "project.name",
    "project.category",
    "inputs.capital_cost",
    "inputs.external_funding",
    "inputs.annual_savings",
    "inputs.annual_operating_cost",
    "inputs.time_horizon_years",
    "inputs.discount_rate_percent",
    "inputs.annual_emissions_reduced_tons",
    "inputs.carbon_price_per_ton",
    "inputs.confidence_percent",
    "inputs.implementation_risk_percent",
]

V110_FIELDS = [
    "model_id",
    "project.name",
    "project.category",
    "context.currency",
    "context.price_basis",
    "context.discount_rate_basis",
    "context.period_frequency",
    "context.time_basis",
    "context.rounding_policy",
    "context.monetary_decimals",
    "context.ratio_decimals",
    "context.score_decimals",
    "assumptions.capital_cost",
    "assumptions.external_funding",
    "assumptions.annual_savings",
    "assumptions.annual_operating_cost",
    "assumptions.time_horizon_years",
    "assumptions.discount_rate_percent",
    "assumptions.annual_emissions_reduced_tons",
    "assumptions.carbon_price_per_ton",
    "assumptions.confidence_percent",
    "assumptions.implementation_risk_percent",
]


def is_legacy_v100(payload: dict[str, Any]) -> bool:
    return "contract_version" not in payload and "inputs" in payload


def is_v110(payload: dict[str, Any]) -> bool:
    return payload.get("contract_version") == "1.1.0"


def migrate_v100(
    payload: dict[str, Any],
) -> tuple[FinanceScenarioInput, MigrationRecord]:
    project_data = payload.get("project")
    input_data = payload.get("inputs")
    if not isinstance(project_data, dict) or not isinstance(input_data, dict):
        raise ValueError("Legacy scenario requires project and inputs objects")
    scenario = FinanceScenarioInput(
        contract_version=CONTRACT_VERSION,
        model_id=MODEL_ID,
        project=FinanceProject.model_validate(project_data),
        context=FinanceContext(),
        assumptions=FinanceInputs.model_validate(input_data),
    )
    migration = MigrationRecord(
        source_contract_version="1.0.0",
        preserved_fields=list(LEGACY_FIELDS),
    )
    return scenario, migration


def migrate_v110(
    payload: dict[str, Any],
) -> tuple[FinanceScenarioInput, MigrationRecord]:
    migrated = dict(payload)
    migrated["contract_version"] = CONTRACT_VERSION
    scenario = FinanceScenarioInput.model_validate(migrated)
    return scenario, MigrationRecord(
        source_contract_version="1.1.0",
        preserved_fields=list(V110_FIELDS),
    )


def normalize_scenario(
    payload: dict[str, Any],
) -> tuple[FinanceScenarioInput, MigrationRecord | None]:
    if is_legacy_v100(payload):
        return migrate_v100(payload)
    if is_v110(payload):
        return migrate_v110(payload)
    return FinanceScenarioInput.model_validate(payload), None
