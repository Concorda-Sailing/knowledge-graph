"""Tests for `refresh_node_embeddings` — incremental per-node update of
the embedding index, used by the dossier-finalize / dossier-bump
lifecycle commands so authored content is searchable immediately (#36).

The fastembed model load is monkeypatched out: we replace
`embed_chunks` with a deterministic stub that returns one row of
all-ones per chunk. This lets us assert the merge math (drop +
re-insert + renumber) without paying the model-download cost.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from depgraph.extractors import reconcile
from depgraph.lib.embeddings import VECTOR_DIM, write_index


def _stub_embed(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Replace embed_chunks with a deterministic stub. Returns a mutable
    list capturing each call's input chunks so tests can assert on the
    re-embed boundary."""
    calls: list[list[str]] = []

    def fake(chunks: list[str]) -> np.ndarray:
        calls.append(list(chunks))
        if not chunks:
            return np.zeros((0, VECTOR_DIM), dtype=np.float16)
        return np.ones((len(chunks), VECTOR_DIM), dtype=np.float16)

    monkeypatch.setattr(reconcile, "embed_chunks", fake)
    monkeypatch.setattr(reconcile, "_EMBEDDING_AVAILABLE", True)
    return calls


def _seed_index(data_dir: Path, rows: list[dict]) -> None:
    """Write a minimal seed embedding index for tests to refresh against."""
    index_dir = data_dir / "nodes" / "_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    vecs = np.zeros((len(rows), VECTOR_DIM), dtype=np.float16)
    # Encode the row's index into the vector so tests can tell them apart.
    for i in range(len(rows)):
        vecs[i, 0] = np.float16(i + 1)
        rows[i]["row"] = i
    write_index(index_dir / "embeddings.bin", index_dir / "embeddings.jsonl",
                vecs, rows)


def _read_index(data_dir: Path) -> tuple[list[dict], np.ndarray]:
    from depgraph.lib.embeddings import read_index
    return read_index(
        data_dir / "nodes" / "_index" / "embeddings.bin",
        data_dir / "nodes" / "_index" / "embeddings.jsonl",
    )


def _make_node(node_id: str, *, dossier_rel: str | None = None) -> dict:
    return {
        "id": node_id,
        "primitive": "function",
        "kind": "service",
        "name": node_id.split("::")[-1],
        "owner": None,
        "source": {"repo": "api", "path": "services/foo.py",
                    "language": "python", "line": 1, "end_line": 5},
        "signature": {"parameters": [], "return_type": None},
        "attributes": {},
        "edges_out": [],
        "dossier": dossier_rel,
    }


def _write_dossier(data_dir: Path, rel: str, body: str) -> None:
    p = data_dir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\nnode_id: x\nstatus: llm_drafted\n---\n\n# Title\n\n{body}\n"
    )


def test_refresh_replaces_existing_rows_for_target_node(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _stub_embed(monkeypatch)
    # Seed two nodes' rows in the existing index — one of them is the
    # target, the other must be preserved untouched.
    other_summary = "api::other.py::other\nkind: function"
    target_old_summary = "api::services/foo.py::foo\nkind: function"
    _seed_index(tmp_path, [
        {"node_id": "api::other.py::other", "chunk_index": 0,
         "content_hash": reconcile._chunk_hash(other_summary),
         "text_preview": "other preview",
         "source_field": "node_summary"},
        {"node_id": "api::services/foo.py::foo", "chunk_index": 0,
         "content_hash": reconcile._chunk_hash(target_old_summary),
         "text_preview": "old foo preview",
         "source_field": "node_summary"},
    ])

    node = _make_node("api::services/foo.py::foo",
                       dossier_rel="dossiers/api/services/foo.py/foo.md")
    _write_dossier(tmp_path, node["dossier"], "Fresh dossier body for foo.")

    status = reconcile.refresh_node_embeddings(node, tmp_path)
    assert status == "ok"

    rows, vecs = _read_index(tmp_path)
    # Exactly one row for the other node (preserved); exactly two for the
    # target (synthetic summary + dossier body).
    by_node: dict[str, list[dict]] = {}
    for r in rows:
        by_node.setdefault(r["node_id"], []).append(r)
    assert set(by_node) == {"api::other.py::other", "api::services/foo.py::foo"}
    assert len(by_node["api::other.py::other"]) == 1
    foo_rows = by_node["api::services/foo.py::foo"]
    foo_fields = {r["source_field"] for r in foo_rows}
    assert foo_fields == {"node_summary", "dossier_body"}
    # Row indices are contiguous and match the bin layout.
    for i, r in enumerate(rows):
        assert r["row"] == i


def test_refresh_carries_forward_unchanged_synthetic_summary_vector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the node's signature hasn't changed, its synthetic summary
    has the same content_hash as the prior row — the existing vector
    must carry forward, not re-embed."""
    calls = _stub_embed(monkeypatch)
    node = _make_node("api::services/foo.py::foo")
    summary = reconcile._synthetic_node_summary(node)
    _seed_index(tmp_path, [
        {"node_id": node["id"], "chunk_index": 0,
         "content_hash": reconcile._chunk_hash(summary),
         "text_preview": summary[:120].replace("\n", " "),
         "source_field": "node_summary"},
    ])

    status = reconcile.refresh_node_embeddings(node, tmp_path)
    assert status == "ok"
    # No dossier, summary unchanged → embed_chunks should have been called
    # with an empty list (no fresh embeds needed).
    assert calls == [[]] or all(not c for c in calls)


def test_refresh_returns_skipped_when_no_index_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If there's no prior pass yet (pre-first-regen), refresh defers
    to the next full regen rather than building an index from scratch."""
    _stub_embed(monkeypatch)
    node = _make_node("api::services/foo.py::foo")
    status = reconcile.refresh_node_embeddings(node, tmp_path)
    assert status == "skipped"


def test_refresh_returns_skipped_when_fastembed_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(reconcile, "_EMBEDDING_AVAILABLE", False)
    node = _make_node("api::services/foo.py::foo")
    status = reconcile.refresh_node_embeddings(node, tmp_path)
    assert status == "skipped"


def test_refresh_replaces_dossier_chunks_when_body_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Updating the dossier body changes its chunks' content_hash, so
    refresh must drop the old dossier_body rows and emit new ones."""
    _stub_embed(monkeypatch)
    node = _make_node("api::services/foo.py::foo",
                       dossier_rel="dossiers/api/services/foo.py/foo.md")
    _write_dossier(tmp_path, node["dossier"], "Original body.")
    # First pass: seed via refresh itself (after seeding a no-op prior index).
    _seed_index(tmp_path, [])
    # An empty seed index returns "skipped", so plant a one-row index first:
    _seed_index(tmp_path, [
        {"node_id": "api::other::z", "chunk_index": 0,
         "content_hash": "sha256:dead",
         "text_preview": "z", "source_field": "node_summary"},
    ])
    s1 = reconcile.refresh_node_embeddings(node, tmp_path)
    assert s1 == "ok"
    rows_a, _ = _read_index(tmp_path)
    body_a = next(r for r in rows_a if r["source_field"] == "dossier_body"
                  and r["node_id"] == node["id"])

    # Mutate the dossier and refresh again.
    _write_dossier(tmp_path, node["dossier"], "Revised body, different text.")
    s2 = reconcile.refresh_node_embeddings(node, tmp_path)
    assert s2 == "ok"
    rows_b, _ = _read_index(tmp_path)
    body_b = next(r for r in rows_b if r["source_field"] == "dossier_body"
                  and r["node_id"] == node["id"])
    assert body_b["content_hash"] != body_a["content_hash"]
    # The unrelated row is still present.
    assert any(r["node_id"] == "api::other::z" for r in rows_b)


def test_dossier_finalize_invokes_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: dossier-finalize triggers an embedding refresh so the
    new dossier shows up in the index without waiting for regen (#36)."""
    import argparse
    from depgraph.lib.cli.context import Context
    from depgraph.lib.cli.dossier import cmd_dossier_finalize

    data_dir = tmp_path / "depgraph"
    nodes_dir = data_dir / "nodes" / "functions"
    nodes_dir.mkdir(parents=True)
    node = _make_node("api::services/foo.py::foo",
                       dossier_rel="dossiers/api/services/foo.py/foo.md")
    node["structural_hash"] = "deadbeef01234567"
    (nodes_dir / "foo.json").write_text(json.dumps(node))

    body_file = tmp_path / "body.md"
    body_file.write_text("## Purpose\n\nDoes a thing.\n")

    _stub_embed(monkeypatch)
    _seed_index(data_dir, [
        {"node_id": "api::placeholder", "chunk_index": 0,
         "content_hash": "sha256:abc",
         "text_preview": "p", "source_field": "node_summary"},
    ])

    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(
        node_id=node["id"], body_file=str(body_file), authored_by=[],
    )
    rc = cmd_dossier_finalize(args, ctx)
    assert rc == 0

    rows, _ = _read_index(data_dir)
    fields_for_node = {r["source_field"] for r in rows if r["node_id"] == node["id"]}
    assert fields_for_node == {"node_summary", "dossier_body"}
