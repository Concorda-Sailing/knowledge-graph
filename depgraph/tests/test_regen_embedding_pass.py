"""Integration tests for the embedding pass in v2 regen.

The v1 reconcile.py ran `_run_embedding_pass` as part of finalization;
the v2 cutover dropped it (#38 gap A). These tests pin the wiring so
the embedding index lands on disk after regen and the `--no-embeddings`
opt-out skips it cleanly.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tiny_python_repo(tmp_path: Path) -> Path:
    src = tmp_path / "repo"
    api = src / "api"
    api.mkdir(parents=True)
    (api / "main.py").write_text(
        "def helper(): pass\n\n"
        "def create_event():\n"
        "    helper()\n"
    )
    return src


def _regen(data_dir: Path, repo_path: Path, *extra: str) -> subprocess.CompletedProcess:
    data_dir.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            sys.executable, "-m", "kg.cli", "depgraph", "regen",
            "--data-dir", str(data_dir),
            "--repo-key", "api", "--repo-path", str(repo_path / "api"),
            *extra,
        ],
        capture_output=True, text=True, timeout=120,
    )


def test_default_regen_runs_embedding_pass(tmp_path, tiny_python_repo):
    """Default `depgraph regen` should produce the embedding index and
    stamp `embedding_status` into `_meta.json`. Status will be "ok" when
    fastembed is installed, "skipped" otherwise — either way the field
    must be set so downstream consumers can tell the pass ran."""
    data_dir = tmp_path / "out"
    r = _regen(data_dir, tiny_python_repo)
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"

    meta = json.loads((data_dir / "depgraph" / "nodes" / "_meta.json").read_text())
    assert "embedding_status" in meta, "embedding_status missing from _meta.json"
    assert meta["embedding_status"] in ("ok", "failed", "skipped")

    # If fastembed is available the pass succeeded → embedding index on disk.
    # If skipped, the index files are legitimately absent.
    bin_path = data_dir / "depgraph" / "nodes" / "_index" / "embeddings.bin"
    jsonl_path = data_dir / "depgraph" / "nodes" / "_index" / "embeddings.jsonl"
    if meta["embedding_status"] == "ok":
        assert bin_path.exists() and jsonl_path.exists(), (
            "embedding_status=ok but index files missing"
        )


def test_no_embeddings_flag_skips_pass(tmp_path, tiny_python_repo):
    """`--no-embeddings` must short-circuit the pass: no embed call, no
    index files written, and `embedding_status=skipped` in _meta.json."""
    data_dir = tmp_path / "out"
    r = _regen(data_dir, tiny_python_repo, "--no-embeddings")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"

    meta = json.loads((data_dir / "depgraph" / "nodes" / "_meta.json").read_text())
    assert meta["embedding_status"] == "skipped"

    bin_path = data_dir / "depgraph" / "nodes" / "_index" / "embeddings.bin"
    jsonl_path = data_dir / "depgraph" / "nodes" / "_index" / "embeddings.jsonl"
    assert not bin_path.exists()
    assert not jsonl_path.exists()
