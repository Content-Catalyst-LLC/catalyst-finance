#!/usr/bin/env python3
"""Catalyst Finance v1.2.0 release contract."""

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
VERSION = "1.2.0"
MODEL_ID = "catalyst-finance.screening"
FIXED_TIMESTAMP = "2026-07-17T00:00:00+00:00"


class ReleaseError(RuntimeError):
    """Raised when a release contract fails."""


def run(
    command: Sequence[str],
    *,
    cwd: Path = ROOT,
    capture: bool = False,
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


def _match(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        raise ReleaseError(f"Could not find version in {label}")
    return match.group(1)


def check_versions() -> None:
    version_file = require("VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads(require("pyproject.toml").read_text(encoding="utf-8"))
    package_text = require("catalyst_finance/version.py").read_text(encoding="utf-8")
    plugin_text = require(
        "wordpress/catalyst-finance-demo/catalyst-finance-demo.php"
    ).read_text(encoding="utf-8")
    engine_text = require(
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-engine.js"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        require("catalyst_finance_manifest.json").read_text(encoding="utf-8")
    )
    example = json.loads(
        require("examples/sample_finance_scenario.output.json").read_text(
            encoding="utf-8"
        )
    )
    input_schema = json.loads(
        require("schemas/finance_input.schema.json").read_text(encoding="utf-8")
    )
    publication_schema = json.loads(
        require("schemas/finance_publication.schema.json").read_text(encoding="utf-8")
    )
    workspace_schema = json.loads(
        require("schemas/finance_workspace.schema.json").read_text(encoding="utf-8")
    )
    workspace_export = json.loads(
        require("examples/sample_finance_workspace.export.json").read_text(
            encoding="utf-8"
        )
    )
    observed = {
        "VERSION": version_file,
        "pyproject": pyproject["project"]["version"],
        "package": _match(r'__version__ = "([^"]+)"', package_text, "package"),
        "plugin": _match(r"Version:\s*([0-9.]+)", plugin_text, "plugin"),
        "plugin constant": _match(
            r"CATALYST_FINANCE_DEMO_VERSION', '([0-9.]+)'",
            plugin_text,
            "plugin constant",
        ),
        "browser engine": _match(
            r"const CONTRACT_VERSION = '([0-9.]+)'", engine_text, "browser engine"
        ),
        "manifest": manifest["version"],
        "manifest contract": manifest["contract_version"],
        "example": example["metadata"]["version"],
        "example contract": example["contract_version"],
        "input schema": input_schema["properties"]["contract_version"]["const"],
        "publication schema": publication_schema["properties"]["contract_version"][
            "const"
        ],
        "workspace schema": workspace_schema["properties"][
            "workspace_contract_version"
        ]["const"],
        "workspace export": workspace_export["export_contract_version"],
        "workspace record": workspace_export["workspace"]["workspace_contract_version"],
    }
    mismatches = {name: value for name, value in observed.items() if value != VERSION}
    if mismatches:
        raise ReleaseError(f"Version contract failed: {mismatches}")
    if manifest["model_id"] != MODEL_ID or example["model_id"] != MODEL_ID:
        raise ReleaseError("Model identifier contract failed.")
    print(f"PASS: {len(observed)} version surfaces report {VERSION}.")


def check_layout() -> None:
    required = [
        "app.py",
        "catalyst_finance/api.py",
        "catalyst_finance/calculation.py",
        "catalyst_finance/cli.py",
        "catalyst_finance/domain.py",
        "catalyst_finance/engine.py",
        "catalyst_finance/interpretation.py",
        "catalyst_finance/io.py",
        "catalyst_finance/migration.py",
        "catalyst_finance/models.py",
        "catalyst_finance/narrative.py",
        "catalyst_finance/registry.py",
        "catalyst_finance/repositories.py",
        "catalyst_finance/templates.py",
        "catalyst_finance/workspace.py",
        "catalyst_finance/workspace_cli.py",
        "catalyst_finance/workspace_models.py",
        "data/sample_finance_scenario.json",
        "data/legacy_v1.1.0_scenario.json",
        "data/legacy_v1.0.0_scenario.json",
        "scripts/browser_parity.js",
        "scripts/generate_schemas.py",
        "scripts/reproduce_workspace_example.py",
        "tests/test_browser_parity.py",
        "tests/test_workspace.py",
        "tests/test_workspace_cli.py",
        "tests/test_contracts.py",
        "release/v1.2.0.md",
        "schemas/finance_input.schema.json",
        "schemas/finance_result.schema.json",
        "schemas/finance_interpretation.schema.json",
        "schemas/finance_metadata.schema.json",
        "schemas/finance_publication.schema.json",
        "schemas/finance_workspace.schema.json",
        "schemas/finance_workspace_export.schema.json",
        "schemas/finance_workspace_scenario.schema.json",
        "schemas/finance_scenario_template.schema.json",
        "examples/sample_finance_workspace.export.json",
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-engine.js",
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
    ruff_available = (
        shutil.which("ruff") is not None
        or subprocess.run(
            [sys.executable, "-c", "import ruff"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    mypy_available = (
        shutil.which("mypy") is not None
        or subprocess.run(
            [sys.executable, "-c", "import mypy"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if ruff_available:
        run([sys.executable, "-m", "ruff", "check", "."])
        run([sys.executable, "-m", "ruff", "format", "--check", "."])
    elif not portable:
        raise ReleaseError("Ruff is required for release validation.")
    else:
        print("INFO: portable mode skipped unavailable Ruff checks.")
    if mypy_available:
        run([sys.executable, "-m", "mypy"])
    elif not portable:
        raise ReleaseError("Mypy is required for release validation.")
    else:
        print("INFO: portable mode skipped unavailable Mypy checks.")


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
    canonical_input = json.loads(
        require("data/sample_finance_scenario.json").read_text(encoding="utf-8")
    )
    publication = json.loads(
        require("examples/sample_finance_scenario.output.json").read_text(
            encoding="utf-8"
        )
    )
    migrated = json.loads(
        require("examples/legacy_v1.0.0_scenario.migrated.output.json").read_text(
            encoding="utf-8"
        )
    )
    migrated_v110 = json.loads(
        require("examples/legacy_v1.1.0_scenario.migrated.output.json").read_text(
            encoding="utf-8"
        )
    )
    workspace_export = json.loads(
        require("examples/sample_finance_workspace.export.json").read_text(
            encoding="utf-8"
        )
    )
    _validate(schemas["finance_input.schema.json"], canonical_input, "Canonical input")
    _validate(
        schemas["finance_publication.schema.json"], publication, "Canonical publication"
    )
    _validate(
        schemas["finance_publication.schema.json"], migrated, "Migrated publication"
    )
    _validate(
        schemas["finance_publication.schema.json"],
        migrated_v110,
        "Migrated v1.1.0 publication",
    )
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
    _validate(schemas["finance_result.schema.json"], publication["results"], "Results")
    _validate(
        schemas["finance_interpretation.schema.json"],
        publication["interpretation"],
        "Interpretation",
    )
    _validate(
        schemas["finance_metadata.schema.json"], publication["metadata"], "Metadata"
    )

    legacy = json.loads(
        require("data/legacy_v1.0.0_scenario.json").read_text(encoding="utf-8")
    )
    if migrated["assumptions"] != legacy["inputs"]:
        raise ReleaseError("Legacy migration did not preserve all input values.")
    migration = migrated["metadata"]["migration"]
    if migration is None or len(migration["preserved_fields"]) != 12:
        raise ReleaseError("Legacy migration provenance is incomplete.")
    migration_v110 = migrated_v110["metadata"]["migration"]
    if (
        migration_v110 is None
        or migration_v110["source_contract_version"] != "1.1.0"
        or len(migration_v110["preserved_fields"]) != 22
    ):
        raise ReleaseError("v1.1.0 migration provenance is incomplete.")

    from scripts.generate_schemas import generate
    from scripts.reproduce_examples import reproduce
    from scripts.reproduce_workspace_example import reproduce as reproduce_workspace

    with tempfile.TemporaryDirectory(prefix="catalyst-finance-schemas-") as tmp:
        generated_dir = Path(tmp)
        generate(generated_dir)
        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            if path.read_bytes() != (generated_dir / path.name).read_bytes():
                raise ReleaseError(f"Generated schema mismatch: {path.name}")

    with tempfile.TemporaryDirectory(prefix="catalyst-finance-examples-") as tmp:
        generated = reproduce(Path(tmp))
        for path in generated:
            expected = require(f"examples/{path.name}").read_bytes()
            if path.read_bytes() != expected:
                raise ReleaseError(f"Reproducible example mismatch: {path.name}")

    with tempfile.TemporaryDirectory(
        prefix="catalyst-finance-workspace-example-"
    ) as tmp:
        generated_workspace = reproduce_workspace(Path(tmp) / "workspace.json")
        expected_workspace = require("examples/sample_finance_workspace.export.json")
        if generated_workspace.read_bytes() != expected_workspace.read_bytes():
            raise ReleaseError("Reproducible workspace export mismatch.")
    print("PASS: schemas, migrations, workspace export, and examples passed.")


def check_browser_parity(portable: bool) -> None:
    node = shutil.which("node")
    if node is None:
        if portable:
            print(
                "INFO: portable mode skipped browser parity because Node.js is absent."
            )
            return
        raise ReleaseError("Node.js is required for browser parity.")

    from catalyst_finance.engine import evaluate_scenario
    from catalyst_finance.io import load_scenario

    for filename in [
        "sample_finance_scenario.json",
        "legacy_v1.0.0_scenario.json",
        "legacy_v1.1.0_scenario.json",
    ]:
        path = ROOT / "data" / filename
        scenario, migration = load_scenario(path)
        expected = evaluate_scenario(
            scenario,
            generated_at=FIXED_TIMESTAMP,
            migration=migration,
        ).model_dump(mode="json")
        completed = run(
            [node, "scripts/browser_parity.js", str(path), FIXED_TIMESTAMP],
            capture=True,
        )
        actual = json.loads(completed.stdout)
        if actual != expected:
            raise ReleaseError(f"Python/browser parity failed: {filename}")
    print("PASS: Python and browser engines are contract-equivalent.")


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
            engine = archive.read(
                "catalyst-finance-demo/assets/catalyst-finance-engine.js"
            ).decode("utf-8")
            if f"Version: {VERSION}" not in php or VERSION not in engine:
                raise ReleaseError("WordPress package version mismatch.")
            browser = archive.read(
                "catalyst-finance-demo/assets/catalyst-finance-demo.js"
            ).decode("utf-8")
            required_workspace_tokens = [
                "workspace_contract_version",
                "data-scfin-export-workspace",
                "data-scfin-import-workspace",
                "Recovered unsaved changes",
                "beforeunload",
            ]
            if any(token not in php + browser for token in required_workspace_tokens):
                raise ReleaseError("WordPress workspace controls are incomplete.")
    print("PASS: reproducible WordPress package contract passed.")


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
            "wordpress/catalyst-finance-demo/assets/catalyst-finance-engine.js",
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
    print("Catalyst Finance v1.2.0 release contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
