"""Regression test: bin/depgraph X and bin/kg depgraph X produce identical output.

Same for logigraph.  Both routes now dispatch into the same Python
handlers via lib/cli/build_parser(), so drift would be a silent
regression — this test catches it.

Tests skip cleanly in environments without ~/concorda-knowledge-graph/.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"
DEPGRAPH_BIN = TOOL_ROOT / "depgraph" / "bin" / "depgraph"
LOGIGRAPH_BIN = TOOL_ROOT / "logigraph" / "bin" / "logigraph"

_CONCORDA_KG = Path.home() / "concorda-knowledge-graph"
_DEPGRAPH_DATA = _CONCORDA_KG / "depgraph"
_LOGIGRAPH_DATA = _CONCORDA_KG / "logigraph"


def _have_live_data() -> bool:
    """Return True if the concorda knowledge-graph data dir is present."""
    return (_DEPGRAPH_DATA / "nodes").exists()


# ---------------------------------------------------------------------------
# depgraph parity
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _have_live_data(), reason="needs ~/concorda-knowledge-graph")
@pytest.mark.parametrize("subcmd", [
    ["--help"],
    ["health"],
    ["stats"],
    ["repo-list"],
    ["validate"],
])
def test_depgraph_legacy_vs_kg_parity(subcmd: list[str]) -> None:
    """`depgraph X` and `kg depgraph X` produce byte-for-byte identical output."""
    data_dir = str(_DEPGRAPH_DATA)

    env_legacy = {**os.environ, "DEPGRAPH_DATA_DIR": data_dir}

    legacy = subprocess.run(
        [sys.executable, str(DEPGRAPH_BIN), *subcmd],
        env=env_legacy,
        capture_output=True,
        text=True,
    )

    # kg depgraph resolves the project via --data-dir; the subprocess form is used
    # to avoid in-process sys.path contamination between test parametrize runs.
    env_kg = {**os.environ}
    via_kg = subprocess.run(
        [sys.executable, str(KG_BIN), "depgraph", "--data-dir", data_dir, *subcmd],
        env=env_kg,
        capture_output=True,
        text=True,
    )

    assert legacy.stdout == via_kg.stdout, (
        f"stdout drift for `depgraph {' '.join(subcmd)}`:\n"
        f"--- legacy ---\n{legacy.stdout}\n--- via kg ---\n{via_kg.stdout}"
    )
    assert legacy.returncode == via_kg.returncode, (
        f"exit-code drift for `depgraph {' '.join(subcmd)}`: "
        f"legacy={legacy.returncode} kg={via_kg.returncode}"
    )


# ---------------------------------------------------------------------------
# logigraph parity
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _have_live_data(), reason="needs ~/concorda-knowledge-graph")
@pytest.mark.parametrize("subcmd", [
    ["--help"],
    ["health"],
    ["stats"],
])
def test_logigraph_legacy_vs_kg_parity(subcmd: list[str]) -> None:
    """`logigraph X` and `kg logigraph X` produce byte-for-byte identical output."""
    logi_dir = str(_LOGIGRAPH_DATA)
    dep_dir = str(_DEPGRAPH_DATA)

    env_legacy = {
        **os.environ,
        "LOGIGRAPH_DATA_DIR": logi_dir,
        "DEPGRAPH_DATA_DIR": dep_dir,
    }

    legacy = subprocess.run(
        [sys.executable, str(LOGIGRAPH_BIN), *subcmd],
        env=env_legacy,
        capture_output=True,
        text=True,
    )

    # kg logigraph resolves via --data-dir (the logigraph subdir); the resolver
    # steps up to the parent bundle dir and derives depgraph_dir from there.
    env_kg = {**os.environ}
    via_kg = subprocess.run(
        [sys.executable, str(KG_BIN), "logigraph", "--data-dir", logi_dir, *subcmd],
        env=env_kg,
        capture_output=True,
        text=True,
    )

    assert legacy.stdout == via_kg.stdout, (
        f"stdout drift for `logigraph {' '.join(subcmd)}`:\n"
        f"--- legacy ---\n{legacy.stdout}\n--- via kg ---\n{via_kg.stdout}"
    )
    assert legacy.returncode == via_kg.returncode, (
        f"exit-code drift for `logigraph {' '.join(subcmd)}`: "
        f"legacy={legacy.returncode} kg={via_kg.returncode}"
    )
