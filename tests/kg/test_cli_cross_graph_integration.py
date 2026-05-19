"""Cross-graph in-process integration: depgraph then logigraph in the same process.

Uses the same `single_project` fixture pattern as test_cli_subprocess_shims.py.
Verifies that the lib namespace eviction in kg/cli/logigraph.py correctly
switches the 'lib' namespace so both graphs work end-to-end without the
second call resolving to the wrong lib package.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


@pytest.fixture
def single_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Mirror of the fixture in test_cli_subprocess_shims.py."""
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    root = tmp_path / "solo-knowledge-graph"
    (root / "depgraph" / "nodes").mkdir(parents=True)
    (root / "logigraph" / "nodes").mkdir(parents=True)
    (root / "project.toml").write_text(
        '[project]\nname = "solo"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    (root / "depgraph" / "project.toml").write_text('[project]\nname = "solo"\n')
    depgraph_dir = root / "depgraph"
    (root / "logigraph" / "project.toml").write_text(
        f'[project]\nname = "solo"\n\n[depgraph]\ndata_dir = "{depgraph_dir}"\n'
    )
    # Stub _meta.json on both sides so health passes the post-#61/#62
    # liveness gate. These tests exercise cross-graph dispatch — they
    # simulate a post-regen project, not the never-extracted state.
    (root / "depgraph" / "nodes" / "_meta.json").write_text(
        '{"schema_version": 2, "regen_status": "complete", "node_count": 0}'
    )
    (root / "logigraph" / "nodes" / "_meta.json").write_text(
        '{"schema_version": 1, "regen_status": "complete", "node_count": 0}'
    )
    subprocess.run(
        [sys.executable, str(KG_BIN), "project", "add", str(root)],
        check=True, env={**os.environ, "KG_REGISTRY_PATH": str(reg)},
    )
    return {"root": root, "registry": reg}


def _run(env_reg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True,
        env={**os.environ, "KG_REGISTRY_PATH": str(env_reg)},
    )


# ---------------------------------------------------------------------------
# Sequential subprocess invocations (the standard integration form)
# ---------------------------------------------------------------------------

def test_kg_depgraph_then_logigraph_health_both_succeed(single_project: dict) -> None:
    """kg depgraph health followed by kg logigraph health both return 0.

    This validates the complete cross-graph dispatch pipeline. While each
    invocation is a separate process (subprocess.run), together they confirm
    that project resolution, Context construction, and the health command
    handlers work for both graph types from the same project layout.
    """
    reg = single_project["registry"]

    dg_res = _run(reg, "depgraph", "health")
    lg_res = _run(reg, "logigraph", "health")

    assert dg_res.returncode == 0, f"depgraph health failed: {dg_res.stderr}"
    assert lg_res.returncode == 0, f"logigraph health failed: {lg_res.stderr}"


def test_kg_depgraph_validate_then_logigraph_validate_both_succeed(
    single_project: dict,
) -> None:
    """kg depgraph validate then kg logigraph validate both return 0 on empty graphs."""
    reg = single_project["registry"]

    dg_res = _run(reg, "depgraph", "validate")
    lg_res = _run(reg, "logigraph", "validate")

    assert dg_res.returncode == 0, f"depgraph validate failed: {dg_res.stderr}"
    assert lg_res.returncode == 0, f"logigraph validate failed: {lg_res.stderr}"


# ---------------------------------------------------------------------------
# In-process sequential dispatch (verifies the lib namespace switch)
# ---------------------------------------------------------------------------

def test_kg_depgraph_then_logigraph_in_same_process(single_project: dict) -> None:
    """Call kg.cli.main() twice in the same Python session: depgraph health then
    logigraph health. The sys.modules eviction in kg/cli/logigraph.py must
    cleanly switch the 'lib' namespace between the two calls.

    We use subprocess with a short inline script so the two calls run in the
    same interpreter process — something we cannot do from within the test
    process itself because the conftest.py namespace management is already
    active here.
    """
    reg = single_project["registry"]
    script = (
        "import sys, os\n"
        f"sys.path.insert(0, '{TOOL_ROOT}')\n"
        f"os.environ['KG_REGISTRY_PATH'] = '{reg}'\n"
        "from kg.cli import main\n"
        "rc1 = main(['depgraph', 'health'])\n"
        "rc2 = main(['logigraph', 'health'])\n"
        "sys.exit(0 if (rc1 == 0 and rc2 == 0) else 1)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"In-process cross-graph dispatch failed.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
