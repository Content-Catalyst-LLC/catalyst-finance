#!/usr/bin/env python3
"""Build a deterministic source archive for the current release."""

from __future__ import annotations

import argparse
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
RELEASE_ROOT = f"catalyst-finance-v{VERSION}"
DEFAULT_OUTPUT = ROOT / "dist" / f"catalyst-finance-v{VERSION}-repository.zip"
ZIP_TIME = (2026, 1, 1, 0, 0, 0)
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


def included_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if any(part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if path.name == ".DS_Store" or path.name.endswith("~"):
            continue
        if (
            relative.parts
            and relative.parts[0] == "outputs"
            and path.name != ".gitkeep"
        ):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in included_files():
            relative = Path(RELEASE_ROOT) / path.relative_to(ROOT)
            info = zipfile.ZipInfo(relative.as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return output


def verify(output: Path) -> None:
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        required = {
            f"{RELEASE_ROOT}/VERSION",
            f"{RELEASE_ROOT}/pyproject.toml",
            f"{RELEASE_ROOT}/catalyst_finance/platform.py",
            f"{RELEASE_ROOT}/data/sample_platform.json",
            f"{RELEASE_ROOT}/schemas/platform_definition.schema.json",
            f"{RELEASE_ROOT}/examples/sample_platform.output.json",
            f"{RELEASE_ROOT}/scripts/check_release.py",
            f"{RELEASE_ROOT}/wordpress/catalyst-finance-demo/catalyst-finance-demo.php",
            f"{RELEASE_ROOT}/wordpress/catalyst-finance-demo/assets/catalyst-finance-platform-engine.js",
        }
        missing = sorted(required.difference(names))
        if missing:
            raise SystemExit(f"Repository archive is missing: {', '.join(missing)}")
        prefix = f"{RELEASE_ROOT}/"
        if any(not name.startswith(prefix) for name in names):
            raise SystemExit("Repository archive root contract failed.")
        if any(
            marker in name
            for name in names
            for marker in ("/__pycache__/", "/.pytest_cache/", "/dist/")
        ):
            raise SystemExit("Repository archive contains transient state.")
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Corrupt archive member: {bad}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = build(args.output.resolve())
    os.utime(output, (0, 0))
    verify(output)
    print(f"Built {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
