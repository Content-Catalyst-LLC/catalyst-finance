"""Canonical Catalyst Finance v1.3.0 evaluation engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .calculation import calculate
from .interpretation import interpret
from .migration import normalize_scenario
from .models import (
    CONTRACT_VERSION,
    FinanceMetadata,
    FinanceMethodology,
    FinancePublication,
    FinanceScenarioInput,
    MigrationRecord,
)
from .narrative import narrate

DISCLAIMER = (
    "Educational software only; not financial, investment, legal, accounting, "
    "tax, fiduciary, procurement, funding, lending, or assurance advice."
)


def evaluate_scenario(
    scenario: FinanceScenarioInput,
    *,
    generated_at: str | None = None,
    migration: MigrationRecord | None = None,
) -> FinancePublication:
    results = calculate(scenario.assumptions, scenario.context)
    interpretation = interpret(scenario.assumptions, results)
    narrative = narrate(results)
    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    return FinancePublication(
        contract_version=CONTRACT_VERSION,
        model_id=scenario.model_id,
        project=scenario.project,
        context=scenario.context,
        assumptions=scenario.assumptions,
        results=results,
        interpretation=interpretation,
        narrative=narrative,
        methodology=FinanceMethodology(),
        metadata=FinanceMetadata(
            generated_at=timestamp,
            disclaimer=DISCLAIMER,
            migration=migration,
        ),
    )


def evaluate_payload(
    payload: dict[str, Any], *, generated_at: str | None = None
) -> FinancePublication:
    scenario, migration = normalize_scenario(payload)
    return evaluate_scenario(
        scenario,
        generated_at=generated_at,
        migration=migration,
    )
