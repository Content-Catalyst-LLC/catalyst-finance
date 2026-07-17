#!/usr/bin/env python3
"""Generate checked-in JSON Schemas from the canonical Pydantic contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.models import (  # noqa: E402
    FinanceInterpretation,
    FinanceMetadata,
    FinancePublication,
    FinanceResults,
    FinanceScenarioInput,
)
from catalyst_finance.workspace_models import (  # noqa: E402
    FinanceWorkspace,
    ScenarioTemplate,
    WorkspaceExport,
    WorkspaceScenario,
)

SCHEMAS: list[tuple[str, type[Any]]] = [
    ("finance_input.schema.json", FinanceScenarioInput),
    ("finance_result.schema.json", FinanceResults),
    ("finance_interpretation.schema.json", FinanceInterpretation),
    ("finance_metadata.schema.json", FinanceMetadata),
    ("finance_publication.schema.json", FinancePublication),
    ("finance_workspace.schema.json", FinanceWorkspace),
    ("finance_workspace_export.schema.json", WorkspaceExport),
    ("finance_workspace_scenario.schema.json", WorkspaceScenario),
    ("finance_scenario_template.schema.json", ScenarioTemplate),
]


def generate(output_dir: Path | None = None) -> None:
    output_dir = output_dir or (ROOT / "schemas")
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMAS:
        schema = model.model_json_schema(ref_template="#/$defs/{model}")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = (
            "https://sustainablecatalyst.com/schemas/catalyst-finance/1.2.0/" + filename
        )
        path = output_dir / filename
        path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    (output_dir / "finance_scenario.schema.json").write_bytes(
        (output_dir / "finance_publication.schema.json").read_bytes()
    )


if __name__ == "__main__":
    generate()
