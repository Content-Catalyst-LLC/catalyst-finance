#!/usr/bin/env python3
"""Catalyst Finance v1.4.0 release contract."""

from __future__ import annotations

import argparse
import compileall
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VERSION = "1.4.0"
SCREENING_MODEL_ID = "catalyst-finance.screening"
CASHFLOW_MODEL_ID = "catalyst-finance.cash-flow"
COMPARISON_MODEL_ID = "catalyst-finance.comparison"
FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"
CASHFLOW_FIXTURES = [
    "sample_cash_flow_scenario.json",
    "irregular_cash_flow_scenario.json",
    "negative_cash_flow_scenario.json",
    "zero_cost_cash_flow_scenario.json",
    "multiple_sign_cash_flow_scenario.json",
]


class ReleaseError(RuntimeError):
    """Raised when a release contract fails."""


def run(
    command: Sequence[str], *, cwd: Path = ROOT, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print("RUN:", " ".join(command))
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=capture,
        text=True,
    )
    if completed.returncode:
        if capture:
            print(completed.stdout)
            print(completed.stderr, file=sys.stderr)
        raise ReleaseError(
            f"Command failed with status {completed.returncode}: {' '.join(command)}"
        )
    return completed


def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        raise ReleaseError(f"Required release path is missing: {path}")
    return target


def load_json(path: str) -> dict[str, Any]:
    value = json.loads(require(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReleaseError(f"Expected a JSON object: {path}")
    return value


def _match(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        raise ReleaseError(f"Could not find version in {label}")
    return match.group(1)


def check_versions() -> None:
    pyproject = tomllib.loads(require("pyproject.toml").read_text(encoding="utf-8"))
    plugin_text = require(
        "wordpress/catalyst-finance-demo/catalyst-finance-demo.php"
    ).read_text(encoding="utf-8")
    browser_paths = {
        "screening browser": "wordpress/catalyst-finance-demo/assets/catalyst-finance-engine.js",
        "cash-flow browser": "wordpress/catalyst-finance-demo/assets/catalyst-finance-cashflow-engine.js",
        "comparison browser": "wordpress/catalyst-finance-demo/assets/catalyst-finance-comparison-engine.js",
    }
    package_text = require("catalyst_finance/version.py").read_text(encoding="utf-8")
    manifest = load_json("catalyst_finance_manifest.json")
    examples = {
        "screening": load_json("examples/sample_finance_scenario.output.json"),
        "cash-flow": load_json("examples/sample_cash_flow_scenario.output.json"),
        "comparison": load_json("examples/sample_comparison.output.json"),
    }
    schemas = {
        name: load_json(f"schemas/{name}")
        for name in [
            "finance_input.schema.json",
            "finance_publication.schema.json",
            "cash_flow_input.schema.json",
            "cash_flow_publication.schema.json",
            "comparison_definition.schema.json",
            "comparison_publication.schema.json",
            "finance_workspace.schema.json",
        ]
    }
    workspace_export = load_json("examples/sample_finance_workspace.export.json")
    observed: dict[str, str] = {
        "VERSION": require("VERSION").read_text(encoding="utf-8").strip(),
        "pyproject": pyproject["project"]["version"],
        "package": _match(r'__version__ = "([^"]+)"', package_text, "package"),
        "plugin": _match(r"Version:\s*([0-9.]+)", plugin_text, "plugin"),
        "plugin constant": _match(
            r"CATALYST_FINANCE_DEMO_VERSION', '([0-9.]+)'",
            plugin_text,
            "plugin constant",
        ),
        "manifest": manifest["version"],
        "manifest contract": manifest["contract_version"],
        "manifest methodology": manifest["methodology_version"],
        "manifest workspace": manifest["workspace_contract_version"],
        "screening example": examples["screening"]["metadata"]["version"],
        "screening example contract": examples["screening"]["contract_version"],
        "cash-flow example": examples["cash-flow"]["metadata"]["version"],
        "cash-flow example contract": examples["cash-flow"]["contract_version"],
        "comparison example": examples["comparison"]["metadata"]["version"],
        "comparison example contract": examples["comparison"]["contract_version"],
        "workspace export": workspace_export["export_contract_version"],
        "workspace record": workspace_export["workspace"]["workspace_contract_version"],
    }
    for label, path in browser_paths.items():
        observed[label] = _match(
            r"const CONTRACT_VERSION = '([0-9.]+)'",
            require(path).read_text(encoding="utf-8"),
            label,
        )
    for name, schema in schemas.items():
        property_name = (
            "workspace_contract_version"
            if name == "finance_workspace.schema.json"
            else "contract_version"
        )
        observed[f"schema {name}"] = schema["properties"][property_name]["const"]

    mismatches = {name: value for name, value in observed.items() if value != VERSION}
    if mismatches:
        raise ReleaseError(f"Version contract failed: {mismatches}")
    expected_model_ids = {
        "model_id": SCREENING_MODEL_ID,
        "cash_flow_model_id": CASHFLOW_MODEL_ID,
        "comparison_model_id": COMPARISON_MODEL_ID,
    }
    if any(manifest.get(key) != value for key, value in expected_model_ids.items()):
        raise ReleaseError("Manifest model identifier contract failed.")
    if examples["screening"]["model_id"] != SCREENING_MODEL_ID:
        raise ReleaseError("Screening model identifier contract failed.")
    if examples["cash-flow"]["model_id"] != CASHFLOW_MODEL_ID:
        raise ReleaseError("Cash-flow model identifier contract failed.")
    if examples["comparison"]["model_id"] != COMPARISON_MODEL_ID:
        raise ReleaseError("Comparison model identifier contract failed.")
    print(f"PASS: {len(observed)} version surfaces report {VERSION}.")


def check_layout() -> None:
    required = [
        "app.py",
        "catalyst_finance/api.py",
        "catalyst_finance/calculation.py",
        "catalyst_finance/cashflow.py",
        "catalyst_finance/cashflow_cli.py",
        "catalyst_finance/cashflow_migration.py",
        "catalyst_finance/cashflow_models.py",
        "catalyst_finance/comparison.py",
        "catalyst_finance/comparison_cli.py",
        "catalyst_finance/comparison_models.py",
        "catalyst_finance/engine.py",
        "catalyst_finance/migration.py",
        "catalyst_finance/models.py",
        "catalyst_finance/repositories.py",
        "catalyst_finance/workspace.py",
        "catalyst_finance/workspace_models.py",
        "data/sample_finance_scenario.json",
        "data/sample_comparison.json",
        "data/legacy_v1.0.0_scenario.json",
        "data/legacy_v1.1.0_scenario.json",
        "data/legacy_v1.2.0_scenario.json",
        "data/legacy_v1.3.0_scenario.json",
        "data/legacy_v1.3.0_cash_flow_scenario.json",
        *[f"data/{filename}" for filename in CASHFLOW_FIXTURES],
        "scripts/browser_parity.js",
        "scripts/browser_cashflow_parity.js",
        "scripts/browser_comparison_parity.js",
        "scripts/generate_schemas.py",
        "scripts/reproduce_examples.py",
        "scripts/reproduce_cashflow_examples.py",
        "scripts/reproduce_comparison_example.py",
        "scripts/reproduce_workspace_example.py",
        "tests/test_browser_parity.py",
        "tests/test_cashflow.py",
        "tests/test_cashflow_cli.py",
        "tests/test_cashflow_migration.py",
        "tests/test_comparison.py",
        "tests/test_comparison_cli.py",
        "tests/test_workspace.py",
        "tests/test_workspace_comparison.py",
        "release/v1.4.0.md",
        "docs/cash-flow-modeling.md",
        "docs/capital-budgeting-review-checklist.md",
        "docs/scenario-comparison.md",
        "docs/comparison-review-checklist.md",
        "schemas/finance_input.schema.json",
        "schemas/finance_publication.schema.json",
        "schemas/cash_flow_input.schema.json",
        "schemas/cash_flow_publication.schema.json",
        "schemas/comparison_definition.schema.json",
        "schemas/comparison_publication.schema.json",
        "schemas/finance_workspace.schema.json",
        "schemas/finance_workspace_export.schema.json",
        "examples/sample_finance_workspace.export.json",
        "examples/sample_cash_flow_scenario.output.json",
        "examples/sample_cash_flow_scenario.periods.csv",
        "examples/sample_comparison.output.json",
        "examples/sample_comparison.output.csv",
        "examples/sample_comparison.output.md",
        "examples/sample_comparison.output.html",
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-engine.js",
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-cashflow-engine.js",
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-comparison-engine.js",
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-demo.js",
    ]
    for path in required:
        require(path)
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    if [path.name for path in workflows] != ["ci.yml"]:
        raise ReleaseError(
            "Exactly one CI workflow named .github/workflows/ci.yml is required."
        )
    archives = [
        path
        for path in ROOT.rglob("*.zip")
        if "dist" not in path.parts and ".git" not in path.parts
    ]
    if archives:
        raise ReleaseError(f"Unexpected checked-in archive(s): {archives}")
    transient_names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    transient = [
        path
        for path in ROOT.rglob("*")
        if path.is_dir() and path.name in transient_names and ".venv" not in path.parts
    ]
    if transient:
        raise ReleaseError(f"Transient Python state exists: {transient}")
    print("PASS: repository layout and single-workflow contract passed.")


def check_static_tools(portable: bool) -> None:
    for module, label, commands in [
        (
            "ruff",
            "Ruff",
            [
                [sys.executable, "-m", "ruff", "check", "."],
                [sys.executable, "-m", "ruff", "format", "--check", "."],
            ],
        ),
        ("mypy", "Mypy", [[sys.executable, "-m", "mypy"]]),
    ]:
        available = (
            subprocess.run(
                [sys.executable, "-c", f"import {module}"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        if available:
            for command in commands:
                run(command)
        elif not portable:
            raise ReleaseError(f"{label} is required for release validation.")
        else:
            print(f"INFO: portable mode skipped unavailable {label} checks.")


def _validate(schema: dict[str, Any], instance: Any, label: str) -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    if errors:
        messages = [f"{list(error.path)}: {error.message}" for error in errors]
        raise ReleaseError(f"{label} schema validation failed: {'; '.join(messages)}")


def check_contracts_and_examples() -> None:
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "schemas").glob("*.schema.json"))
    }
    screening_input = load_json("data/sample_finance_scenario.json")
    screening_publication = load_json("examples/sample_finance_scenario.output.json")
    _validate(schemas["finance_input.schema.json"], screening_input, "Screening input")
    _validate(
        schemas["finance_publication.schema.json"],
        screening_publication,
        "Screening publication",
    )
    for version in ["1.0.0", "1.1.0", "1.2.0", "1.3.0"]:
        migrated = load_json(
            f"examples/legacy_v{version}_scenario.migrated.output.json"
        )
        _validate(
            schemas["finance_publication.schema.json"],
            migrated,
            f"Migrated v{version} publication",
        )
        migration = migrated["metadata"]["migration"]
        if migration is None or migration["source_contract_version"] != version:
            raise ReleaseError(f"v{version} migration provenance is incomplete.")
        expected_count = 12 if version == "1.0.0" else 22
        if len(migration["preserved_fields"]) != expected_count:
            raise ReleaseError(
                f"v{version} migration field preservation is incomplete."
            )
    legacy = load_json("data/legacy_v1.0.0_scenario.json")
    migrated_100 = load_json("examples/legacy_v1.0.0_scenario.migrated.output.json")
    if migrated_100["assumptions"] != legacy["inputs"]:
        raise ReleaseError("Legacy v1.0.0 migration did not preserve all input values.")

    cashflow_publications: dict[str, dict[str, Any]] = {}
    for filename in CASHFLOW_FIXTURES:
        stem = filename.removesuffix(".json")
        input_payload = load_json(f"data/{filename}")
        publication = load_json(f"examples/{stem}.output.json")
        cashflow_publications[filename] = publication
        _validate(
            schemas["cash_flow_input.schema.json"],
            input_payload,
            f"Cash-flow input {filename}",
        )
        _validate(
            schemas["cash_flow_publication.schema.json"],
            publication,
            f"Cash-flow publication {filename}",
        )
        period_net = round(
            sum(row["net_cash_flow"] for row in publication["periods"]), 2
        )
        if abs(period_net - publication["metrics"]["net_cash_flow"]) > 0.02:
            raise ReleaseError(f"Period reconciliation failed: {filename}")
        if len(publication["metrics"]["metric_trace"]) < 9:
            raise ReleaseError(f"Metric trace is incomplete: {filename}")
    multiple = cashflow_publications["multiple_sign_cash_flow_scenario.json"]
    if (
        multiple["metrics"]["irr_status"] != "ambiguous_multiple_sign_changes"
        or multiple["metrics"]["irr_percent_annual"] is not None
        or multiple["metrics"]["irr_roots_percent_annual"] != [10.0, 20.0]
    ):
        raise ReleaseError("Multiple-sign-change IRR ambiguity contract failed.")

    from catalyst_finance.cashflow_migration import normalize_cash_flow

    legacy_cashflow = load_json("data/legacy_v1.3.0_cash_flow_scenario.json")
    normalized_cashflow = normalize_cash_flow(legacy_cashflow).model_dump(mode="json")
    for key, value in legacy_cashflow.items():
        if key == "contract_version":
            continue
        if key != "lines" and normalized_cashflow.get(key) != value:
            raise ReleaseError(
                f"Legacy v1.3.0 cash-flow migration changed source field: {key}"
            )
    for index, source_line in enumerate(legacy_cashflow["lines"]):
        normalized_line = normalized_cashflow["lines"][index]
        for key, value in source_line.items():
            if normalized_line.get(key) != value:
                raise ReleaseError(
                    "Legacy v1.3.0 cash-flow migration changed source line "
                    f"{index} field: {key}"
                )

    comparison_definition = load_json("data/sample_comparison.json")
    comparison_publication = load_json("examples/sample_comparison.output.json")
    _validate(
        schemas["comparison_definition.schema.json"],
        comparison_definition,
        "Comparison definition",
    )
    _validate(
        schemas["comparison_publication.schema.json"],
        comparison_publication,
        "Comparison publication",
    )
    if len(comparison_publication["alternatives"]) < 3:
        raise ReleaseError("Comparison must preserve at least three alternatives.")
    if len(comparison_publication["rankings"]) != len(
        comparison_publication["alternatives"]
    ):
        raise ReleaseError("Comparison rankings are incomplete.")
    if [item["rank"] for item in comparison_publication["rankings"]] != [1, 2, 3]:
        raise ReleaseError("Comparison ranking order is invalid.")
    if any(
        not all(
            alt["source"].get(key)
            for key in ["workspace_id", "scenario_id", "revision_id"]
        )
        for alt in comparison_publication["alternatives"]
    ):
        raise ReleaseError("Comparison revision traceability is incomplete.")
    if len(comparison_publication["one_way_sensitivities"]) < 5:
        raise ReleaseError("One-way sensitivity coverage is incomplete.")
    if (
        not comparison_publication["two_way_sensitivities"]
        or len(comparison_publication["two_way_sensitivities"][0]["cells"]) < 12
    ):
        raise ReleaseError("Two-way sensitivity matrix is incomplete.")
    if len(comparison_publication["break_even_results"]) < 3 or any(
        item["status"] not in {"found", "already_at_target"}
        for item in comparison_publication["break_even_results"]
    ):
        raise ReleaseError("Break-even threshold search contract failed.")
    reproducible = [
        *comparison_publication["one_way_sensitivities"],
        *comparison_publication["two_way_sensitivities"],
        *comparison_publication["break_even_results"],
    ]
    if any(not item.get("reproducibility_key") for item in reproducible):
        raise ReleaseError("Comparison reproducibility keys are incomplete.")

    workspace_export = load_json("examples/sample_finance_workspace.export.json")
    _validate(
        schemas["finance_workspace_export.schema.json"],
        workspace_export,
        "Workspace export",
    )
    _validate(
        schemas["finance_workspace.schema.json"],
        workspace_export["workspace"],
        "Workspace",
    )

    from scripts.generate_schemas import generate
    from scripts.reproduce_cashflow_examples import reproduce as reproduce_cashflow
    from scripts.reproduce_comparison_example import reproduce as reproduce_comparison
    from scripts.reproduce_examples import reproduce
    from scripts.reproduce_workspace_example import reproduce as reproduce_workspace

    with tempfile.TemporaryDirectory(prefix="catalyst-finance-schemas-") as tmp:
        generated_dir = Path(tmp)
        generate(generated_dir)
        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            if path.read_bytes() != (generated_dir / path.name).read_bytes():
                raise ReleaseError(f"Generated schema mismatch: {path.name}")
    with tempfile.TemporaryDirectory(prefix="catalyst-finance-examples-") as tmp:
        for path in reproduce(Path(tmp)):
            if path.read_bytes() != require(f"examples/{path.name}").read_bytes():
                raise ReleaseError(
                    f"Reproducible screening example mismatch: {path.name}"
                )
    with tempfile.TemporaryDirectory(prefix="catalyst-finance-cashflow-") as tmp:
        for path in reproduce_cashflow(Path(tmp)):
            if path.read_bytes() != require(f"examples/{path.name}").read_bytes():
                raise ReleaseError(
                    f"Reproducible cash-flow example mismatch: {path.name}"
                )
    with tempfile.TemporaryDirectory(prefix="catalyst-finance-comparison-") as tmp:
        for path in reproduce_comparison(Path(tmp)):
            if path.read_bytes() != require(f"examples/{path.name}").read_bytes():
                raise ReleaseError(
                    f"Reproducible comparison example mismatch: {path.name}"
                )
    with tempfile.TemporaryDirectory(prefix="catalyst-finance-workspace-") as tmp:
        generated_workspace = reproduce_workspace(Path(tmp) / "workspace.json")
        if (
            generated_workspace.read_bytes()
            != require("examples/sample_finance_workspace.export.json").read_bytes()
        ):
            raise ReleaseError("Reproducible workspace export mismatch.")
    print(
        "PASS: schemas, migrations, capital-budgeting benchmarks, comparison analyses, and exports passed."
    )


def _comparison_core(payload: dict[str, Any]) -> dict[str, Any]:
    selected = json.loads(
        json.dumps(
            {
                key: payload[key]
                for key in [
                    "contract_version",
                    "model_id",
                    "alternatives",
                    "aligned_metrics",
                    "rankings",
                    "one_way_sensitivities",
                    "two_way_sensitivities",
                    "break_even_results",
                    "tornado",
                ]
            }
        )
    )
    for item in selected["one_way_sensitivities"]:
        item.pop("reproducibility_key", None)
    for item in selected["two_way_sensitivities"]:
        item.pop("reproducibility_key", None)
    for item in selected["break_even_results"]:
        item.pop("reproducibility_key", None)
        item.pop("notes", None)
    return selected


def check_browser_parity(portable: bool) -> None:
    node = shutil.which("node")
    if node is None:
        if portable:
            print(
                "INFO: portable mode skipped browser parity because Node.js is absent."
            )
            return
        raise ReleaseError("Node.js is required for browser parity.")

    from catalyst_finance.cashflow import evaluate_cash_flow
    from catalyst_finance.cashflow_migration import normalize_cash_flow
    from catalyst_finance.cashflow_models import CashFlowScenarioInput
    from catalyst_finance.comparison import evaluate_comparison
    from catalyst_finance.comparison_models import ComparisonDefinition
    from catalyst_finance.engine import evaluate_scenario
    from catalyst_finance.io import load_scenario

    screening_files = [
        "sample_finance_scenario.json",
        "legacy_v1.0.0_scenario.json",
        "legacy_v1.1.0_scenario.json",
        "legacy_v1.2.0_scenario.json",
        "legacy_v1.3.0_scenario.json",
    ]
    for filename in screening_files:
        path = ROOT / "data" / filename
        scenario, migration = load_scenario(path)
        expected = evaluate_scenario(
            scenario, generated_at=FIXED_TIMESTAMP, migration=migration
        ).model_dump(mode="json")
        actual = json.loads(
            run(
                [node, "scripts/browser_parity.js", str(path), FIXED_TIMESTAMP],
                capture=True,
            ).stdout
        )
        if actual != expected:
            raise ReleaseError(f"Screening Python/browser parity failed: {filename}")
    for filename in CASHFLOW_FIXTURES:
        path = ROOT / "data" / filename
        scenario = CashFlowScenarioInput.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )
        expected = evaluate_cash_flow(
            scenario, generated_at=FIXED_TIMESTAMP
        ).model_dump(mode="json")
        actual = json.loads(
            run(
                [
                    node,
                    "scripts/browser_cashflow_parity.js",
                    str(path),
                    FIXED_TIMESTAMP,
                ],
                capture=True,
            ).stdout
        )
        if actual != expected:
            raise ReleaseError(f"Cash-flow Python/browser parity failed: {filename}")
    legacy_cashflow_path = ROOT / "data/legacy_v1.3.0_cash_flow_scenario.json"
    legacy_cashflow = normalize_cash_flow(
        json.loads(legacy_cashflow_path.read_text(encoding="utf-8"))
    )
    expected_legacy = evaluate_cash_flow(
        legacy_cashflow, generated_at=FIXED_TIMESTAMP
    ).model_dump(mode="json")
    with tempfile.TemporaryDirectory(prefix="catalyst-finance-legacy-cf-") as tmp:
        normalized_path = Path(tmp) / "normalized.json"
        normalized_path.write_text(
            json.dumps(legacy_cashflow.model_dump(mode="json")), encoding="utf-8"
        )
        actual_legacy = json.loads(
            run(
                [
                    node,
                    "scripts/browser_cashflow_parity.js",
                    str(normalized_path),
                    FIXED_TIMESTAMP,
                ],
                capture=True,
            ).stdout
        )
    if actual_legacy != expected_legacy:
        raise ReleaseError("Migrated v1.3.0 cash-flow Python/browser parity failed.")

    comparison_path = ROOT / "data/sample_comparison.json"
    definition = ComparisonDefinition.model_validate(
        json.loads(comparison_path.read_text(encoding="utf-8"))
    )
    expected_comparison = evaluate_comparison(
        definition, generated_at=FIXED_TIMESTAMP
    ).model_dump(mode="json")
    actual_comparison = json.loads(
        run(
            [
                node,
                "scripts/browser_comparison_parity.js",
                str(comparison_path),
                FIXED_TIMESTAMP,
            ],
            capture=True,
        ).stdout
    )
    if _comparison_core(actual_comparison) != _comparison_core(expected_comparison):
        raise ReleaseError("Comparison Python/browser core parity failed.")
    print(
        "PASS: screening, cash-flow, migration, and comparison browser engines match Python."
    )


def check_plugin() -> None:
    from scripts.build_plugin import build, verify

    with tempfile.TemporaryDirectory(prefix="catalyst-finance-plugin-") as tmp:
        output = Path(tmp) / "catalyst-finance.zip"
        build(output)
        verify(output)
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise ReleaseError("WordPress package ZIP integrity failed.")
            php = archive.read(
                "catalyst-finance-demo/catalyst-finance-demo.php"
            ).decode("utf-8")
            screening = archive.read(
                "catalyst-finance-demo/assets/catalyst-finance-engine.js"
            ).decode("utf-8")
            cashflow = archive.read(
                "catalyst-finance-demo/assets/catalyst-finance-cashflow-engine.js"
            ).decode("utf-8")
            comparison = archive.read(
                "catalyst-finance-demo/assets/catalyst-finance-comparison-engine.js"
            ).decode("utf-8")
            browser = archive.read(
                "catalyst-finance-demo/assets/catalyst-finance-demo.js"
            ).decode("utf-8")
            if (
                f"Version: {VERSION}" not in php
                or VERSION not in screening
                or VERSION not in cashflow
                or VERSION not in comparison
            ):
                raise ReleaseError("WordPress package version mismatch.")
            combined = php + browser + cashflow + comparison
            required_tokens = [
                "workspace_contract_version",
                "data-scfin-export-workspace",
                "data-scfin-import-workspace",
                "Recovered unsaved changes",
                "beforeunload",
                "data-scfin-capital-budgeting",
                "data-scfin-cf-table",
                "data-scfin-cf-waterfall",
                "metric_trace",
                "data-scfin-comparison-studio",
                "data-scfin-comparison-ranking",
                "data-scfin-comparison-tornado",
                "data-scfin-comparison-thresholds",
                "CatalystFinanceComparisonEngine",
                "break_even_results",
                "non_financial_caveats",
            ]
            missing = [token for token in required_tokens if token not in combined]
            if missing:
                raise ReleaseError(
                    f"WordPress finance controls are incomplete: {missing}"
                )
    print("PASS: reproducible WordPress comparison-studio package contract passed.")


def check_syntax(portable: bool) -> None:
    for path in ["app.py", "catalyst_finance", "python", "scripts", "tests"]:
        target = ROOT / path
        ok = (
            compileall.compile_file(str(target), quiet=1, force=True)
            if target.is_file()
            else compileall.compile_dir(str(target), quiet=1, force=True)
        )
        if not ok:
            raise ReleaseError(f"Python compilation failed: {path}")
    from scripts.smoke_test import main as smoke_main

    if smoke_main() != 0:
        raise ReleaseError("Portable smoke tests failed.")
    node = shutil.which("node")
    if node:
        for path in [
            "scripts/browser_parity.js",
            "scripts/browser_cashflow_parity.js",
            "scripts/browser_comparison_parity.js",
            "wordpress/catalyst-finance-demo/assets/catalyst-finance-engine.js",
            "wordpress/catalyst-finance-demo/assets/catalyst-finance-cashflow-engine.js",
            "wordpress/catalyst-finance-demo/assets/catalyst-finance-comparison-engine.js",
            "wordpress/catalyst-finance-demo/assets/catalyst-finance-demo.js",
        ]:
            run([node, "--check", path])
    elif not portable:
        raise ReleaseError("Node.js is required for JavaScript syntax checks.")
    else:
        print("INFO: portable mode skipped optional Node.js syntax checks.")
    php = shutil.which("php")
    if php:
        run([php, "-l", "wordpress/catalyst-finance-demo/catalyst-finance-demo.php"])
    elif not portable:
        raise ReleaseError("PHP is required for the plugin syntax check.")
    else:
        print("INFO: portable mode skipped optional PHP syntax check.")


def clear_transient_state() -> None:
    names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    for path in sorted(ROOT.rglob("*"), reverse=True):
        if path.is_dir() and path.name in names and ".venv" not in path.parts:
            shutil.rmtree(path, ignore_errors=True)
    for path in ROOT.rglob("*.py[co]"):
        path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Permit unavailable optional Node/PHP checks.",
    )
    args = parser.parse_args()
    try:
        clear_transient_state()
        check_versions()
        check_layout()
        check_static_tools(args.portable)
        run([sys.executable, "-m", "pytest", "-q"])
        check_contracts_and_examples()
        check_browser_parity(args.portable)
        check_plugin()
        check_syntax(args.portable)
        clear_transient_state()
        check_layout()
    except (
        ReleaseError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Catalyst Finance v1.4.0 release contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
