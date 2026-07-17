"""Migration into the Catalyst Finance v1.1.0 input contract."""

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


def is_legacy_v100(payload: dict[str, Any]) -> bool:
    return "contract_version" not in payload and "inputs" in payload


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


def normalize_scenario(
    payload: dict[str, Any],
) -> tuple[FinanceScenarioInput, MigrationRecord | None]:
    if is_legacy_v100(payload):
        return migrate_v100(payload)
    return FinanceScenarioInput.model_validate(payload), None
