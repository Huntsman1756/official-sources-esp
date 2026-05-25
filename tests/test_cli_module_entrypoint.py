from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_python_module_cli_entrypoint_uses_source_tree_registry():
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "official_sources.cli",
            "sources",
            "status",
            "--source",
            "BOIB",
        ],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "source_code=BOIB" in result.stdout
    assert "operational_status=monitor_validated" in result.stdout
    assert "monitor_support=available" in result.stdout
