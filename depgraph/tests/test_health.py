"""depgraph health — behavior locks for the SessionStart-timeout perf fix.

`health` is fired by the SessionStart hook under a tight time budget. Two
changes keep it inside that budget on a full corpus:
  1. the JSON-schema validator is compiled ONCE (jsonschema.validate()
     re-validates the schema itself on every call — at corpus scale that
     dominated and blew the hook's budget), and
  2. the coverage-caveat histogram is folded into the single corpus walk
     instead of a second full re-read of every node file.

These tests pin the externally-observable behavior that must survive those
perf changes: invalid nodes are still flagged, and caveat counts still show.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]            # knowledge-graph/
DEPGRAPH_BIN = REPO_ROOT / "depgraph" / "bin" / "depgraph"


def _valid_function(node_id: str, *, caveats: list[str] | None = None) -> dict:
    repo, rel, sym = node_id.split("::", 2)
    node = {
        "schema_version": 2,
        "id": node_id,
        "primitive": "function",
        "name": sym,
        "owner": None,
        "source": {"repo": repo, "path": rel, "language": "python", "line": 1, "end_line": 2},
        "signature": {"parameters": [], "return_type": None, "is_async": False, "decorators": []},
        "attributes": {},
        "structural_hash": "0" * 64,
        "kind": "function",
        "extractor": "test",
        "edges_out": [],
    }
    if caveats:
        node["coverage_caveats"] = caveats
    return node


def _setup_corpus(tmp_path: Path) -> Path:
    work = tmp_path / "depgraph"
    (work / "nodes" / "functions").mkdir(parents=True)
    (work / "nodes" / "_index").mkdir(parents=True)
    # _meta.json is the "extraction ran" liveness signal health requires.
    (work / "nodes" / "_meta.json").write_text(
        json.dumps({"node_count": 2, "regen_status": "complete"})
    )
    # Flat v2 reverse index (empty is fine for these assertions).
    (work / "nodes" / "_index" / "by_target.json").write_text("{}\n")
    return work


def _run_health(work: Path) -> subprocess.CompletedProcess:
    # KG_NO_VENV_REEXEC=1 pins execution to this interpreter (sys.executable)
    # so the test deterministically uses the same jsonschema availability the
    # `pytest.importorskip` guards below check for.
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(work),
           "PYTHONPATH": str(REPO_ROOT), "KG_NO_VENV_REEXEC": "1"}
    return subprocess.run(
        [sys.executable, str(DEPGRAPH_BIN), "health"],
        capture_output=True, text=True, timeout=60, env=env,
    )


def test_health_counts_caveats_in_single_walk(tmp_path):
    """The coverage-caveat histogram must still be produced after folding the
    second corpus walk into the main one. Independent of jsonschema."""
    work = _setup_corpus(tmp_path)
    good = _valid_function("api::a.py::good", caveats=["pydantic_refs_not_extracted"])
    (work / "nodes" / "functions" / "good.json").write_text(json.dumps(good))

    out = _run_health(work).stdout
    assert "pydantic_refs_not_extracted" in out, out


def test_health_flags_invalid_node(tmp_path):
    """Compiled validator must still catch a malformed node. Requires
    jsonschema in the interpreter that runs health (validation no-ops
    without it)."""
    pytest.importorskip("jsonschema")
    work = _setup_corpus(tmp_path)
    (work / "nodes" / "functions" / "bad.json").write_text(
        json.dumps({"id": "api::a.py::bad", "primitive": "function"})
    )
    out = _run_health(work).stdout
    assert "invalid node" in out, out


def test_health_clean_corpus_reports_no_invalid(tmp_path):
    """A well-formed corpus must not report invalid nodes — guards against the
    compiled validator becoming a no-op (false 'clean') after the refactor."""
    pytest.importorskip("jsonschema")
    work = _setup_corpus(tmp_path)
    good = _valid_function("api::a.py::good")
    (work / "nodes" / "functions" / "good.json").write_text(json.dumps(good))

    out = _run_health(work).stdout
    assert "invalid node" not in out, out
