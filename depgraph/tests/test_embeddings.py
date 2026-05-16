"""Tests for lib.embeddings — the fastembed-driven indexer.

The model is loaded lazily on first call. Tests use the real model (small
enough to be reasonable in CI); first-run download (~140 MB) caches under
~/.cache/huggingface — subsequent runs are fast."""
import json
import numpy as np
from depgraph.lib.embeddings import (
    embed_chunks,
    write_index,
    read_index,
    vector_dim,
)


def test_embed_chunks_returns_fp16_matrix():
    chunks = ["hello world", "this is a sailing regatta"]
    vecs = embed_chunks(chunks)
    assert vecs.dtype == np.float16
    assert vecs.shape == (2, vector_dim())
    # Vectors should be L2-normalized (bge models output normalized).
    norms = np.linalg.norm(vecs.astype(np.float32), axis=1)
    assert np.allclose(norms, 1.0, atol=0.01)


def test_embed_chunks_empty_returns_empty_matrix():
    vecs = embed_chunks([])
    assert vecs.shape == (0, vector_dim())
    assert vecs.dtype == np.float16


def test_write_then_read_round_trip(tmp_path):
    """Indexing round-trip: write_index(rows, vecs) then read_index(...) gives
    back the same rows + vectors."""
    rows = [
        {"row": 0, "node_id": "x::a", "chunk_index": 0,
         "content_hash": "sha256:aaa", "text_preview": "alpha",
         "source_field": "dossier_body"},
        {"row": 1, "node_id": "x::b", "chunk_index": 0,
         "content_hash": "sha256:bbb", "text_preview": "beta",
         "source_field": "dossier_body"},
    ]
    vecs = embed_chunks(["alpha text", "beta text"])
    bin_path = tmp_path / "embeddings.bin"
    jsonl_path = tmp_path / "embeddings.jsonl"
    write_index(bin_path, jsonl_path, vecs, rows)

    read_rows, read_vecs = read_index(bin_path, jsonl_path)
    assert len(read_rows) == 2
    assert read_rows[0]["node_id"] == "x::a"
    assert read_vecs.shape == (2, vector_dim())
    assert read_vecs.dtype == np.float16
    # Vectors round-trip bit-exactly.
    assert np.array_equal(read_vecs, vecs)


def test_read_missing_index_returns_empty(tmp_path):
    rows, vecs = read_index(tmp_path / "missing.bin", tmp_path / "missing.jsonl")
    assert rows == []
    assert vecs.shape == (0, vector_dim())
