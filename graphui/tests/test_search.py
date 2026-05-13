"""Tests for app.search — hybrid BM25 + cosine over the embedding indexes
produced by depgraph/logigraph reconcile."""
import numpy as np
from app.search import (
    bm25_score,
    cosine_score,
    load_search_index,
    search,
    tokenize,
)


def test_tokenize_basic():
    assert tokenize("Hello, World!") == ["hello", "world"]
    assert tokenize("concorda-api::routers/events.py::ImportEvents") == [
        "concorda", "api", "routers", "events", "py", "importevents",
    ]
    assert tokenize("") == []


def test_bm25_score_higher_for_better_match():
    docs = [
        ["hello", "world"],
        ["foo", "bar", "baz"],
        ["hello", "machine"],
    ]
    query = ["hello"]
    scores = bm25_score(query, docs)
    # Both docs containing "hello" score above the one that doesn't.
    assert scores[0] > scores[1]
    assert scores[2] > scores[1]


def test_cosine_score_with_orthogonal_vectors():
    a = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
    b = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    scores = cosine_score(a, b)
    assert scores.shape == (2,)
    assert abs(scores[0] - 1.0) < 1e-5
    assert abs(scores[1]) < 1e-5


def test_load_search_index_reads_both_corpora(loader):
    import app.search as search_mod
    search_mod._index_cache = None  # clear stale cache so loader paths are re-resolved
    idx = load_search_index()
    # Should expose row counts per scope.
    assert idx["depgraph"]["row_count"] >= 1
    assert idx["logigraph"]["row_count"] >= 1
    # And per-row metadata + a stacked vector matrix.
    assert idx["depgraph"]["rows"][0]["node_id"] == "concorda-web::app/page.tsx::Page"
    assert idx["depgraph"]["vectors"].shape[1] == 384


def test_search_returns_hits_for_relevant_query(loader):
    import app.search as search_mod
    search_mod._index_cache = None
    hits = search("landing page", scopes=None, limit=5)
    assert len(hits) >= 1
    h = hits[0]
    # Hit shape contract.
    for k in ("node_id", "score", "kind_hint", "source_field",
              "text_preview", "href"):
        assert k in h, f"missing key: {k}"
    assert 0.0 <= h["score"] <= 1.0


def test_search_scope_filter_excludes_other_corpora(loader):
    import app.search as search_mod
    search_mod._index_cache = None
    # rules-only scope should not return depgraph code hits.
    hits = search("landing page", scopes=["rules"], limit=5)
    # Either zero hits or only logigraph-rule hits.
    for h in hits:
        assert h["source_field"] in ("rule_statement",), \
            f"unexpected source_field: {h['source_field']}"


def test_search_handles_empty_query(loader):
    assert search("", scopes=None, limit=5) == []
    assert search("   ", scopes=None, limit=5) == []
