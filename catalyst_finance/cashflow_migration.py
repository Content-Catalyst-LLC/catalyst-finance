"""Migration helpers for versioned cash-flow contracts."""

from __future__ import annotations

from typing import Any

from .cashflow_models import CASHFLOW_CONTRACT_VERSION, CashFlowScenarioInput


def normalize_cash_flow(payload: dict[str, Any]) -> CashFlowScenarioInput:
    version = payload.get("contract_version")
    if version in {"1.3.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.8.0"}:
        migrated = dict(payload)
        migrated["contract_version"] = CASHFLOW_CONTRACT_VERSION
        return CashFlowScenarioInput.model_validate(migrated)
    return CashFlowScenarioInput.model_validate(payload)
