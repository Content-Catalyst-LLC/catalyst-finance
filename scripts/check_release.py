#!/usr/bin/env python3
"""Catalyst Finance v1.9.0 release-integrity contract."""

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
VERSION = "1.9.0"
FIXED = "2026-07-17T00:00:00+00:00"
MODELS = {
    "screening": "catalyst-finance.screening",
    "cash-flow": "catalyst-finance.cash-flow",
    "comparison": "catalyst-finance.comparison",
    "uncertainty": "catalyst-finance.uncertainty",
    "pricing": "catalyst-finance.pricing",
    "operating": "catalyst-finance.operating",
    "sustainable": "catalyst-finance.sustainable",
    "governance": "catalyst-finance.governance",
}
BROWSERS = {
    "screening": "catalyst-finance-engine.js",
    "cash-flow": "catalyst-finance-cashflow-engine.js",
    "comparison": "catalyst-finance-comparison-engine.js",
    "uncertainty": "catalyst-finance-uncertainty-engine.js",
    "pricing": "catalyst-finance-pricing-engine.js",
    "operating": "catalyst-finance-operating-engine.js",
    "sustainable": "catalyst-finance-sustainable-engine.js",
    "governance": "catalyst-finance-governance-engine.js",
}


class ReleaseError(RuntimeError):
    pass


def run(
    command: Sequence[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print("RUN:", " ".join(command))
    p = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=capture, check=False
    )
    if p.returncode:
        if capture:
            print(p.stdout)
            print(p.stderr, file=sys.stderr)
        raise ReleaseError(
            f"Command failed with status {p.returncode}: {' '.join(command)}"
        )
    return p


def require(path: str) -> Path:
    p = ROOT / path
    if not p.exists():
        raise ReleaseError(f"Missing required release path: {path}")
    return p


def load(path: str) -> dict[str, Any]:
    v = json.loads(require(path).read_text())
    if not isinstance(v, dict):
        raise ReleaseError(f"Expected JSON object: {path}")
    return v


def match(pattern: str, text: str, label: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise ReleaseError(f"Could not find version in {label}")
    return m.group(1)


def clear() -> None:
    for p in sorted(ROOT.rglob("*"), reverse=True):
        if (
            p.is_dir()
            and p.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
            and ".venv" not in p.parts
        ):
            shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob("*.py[co]"):
        p.unlink(missing_ok=True)


def check_versions() -> None:
    pyproject = tomllib.loads(require("pyproject.toml").read_text())
    manifest = load("catalyst_finance_manifest.json")
    plugin = require(
        "wordpress/catalyst-finance-demo/catalyst-finance-demo.php"
    ).read_text()
    package = require("catalyst_finance/version.py").read_text()
    observed = {
        "VERSION": require("VERSION").read_text().strip(),
        "pyproject": pyproject["project"]["version"],
        "package": match(r'__version__ = "([^"]+)"', package, "package"),
        "plugin": match(r"Version:\s*([0-9.]+)", plugin, "plugin"),
        "plugin constant": match(
            r"CATALYST_FINANCE_DEMO_VERSION', '([0-9.]+)'", plugin, "plugin constant"
        ),
        "manifest": manifest["version"],
        "contract": manifest["contract_version"],
        "methodology": manifest["methodology_version"],
        "workspace": manifest["workspace_contract_version"],
    }
    for label, filename in BROWSERS.items():
        observed[f"{label} browser"] = match(
            r"const CONTRACT_VERSION\s*=\s*'([0-9.]+)'",
            require("wordpress/catalyst-finance-demo/assets/" + filename).read_text(),
            label,
        )
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        schema = json.loads(path.read_text())
        props = schema.get("properties", {})
        key = (
            "workspace_contract_version"
            if "workspace_contract_version" in props
            else "export_contract_version"
            if "export_contract_version" in props
            else "contract_version"
            if "contract_version" in props
            else None
        )
        if key and "const" in props[key]:
            observed["schema " + path.name] = props[key]["const"]
    for path in sorted((ROOT / "examples").glob("*.output.json")):
        value = json.loads(path.read_text())
        if isinstance(value, dict):
            if "contract_version" in value:
                observed["example " + path.name] = value["contract_version"]
            if (
                isinstance(value.get("metadata"), dict)
                and "version" in value["metadata"]
            ):
                observed["example metadata " + path.name] = value["metadata"]["version"]
    workspace = load("examples/sample_finance_workspace.export.json")
    observed["workspace export"] = workspace["export_contract_version"]
    observed["workspace record"] = workspace["workspace"]["workspace_contract_version"]
    bad = {k: v for k, v in observed.items() if v != VERSION}
    if bad:
        raise ReleaseError(f"Version mismatch: {bad}")
    expected = {
        "model_id": MODELS["screening"],
        "cash_flow_model_id": MODELS["cash-flow"],
        "comparison_model_id": MODELS["comparison"],
        "uncertainty_model_id": MODELS["uncertainty"],
        "pricing_model_id": MODELS["pricing"],
        "operating_model_id": MODELS["operating"],
        "sustainable_model_id": MODELS["sustainable"],
        "governance_model_id": MODELS["governance"],
    }
    if any(manifest.get(k) != v for k, v in expected.items()):
        raise ReleaseError("Manifest model identifier contract failed.")
    print(f"PASS: {len(observed)} version surfaces report {VERSION}.")


def check_layout() -> None:
    required = [
        "app.py",
        "catalyst_finance/governance.py",
        "catalyst_finance/governance_cli.py",
        "catalyst_finance/governance_migration.py",
        "catalyst_finance/governance_models.py",
        "data/sample_governance.json",
        "data/legacy_v1.8.0_governance.json",
        "schemas/governance_definition.schema.json",
        "schemas/governance_publication.schema.json",
        "examples/sample_governance.output.json",
        "examples/sample_governance.trace.csv",
        "examples/sample_governance.brief.md",
        "examples/sample_governance.brief.html",
        "examples/sample_governance.public.json",
        "scripts/browser_governance_parity.js",
        "scripts/reproduce_governance_example.py",
        "tests/test_governance.py",
        "tests/test_governance_cli.py",
        "tests/test_api_governance.py",
        "tests/test_workspace_governance.py",
        "docs/evidence-review-governance-publication.md",
        "docs/governance-review-checklist.md",
        "release/v1.9.0.md",
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-governance-engine.js",
    ]
    required += [
        "catalyst_finance/" + name
        for name in [
            "api.py",
            "registry.py",
            "workspace.py",
            "workspace_models.py",
            "workspace_migration.py",
            "sustainable.py",
            "operating.py",
            "pricing.py",
            "uncertainty.py",
            "comparison.py",
            "cashflow.py",
        ]
    ]
    required += [
        "scripts/" + name
        for name in [
            "generate_schemas.py",
            "build_plugin.py",
            "build_repository_release.py",
            "smoke_test.py",
        ]
    ]
    for path in required:
        require(path)
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    if [p.name for p in workflows] != ["ci.yml"]:
        raise ReleaseError("Exactly one CI workflow named ci.yml is required.")
    archives = [
        p
        for p in ROOT.rglob("*.zip")
        if "dist" not in p.parts and ".git" not in p.parts
    ]
    if archives:
        raise ReleaseError(f"Unexpected checked-in archives: {archives}")
    transient = [
        p
        for p in ROOT.rglob("*")
        if p.is_dir()
        and p.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        and ".venv" not in p.parts
    ]
    if transient:
        raise ReleaseError(f"Transient Python state exists: {transient}")
    print("PASS: repository layout and single-workflow contract passed.")


def check_static(portable: bool) -> None:
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
        ok = (
            subprocess.run(
                [sys.executable, "-c", f"import {module}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        if not ok:
            if portable:
                print(f"INFO: portable mode skipped {label}.")
                continue
            raise ReleaseError(f"{label} is required.")
        for cmd in commands:
            run(cmd)


def validate(schema: dict[str, Any], instance: Any, label: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise ReleaseError("jsonschema is required.") from exc
    try:
        jsonschema.Draft202012Validator(schema).validate(instance)
    except jsonschema.ValidationError as exc:
        raise ReleaseError(f"{label} schema failed: {exc.message}") from exc


def check_governance_contract() -> None:
    definition = load("data/sample_governance.json")
    publication = load("examples/sample_governance.output.json")
    validate(
        load("schemas/governance_definition.schema.json"),
        definition,
        "Governance definition",
    )
    validate(
        load("schemas/governance_publication.schema.json"),
        publication,
        "Governance publication",
    )
    r = publication["readiness"]
    if (
        r["status"] != "published"
        or not r["publication_allowed"]
        or r["fully_traced_headline_count"] != 2
    ):
        raise ReleaseError("Governance readiness contract failed.")
    public = publication["public_payload"]
    if (
        len(public["sources"]) != 2
        or len(public["claims"]) != 3
        or public["attachments"]
    ):
        raise ReleaseError("Governance redaction contract failed.")
    audit = publication["audit_history"]
    if (
        not audit
        or audit[-1]["entry_hash"] != publication["run_record"]["audit_head_hash"]
    ):
        raise ReleaseError("Governance audit-chain contract failed.")
    if {x["target"] for x in publication["handoffs"]} != {
        "knowledge_library",
        "decision_studio",
    }:
        raise ReleaseError("Governance handoff contract failed.")
    from catalyst_finance.governance_migration import normalize_governance

    if (
        normalize_governance(
            load("data/legacy_v1.8.0_governance.json")
        ).contract_version
        != VERSION
    ):
        raise ReleaseError("v1.8 governance migration failed.")


def compare_generated(paths: list[Path], temp: Path, label: str) -> None:
    for path in paths:
        expected = require("examples/" + path.name)
        if path.read_bytes() != expected.read_bytes():
            raise ReleaseError(f"Reproducible {label} mismatch: {path.name}")


def check_reproducibility() -> None:
    from scripts.generate_schemas import generate
    from scripts.reproduce_cashflow_examples import reproduce as cashflow
    from scripts.reproduce_comparison_example import reproduce as comparison
    from scripts.reproduce_examples import reproduce as screening
    from scripts.reproduce_governance_example import reproduce as governance
    from scripts.reproduce_pricing_example import reproduce as pricing
    from scripts.reproduce_sustainable_example import reproduce as sustainable
    from scripts.reproduce_uncertainty_example import reproduce as uncertainty
    from scripts.reproduce_workspace_example import reproduce as workspace

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        generate(d)
        for p in sorted((ROOT / "schemas").glob("*.schema.json")):
            if p.read_bytes() != (d / p.name).read_bytes():
                raise ReleaseError(f"Generated schema mismatch: {p.name}")
    for label, func in [
        ("screening", screening),
        ("cash-flow", cashflow),
        ("comparison", comparison),
        ("uncertainty", uncertainty),
        ("pricing", pricing),
        ("sustainable", sustainable),
        ("governance", governance),
    ]:
        with tempfile.TemporaryDirectory() as tmp:
            compare_generated(func(Path(tmp)), Path(tmp), label)
    with tempfile.TemporaryDirectory() as tmp:
        p = workspace(Path(tmp) / "workspace.json")
        if (
            p.read_bytes()
            != require("examples/sample_finance_workspace.export.json").read_bytes()
        ):
            raise ReleaseError("Reproducible workspace mismatch.")
    # Operating reproducer writes canonical files; verify it is idempotent.
    from scripts.reproduce_operating_example import reproduce as operating

    before = {
        name: require("examples/" + name).read_bytes()
        for name in ["sample_operating.output.json", "sample_operating.summary.csv"]
    }
    operating()
    if any(
        require("examples/" + name).read_bytes() != data
        for name, data in before.items()
    ):
        raise ReleaseError("Reproducible operating example mismatch.")
    print("PASS: schemas and all eight model publications reproduce byte-for-byte.")


def check_migrations() -> None:
    from catalyst_finance.cashflow_migration import normalize_cash_flow
    from catalyst_finance.comparison_migration import normalize_comparison
    from catalyst_finance.migration import normalize_scenario
    from catalyst_finance.operating_migration import normalize_operating
    from catalyst_finance.pricing_migration import normalize_pricing
    from catalyst_finance.sustainable_migration import normalize_sustainable
    from catalyst_finance.uncertainty_migration import normalize_uncertainty
    from catalyst_finance.workspace_migration import migrate_workspace_payload

    checks = [
        (
            "screening",
            normalize_scenario(load("data/legacy_v1.8.0_scenario.json"))[
                0
            ].contract_version,
        ),
        (
            "cash-flow",
            normalize_cash_flow(
                load("data/legacy_v1.8.0_cash_flow_scenario.json")
            ).contract_version,
        ),
        (
            "comparison",
            normalize_comparison(
                load("data/legacy_v1.8.0_comparison.json")
            ).contract_version,
        ),
        (
            "uncertainty",
            normalize_uncertainty(
                load("data/legacy_v1.8.0_uncertainty.json")
            ).contract_version,
        ),
        (
            "pricing",
            normalize_pricing(load("data/legacy_v1.8.0_pricing.json")).contract_version,
        ),
        (
            "operating",
            normalize_operating(
                load("data/legacy_v1.8.0_operating.json")
            ).contract_version,
        ),
        (
            "sustainable",
            normalize_sustainable(
                load("data/legacy_v1.8.0_sustainable.json")
            ).contract_version,
        ),
    ]
    bad = [name for name, v in checks if v != VERSION]
    workspace = migrate_workspace_payload(
        load("data/legacy_v1.8.0_workspace.export.json")
    )
    if (
        workspace["export_contract_version"] != VERSION
        or "governance_analyses" not in workspace["workspace"]
    ):
        bad.append("workspace")
    if bad:
        raise ReleaseError(f"v1.8 migration failed: {bad}")
    print("PASS: complete v1.8.0 migration coverage passed.")


def check_plugin() -> None:
    from scripts.build_plugin import build, verify

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "catalyst-finance.zip"
        build(out)
        verify(out)
        with zipfile.ZipFile(out) as z:
            if z.testzip():
                raise ReleaseError("Plugin ZIP integrity failed.")
            combined = "".join(
                z.read(n).decode("utf-8")
                for n in z.namelist()
                if n.endswith((".php", ".js", ".md"))
            )
            tokens = [
                "data-scfin-governance-studio",
                "data-scfin-governance-run",
                "CatalystFinanceGovernanceEngine",
                "public_payload",
                "audit_head_hash",
                "knowledge_library",
                "decision_studio",
                "data-scfin-sustainable-studio",
                "data-scfin-operating-studio",
                "data-scfin-pricing-studio",
                "data-scfin-uncertainty-studio",
                "data-scfin-comparison-studio",
                "data-scfin-capital-budgeting",
            ]
            missing = [t for t in tokens if t not in combined]
            if missing:
                raise ReleaseError(
                    f"WordPress governance controls incomplete: {missing}"
                )
    print("PASS: deterministic WordPress package and eight-studio contract passed.")


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
    from scripts.smoke_test import main as smoke

    if smoke() != 0:
        raise ReleaseError("Portable smoke tests failed.")
    node = shutil.which("node")
    js = [
        *[
            "scripts/browser_" + x + "_parity.js"
            for x in [
                "cashflow",
                "comparison",
                "uncertainty",
                "pricing",
                "operating",
                "sustainable",
                "governance",
            ]
        ],
        "scripts/browser_parity.js",
        *["wordpress/catalyst-finance-demo/assets/" + v for v in BROWSERS.values()],
        "wordpress/catalyst-finance-demo/assets/catalyst-finance-demo.js",
    ]
    if node:
        for path in js:
            run([node, "--check", path])
    elif not portable:
        raise ReleaseError("Node.js is required.")
    php = shutil.which("php")
    if php:
        run([php, "-l", "wordpress/catalyst-finance-demo/catalyst-finance-demo.php"])
    elif not portable:
        raise ReleaseError("PHP is required.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    try:
        clear()
        check_versions()
        check_layout()
        check_static(args.portable)
        run([sys.executable, "-m", "pytest", "-q"])
        check_governance_contract()
        check_reproducibility()
        check_migrations()
        check_plugin()
        check_syntax(args.portable)
        clear()
        check_layout()
    except (ReleaseError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    print("Catalyst Finance v1.9.0 release contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
