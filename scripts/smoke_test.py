#!/usr/bin/env python3
"""Portable v2.0.0 smoke tests that do not require a running server."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from catalyst_finance.api import create_app  # noqa: E402
from catalyst_finance.engine import evaluate_payload  # noqa: E402
from catalyst_finance.repositories import JsonWorkspaceRepository  # noqa: E402
from catalyst_finance.version import __version__  # noqa: E402
from catalyst_finance.workspace import WorkspaceService  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="catalyst-finance-smoke-") as tmp:
        repository = JsonWorkspaceRepository(Path(tmp))
        client = TestClient(create_app(repository))
        assert client.get("/healthz").json() == {"ok": True}
        assert client.get("/api/v1/version").json()["version"] == __version__
        models = client.get("/api/v1/models").json()["models"]
        assert [item["model_id"] for item in models] == [
            "catalyst-finance.screening",
            "catalyst-finance.cash-flow",
            "catalyst-finance.comparison",
            "catalyst-finance.uncertainty",
            "catalyst-finance.pricing",
            "catalyst-finance.operating",
            "catalyst-finance.governance",
            "catalyst-finance.sustainable",
            "catalyst-finance.platform",
        ]
        assert len(client.get("/api/v1/templates").json()["templates"]) == 5

        scenario = json.loads(
            (ROOT / "data" / "sample_finance_scenario.json").read_text(encoding="utf-8")
        )
        publication = evaluate_payload(
            scenario, generated_at="2026-07-17T00:00:00+00:00"
        )
        assert publication.metadata.version == __version__
        assert publication.results.npv > 0
        assert len(publication.results.score_components) == 4

        cashflow = json.loads(
            (ROOT / "data" / "sample_cash_flow_scenario.json").read_text(
                encoding="utf-8"
            )
        )
        cashflow_response = client.post("/api/v1/cash-flow/evaluate", json=cashflow)
        assert cashflow_response.status_code == 200
        cashflow_publication = cashflow_response.json()
        assert cashflow_publication["model_id"] == "catalyst-finance.cash-flow"
        assert cashflow_publication["metadata"]["version"] == __version__
        assert cashflow_publication["metrics"]["npv"] == 198884.69
        assert len(cashflow_publication["periods"]) == 11

        comparison = json.loads(
            (ROOT / "data" / "sample_comparison.json").read_text(encoding="utf-8")
        )
        comparison_response = client.post("/api/v1/compare", json=comparison)
        assert comparison_response.status_code == 200
        comparison_publication = comparison_response.json()
        assert comparison_publication["model_id"] == "catalyst-finance.comparison"
        assert comparison_publication["metadata"]["version"] == __version__
        assert len(comparison_publication["alternatives"]) == 3
        assert comparison_publication["rankings"][0]["alternative_id"] == "upside"
        assert all(
            result["status"] in {"found", "already_at_target"}
            for result in comparison_publication["break_even_results"]
        )

        uncertainty = json.loads(
            (ROOT / "data" / "sample_uncertainty.json").read_text(encoding="utf-8")
        )
        uncertainty["monte_carlo"]["iterations"] = 100
        uncertainty["monte_carlo"]["retain_samples"] = 5
        uncertainty_response = client.post(
            "/api/v1/uncertainty/evaluate", json=uncertainty
        )
        assert uncertainty_response.status_code == 200
        uncertainty_publication = uncertainty_response.json()
        assert uncertainty_publication["model_id"] == "catalyst-finance.uncertainty"
        assert uncertainty_publication["metadata"]["version"] == __version__
        assert uncertainty_publication["metadata"]["configured_iterations"] == 100
        assert uncertainty_publication["metadata"]["completed_iterations"] > 0
        assert len(uncertainty_publication["stress_results"]) == 3

        pricing = json.loads(
            (ROOT / "data" / "sample_pricing.json").read_text(encoding="utf-8")
        )
        pricing_response = client.post("/api/v1/pricing/evaluate", json=pricing)
        assert pricing_response.status_code == 200
        pricing_publication = pricing_response.json()
        assert pricing_publication["model_id"] == "catalyst-finance.pricing"
        assert pricing_publication["metadata"]["version"] == __version__
        assert pricing_publication["recommendation"]["recommended_price"] == 55.0
        assert len(pricing_publication["rows"]) == 51

        operating = json.loads(
            (ROOT / "data" / "sample_operating.json").read_text(encoding="utf-8")
        )
        operating_response = client.post("/api/v1/operating/evaluate", json=operating)
        assert operating_response.status_code == 200
        operating_publication = operating_response.json()
        assert operating_publication["model_id"] == "catalyst-finance.operating"
        assert operating_publication["metadata"]["version"] == __version__
        assert (
            operating_publication["total_summary"]["operating_profit_variance"]
            == 2185.0
        )
        assert len(operating_publication["rows"]) == 4

        sustainable = json.loads(
            (ROOT / "data" / "sample_sustainable.json").read_text(encoding="utf-8")
        )
        sustainable_response = client.post(
            "/api/v1/sustainable/evaluate", json=sustainable
        )
        assert sustainable_response.status_code == 200
        sustainable_publication = sustainable_response.json()
        assert sustainable_publication["model_id"] == "catalyst-finance.sustainable"
        assert sustainable_publication["metadata"]["version"] == __version__
        assert sustainable_publication["carbon"]["avoided_emissions_tco2e"] == 4500.0
        assert sustainable_publication["summary"]["adjusted_project_npv"] == 1526250.9

        governance = json.loads(
            (ROOT / "data" / "sample_governance.json").read_text(encoding="utf-8")
        )
        governance_response = client.post(
            "/api/v1/governance/evaluate", json=governance
        )
        assert governance_response.status_code == 200
        governance_publication = governance_response.json()
        assert governance_publication["model_id"] == "catalyst-finance.governance"
        assert governance_publication["metadata"]["version"] == __version__
        assert governance_publication["readiness"]["status"] == "published"
        assert governance_publication["readiness"]["fully_traced_headline_count"] == 2
        assert len(governance_publication["public_payload"]["sources"]) == 2

        platform = json.loads(
            (ROOT / "data" / "sample_platform.json").read_text(encoding="utf-8")
        )
        platform_response = client.post("/api/v1/platform/evaluate", json=platform)
        assert platform_response.status_code == 200
        platform_publication = platform_response.json()
        assert platform_publication["model_id"] == "catalyst-finance.platform"
        assert platform_publication["metadata"]["version"] == __version__
        assert platform_publication["portfolio"]["risk_adjusted_value"] == 1580250.61
        assert platform_publication["handoffs"]["completed"] == 5

        service = WorkspaceService(repository)
        workspace = service.create_workspace("Smoke workspace")
        workspace = service.create_scenario(workspace.workspace_id, "Smoke scenario")
        reopened = service.get_workspace(workspace.workspace_id)
        assert reopened.scenarios[0].revisions[0].model_version == __version__

    print("Catalyst Finance v2.0.0 smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
