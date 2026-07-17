from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_governance_cli_writes_all_formats(tmp_path: Path) -> None:
    out = tmp_path / "publication.json"
    csv = tmp_path / "trace.csv"
    md = tmp_path / "brief.md"
    html = tmp_path / "brief.html"
    public = tmp_path / "public.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "catalyst_finance.governance_cli",
            "data/sample_governance.json",
            "--output",
            str(out),
            "--csv",
            str(csv),
            "--markdown",
            str(md),
            "--html",
            str(html),
            "--public-json",
            str(public),
        ],
        cwd=ROOT,
        check=True,
    )
    assert json.loads(out.read_text())["readiness"]["status"] == "published"
    assert csv.read_text().startswith("claim_id,classification,complete")
    assert md.read_text().startswith("# Efficiency Retrofit Finance Brief")
    assert "<!doctype html>" in html.read_text()
    assert len(json.loads(public.read_text())["sources"]) == 2
