#!/usr/bin/env python3
"""Portable v1.1.0 smoke tests that do not require a running server."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from catalyst_finance.api import create_app  # noqa: E402
from catalyst_finance.engine import evaluate_payload  # noqa: E402
from catalyst_finance.version import __version__  # noqa: E402


def main() -> int:
    client = TestClient(create_app())
    assert client.get("/healthz").json() == {"ok": True}
    assert client.get("/api/v1/version").json()["version"] == __version__
    models = client.get("/api/v1/models").json()["models"]
    assert models[0]["model_id"] == "catalyst-finance.screening"

    scenario = json.loads(
        (ROOT / "data" / "sample_finance_scenario.json").read_text(encoding="utf-8")
    )
    publication = evaluate_payload(scenario, generated_at="2026-07-17T00:00:00+00:00")
    assert publication.metadata.version == __version__
    assert publication.results.npv > 0
    assert len(publication.results.score_components) == 4
    print("Catalyst Finance v1.1.0 smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
