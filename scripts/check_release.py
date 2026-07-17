#!/usr/bin/env python3
"""Catalyst Finance v1.0.1 release contract."""

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

import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VERSION = "1.0.1"


class ReleaseError(RuntimeError):
    """Raised when a release contract fails."""


def run(command: Sequence[str], *, cwd: Path = ROOT) -> None:
    print("RUN:", " ".join(command))
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode:
        raise ReleaseError(
            f"Command failed with status {completed.returncode}: {' '.join(command)}"
        )


def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        raise ReleaseError(f"Required release path is missing: {path}")
    return target


def check_versions() -> None:
    version_file = require("VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads(require("pyproject.toml").read_text(encoding="utf-8"))
    package_text = require("catalyst_finance/version.py").read_text(encoding="utf-8")
    plugin_text = require(
        "wordpress/catalyst-finance-demo/catalyst-finance-demo.php"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        require("catalyst_finance_manifest.json").read_text(encoding="utf-8")
    )
    example = json.loads(
        require("examples/sample_finance_scenario.output.json").read_text(
            encoding="utf-8"
        )
    )
    schema = json.loads(
        require("schemas/finance_scenario.schema.json").read_text(encoding="utf-8")
    )

    observed = {
        "VERSION": version_file,
        "pyproject": pyproject["project"]["version"],
        "package": re.search(r'__version__ = "([^"]+)"', package_text).group(1),
        "plugin": re.search(r"Version:\s*([0-9.]+)", plugin_text).group(1),
        "plugin constant": re.search(
            r"CATALYST_FINANCE_DEMO_VERSION', '([0-9.]+)'", plugin_text
        ).group(1),
        "manifest": manifest["version"],
        "example": example["metadata"]["version"],
        "schema": schema["properties"]["metadata"]["properties"]["version"]["const"],
    }
    mismatches = {name: value for name, value in observed.items() if value != VERSION}
    if mismatches:
        raise ReleaseError(f"Version contract failed: {mismatches}")
    print(f"PASS: {len(observed)} version surfaces report {VERSION}.")


def check_layout() -> None:
    required = [
        "app.py",
        "catalyst_finance/api.py",
        "catalyst_finance/cli.py",
        "catalyst_finance/domain.py",
        "catalyst_finance/elasticity.py",
        "catalyst_finance/io.py",
        "catalyst_finance/serve.py",
        "scripts/build_plugin.py",
        "scripts/build_repository_release.py",
        "scripts/reproduce_examples.py",
        "scripts/smoke_test.py",
        "tests/test_api.py",
        "tests/test_catalyst_finance_core.py",
        "tests/test_elasticity.py",
        "release/v1.0.1.md",
    ]
    for path in required:
        require(path)

    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    if [path.name for path in workflows] != ["ci.yml"]:
        raise ReleaseError(
            "Exactly one CI workflow named .github/workflows/ci.yml is required."
        )

    forbidden = [ROOT / "plots", ROOT / "data" / "linear_results.csv"]
    for path in forbidden:
        if path.exists():
            raise ReleaseError(f"Generated artifact remains in source layout: {path}")

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
        subprocess.run(
            [sys.executable, "-c", "import ruff"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    mypy_available = (
        subprocess.run(
            [sys.executable, "-c", "import mypy"],
            cwd=ROOT,
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

    mypy_files = [
        "catalyst_finance/__init__.py",
        "catalyst_finance/api.py",
        "catalyst_finance/cli.py",
        "catalyst_finance/domain.py",
        "catalyst_finance/io.py",
        "catalyst_finance/serve.py",
        "catalyst_finance/version.py",
    ]
    if mypy_available:
        run([sys.executable, "-m", "mypy", *mypy_files])
    elif not portable:
        raise ReleaseError("Mypy is required for release validation.")
    else:
        print("INFO: portable mode skipped unavailable Mypy checks.")


def check_json_and_examples() -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads(
        require("schemas/finance_scenario.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    example = json.loads(
        require("examples/sample_finance_scenario.output.json").read_text(
            encoding="utf-8"
        )
    )
    errors = sorted(validator.iter_errors(example), key=lambda item: list(item.path))
    if errors:
        messages = [f"{list(error.path)}: {error.message}" for error in errors]
        raise ReleaseError("Example schema validation failed: " + "; ".join(messages))

    from scripts.reproduce_examples import reproduce

    with tempfile.TemporaryDirectory(prefix="catalyst-finance-examples-") as tmp:
        output_dir = Path(tmp)
        reproduce(output_dir)
        for name in [
            "sample_finance_scenario.output.json",
            "sample_finance_scenario.output.md",
        ]:
            expected = require(f"examples/{name}").read_bytes()
            actual = (output_dir / name).read_bytes()
            if actual != expected:
                raise ReleaseError(f"Reproducible example mismatch: {name}")
    print("PASS: JSON schema and reproducible examples passed.")


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
            if f"Version: {VERSION}" not in php:
                raise ReleaseError("WordPress package version mismatch.")
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
        run(
            [
                node,
                "--check",
                "wordpress/catalyst-finance-demo/assets/catalyst-finance-demo.js",
            ]
        )
    elif not portable:
        raise ReleaseError("Node.js is required for the JavaScript syntax check.")
    else:
        print("INFO: portable mode skipped optional Node.js syntax check.")

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
        check_json_and_examples()
        check_plugin()
        check_syntax(args.portable)
        clear_transient_state()
        check_layout()
    except (ReleaseError, AttributeError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Catalyst Finance v1.0.1 release contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
