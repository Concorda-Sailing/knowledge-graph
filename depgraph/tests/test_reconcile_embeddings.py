"""Integration test: depgraph reconcile builds the embedding index for
every dossier body in the corpus."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "embed_fixture"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _setup_work(tmp_path):
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)
    # detect_orphans needs the repo dir + source file to exist
    # (same pattern as test_reconcile_route_calls).
    api_root = tmp_path / "embed-fixture-api"
    (api_root / "models").mkdir(parents=True)
    (api_root / "models" / "example.py").touch()
    cfg_path = work / "project.toml"
    txt = cfg_path.read_text().replace("/tmp/embed-fixture-api", str(api_root))
    cfg_path.write_text(txt)
    return work


def _run_reconcile(work: Path, **kwargs) -> subprocess.CompletedProcess:
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(work)}
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "extractors" / "reconcile.py")],
        capture_output=True, text=True, env=env,
        **kwargs,
    )


def test_reconcile_writes_embedding_index(tmp_path):
    work = _setup_work(tmp_path)

    result = _run_reconcile(work, timeout=120)  # first-run model dl may be slow
    assert result.returncode == 0, f"reconcile failed: {result.stderr}"

    bin_path = work / "nodes" / "_index" / "embeddings.bin"
    jsonl_path = work / "nodes" / "_index" / "embeddings.jsonl"
    assert bin_path.exists()
    assert jsonl_path.exists()

    rows = [json.loads(l) for l in jsonl_path.read_text().splitlines() if l.strip()]
    assert len(rows) >= 1
    assert all(r["node_id"] == "embed-fixture-api::models/example.py::Example" for r in rows)
    r0 = rows[0]
    assert set(r0.keys()) >= {"row", "node_id", "chunk_index", "content_hash",
                              "text_preview", "source_field"}
    assert r0["source_field"] == "dossier_body"
    assert r0["content_hash"].startswith("sha256:")

    raw = bin_path.read_bytes()
    expected_bytes = len(rows) * 384 * 2
    assert len(raw) == expected_bytes, f"bin size {len(raw)} != expected {expected_bytes}"

    meta = json.loads((work / "nodes" / "_meta.json").read_text())
    assert meta.get("embedding_status") == "ok"


def test_reconcile_skips_unchanged_dossier(tmp_path):
    """Second reconcile run with no changes — embedding bytes should round-trip
    bit-exactly (no re-embedding because content hashes match)."""
    work = _setup_work(tmp_path)

    result = _run_reconcile(work, timeout=120)
    assert result.returncode == 0, f"first reconcile failed: {result.stderr}"
    bin_path = work / "nodes" / "_index" / "embeddings.bin"
    first_bytes = bin_path.read_bytes()

    result2 = _run_reconcile(work, timeout=30)
    assert result2.returncode == 0, f"second reconcile failed: {result2.stderr}"
    assert bin_path.read_bytes() == first_bytes


def test_reconcile_records_failed_status_when_embed_raises(tmp_path):
    """If fastembed can't be imported, reconcile still produces the dep-index
    but records embedding_status: 'skipped' (or 'failed') on _meta.json."""
    work = _setup_work(tmp_path)

    # Inject a poison fastembed shim via PYTHONPATH — the shim's import raises,
    # so `try: from fastembed import TextEmbedding` in lib.embeddings fails,
    # which raises EmbeddingUnavailable from embed_chunks if called, OR
    # _EMBEDDING_AVAILABLE is False at reconcile import if the chunker import
    # also fails. Either way, reconcile should NOT crash.
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    (shim_dir / "fastembed.py").write_text(
        "raise ImportError('shim: fastembed disabled for this test')\n"
    )
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(work), "PYTHONPATH": str(shim_dir)}

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "extractors" / "reconcile.py")],
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert result.returncode == 0, f"reconcile should not fail: stderr={result.stderr}"

    # Dep-index work still happened.
    assert (work / "nodes" / "_index" / "dependents.json").exists()

    # Embedding index is either absent or empty.
    bin_path = work / "nodes" / "_index" / "embeddings.bin"
    jsonl_path = work / "nodes" / "_index" / "embeddings.jsonl"
    if jsonl_path.exists():
        rows = [json.loads(l) for l in jsonl_path.read_text().splitlines() if l.strip()]
        assert rows == [], "embedding rows should be empty when fastembed is unavailable"

    meta = json.loads((work / "nodes" / "_meta.json").read_text())
    assert meta.get("embedding_status") in ("failed", "skipped"), \
        f"expected failed/skipped, got {meta.get('embedding_status')}"
