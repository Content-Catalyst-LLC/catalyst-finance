#!/usr/bin/env python3
"""Build a deterministic Catalyst Finance WordPress plugin ZIP."""

from __future__ import annotations

import argparse
import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "wordpress" / "catalyst-finance-demo"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DEFAULT_OUTPUT = ROOT / "dist" / "catalyst-finance.zip"
VERSIONED_NAME = f"catalyst-finance-demo-v{VERSION}.zip"
ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def build(output: Path) -> Path:
    if not PLUGIN_DIR.is_dir():
        raise SystemExit(f"Plugin source is missing: {PLUGIN_DIR}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    files = sorted(path for path in PLUGIN_DIR.rglob("*") if path.is_file())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = Path(PLUGIN_DIR.name) / path.relative_to(PLUGIN_DIR)
            info = zipfile.ZipInfo(relative.as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return output


def verify(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        expected_root = f"{PLUGIN_DIR.name}/"
        if not names or any(not name.startswith(expected_root) for name in names):
            raise SystemExit("Plugin ZIP root contract failed.")
        required = {
            f"{PLUGIN_DIR.name}/catalyst-finance-demo.php",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-demo.css",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-demo.js",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-engine.js",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-cashflow-engine.js",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-comparison-engine.js",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-uncertainty-engine.js",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-pricing-engine.js",
            f"{PLUGIN_DIR.name}/assets/catalyst-finance-operating-engine.js",
            f"{PLUGIN_DIR.name}/README.md",
        }
        missing = sorted(required.difference(names))
        if missing:
            raise SystemExit(f"Plugin ZIP is missing: {', '.join(missing)}")
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Corrupt member in plugin ZIP: {bad}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--versioned-copy",
        action="store_true",
        help="Also create dist/catalyst-finance-demo-vX.Y.Z.zip.",
    )
    args = parser.parse_args()
    output = build(args.output.resolve())
    verify(output)
    print(f"Built {output}")
    if args.versioned_copy:
        versioned = output.parent / VERSIONED_NAME
        shutil.copyfile(output, versioned)
        os.utime(versioned, (0, 0))
        verify(versioned)
        print(f"Built {versioned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
