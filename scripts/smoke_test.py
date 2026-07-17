#!/usr/bin/env python3
"""Portable release smoke tests that do not require a running server."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from catalyst_finance.api import create_app  # noqa: E402
from catalyst_finance.domain import (  # noqa: E402
    FinanceInputs,
    FinanceProject,
    evaluate,
)
from catalyst_finance.version import __version__  # noqa: E402


def main() -> int:
    client = TestClient(create_app())
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json() == {"ok": True}
    version = client.get("/api/v1/version")
    assert version.status_code == 200
    assert version.json()["version"] == __version__

    payload = evaluate(
        FinanceProject(name="Smoke test"),
        FinanceInputs(
            capital_cost=100,
            external_funding=0,
            annual_savings=30,
            annual_operating_cost=0,
            time_horizon_years=5,
            discount_rate_percent=5,
            annual_emissions_reduced_tons=0,
            carbon_price_per_ton=0,
            confidence_percent=75,
            implementation_risk_percent=25,
        ),
        generated_at="2026-07-17T00:00:00+00:00",
    )
    assert payload["metadata"]["version"] == __version__
    assert payload["results"]["npv"] > 0
    print("Catalyst Finance v1.0.1 smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
