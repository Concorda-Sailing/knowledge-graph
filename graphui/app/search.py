"""Hybrid search over the depgraph + logigraph embedding indexes.

- BM25 over token bags from text_preview + node_id.
- Cosine similarity over the per-chunk embedding matrix written by
  each corpus's reconcile.
- Blended: score = 0.4 * bm25_norm + 0.6 * cosine_norm, with both
  components normalized to [0, 1] across the candidate set.

Index loading is cached by file mtime: first call reads both corpora's
`_index/embeddings.{bin,jsonl}` into memory; subsequent calls reuse the
cached structures unless either file's mtime has advanced.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np

# Reuse depgraph's lib.embeddings.read_index — same module the loader
# already imports via the sibling-repo sys.path hack.
_GRAPHUI_TOOL_ROOT = Path(__file__).resolve().parent.parent
_FRAMEWORK_ROOT = _GRAPHUI_TOOL_ROOT.parent  # ~/tools/knowledge-graph
if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))
from depgraph.lib.embeddings import read_index, EmbeddingUnavailable  # noqa: E402

from . import loader  # noqa: E402


_BM25_K1 = 1.5
_BM25_B = 0.75
_BLEND_BM25 = 0.4
_BLEND_COSINE = 0.6

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

_index_cache: dict | None = None
_index_mtimes: dict[str, float] = {}


def tokenize(text: str) -> list[str]:
    """Split text on non-alphanumeric boundaries; lowercase all tokens.

    Used both for the BM25 doc bags and for query tokenization. The
    regex skips dashes / dots / colons so `web-api::routers/events.py`
    decomposes to ['web', 'api', 'routers', 'events', 'py'].
    """
    if not text:
        return []
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def bm25_score(query_terms: list[str], docs: list[list[str]]) -> np.ndarray:
    """Standard Okapi BM25 over pre-tokenized docs. Returns one float32
    score per doc; higher = more relevant. Empty query or empty doc list
    yields all-zeros."""
    n = len(docs)
    if n == 0 or not query_terms:
        return np.zeros(n, dtype=np.float32)
    doc_lens = np.array([len(d) for d in docs], dtype=np.float32)
    avgdl = float(doc_lens.mean()) if doc_lens.mean() > 0 else 1.0
    df: dict[str, int] = {}
    for t in set(query_terms):
        df[t] = sum(1 for d in docs if t in d)
    scores = np.zeros(n, dtype=np.float32)
    for i, d in enumerate(docs):
        dl = float(doc_lens[i]) or 1.0
        for t in query_terms:
            tf = d.count(t)
            if tf == 0:
                continue
            n_t = df.get(t, 0)
            idf = math.log((n - n_t + 0.5) / (n_t + 0.5) + 1.0)
            denom = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl)
            scores[i] += idf * (tf * (_BM25_K1 + 1)) / denom
    return scores


def cosine_score(query_vecs: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    """Cosine similarity assuming both inputs are L2-normalized (bge-small
    outputs are). `query_vecs` is (1, D); `doc_vecs` is (N, D). Returns (N,)."""
    if doc_vecs.shape[0] == 0:
        return np.zeros(0, dtype=np.float32)
    q = query_vecs.astype(np.float32, copy=False).reshape(-1)
    d = doc_vecs.astype(np.float32, copy=False)
    return d @ q


def _scope_to_source_fields(scope: str) -> set[str]:
    """Map a UI scope chip to the set of source_field values it covers."""
    return {
        "dossiers": {"dossier_body"},
        "rules": {"rule_statement"},
        "domain": {"domain_summary"},
        "processes": {"process_summary", "process_step"},
        "code": {"node_summary"},
    }.get(scope, set())


# Primary mode tabs: each maps to the source_fields covered.
# `node_summary` enters via the synthetic per-node embedding pass (#37) —
# always indexed when the corpus has nodes, so semantic search has surface
# area on dossierless corpora.
MODE_FIELDS: dict[str, set[str]] = {
    "semantic": {"dossier_body", "rule_statement", "domain_summary",
                 "process_summary", "process_step", "node_summary"},
    "dep": {"dossier_body", "node_summary"},
    "knowledge": {"rule_statement", "domain_summary",
                  "process_summary", "process_step"},
    # "lexical" doesn't read from the embedding index — handled in search()
    # by routing into lexical_search() over the in-memory node corpus.
    "lexical": set(),
}


def _load_corpus(label: str, base: Path) -> dict:
    bin_p = base / "_index" / "embeddings.bin"
    jl_p = base / "_index" / "embeddings.jsonl"
    rows, vecs = read_index(bin_p, jl_p)
    return {
        "label": label,
        "rows": rows,
        "vectors": vecs.astype(np.float32, copy=False) if vecs.size else vecs,
        "row_count": len(rows),
        "bin_mtime": bin_p.stat().st_mtime if bin_p.exists() else 0.0,
    }


def load_search_index() -> dict:
    """Load both corpora's indexes, cached by file mtime + active project
    path. Returns {'depgraph': {...}, 'logigraph': {...}} where each
    value is the output of _load_corpus.

    The cache key folds in the active project so that switching projects
    in graphui reloads the right index instead of serving stale data
    from a previously-loaded project that happened to share mtimes.
    """
    global _index_cache
    proj = loader.current_project()
    depgraph_nodes = proj.depgraph_nodes_dir
    logigraph_nodes = proj.logigraph_nodes_dir
    cur_mtimes: dict[str, float | str] = {"_project_id": proj.id}
    for label, base in (("depgraph", depgraph_nodes),
                        ("logigraph", logigraph_nodes)):
        bin_p = base / "_index" / "embeddings.bin"
        cur_mtimes[label] = bin_p.stat().st_mtime if bin_p.exists() else 0.0
    if _index_cache is not None and cur_mtimes == _index_mtimes:
        return _index_cache
    _index_cache = {
        "depgraph": _load_corpus("depgraph", depgraph_nodes),
        "logigraph": _load_corpus("logigraph", logigraph_nodes),
    }
    _index_mtimes.clear()
    _index_mtimes.update(cur_mtimes)
    return _index_cache


def _kind_hint(source_field: str) -> str:
    return {
        "dossier_body": "dossier",
        "rule_statement": "rule",
        "domain_summary": "domain",
        "process_summary": "process",
        "process_step": "process",
        "node_summary": "node",
        "lexical": "node",
    }.get(source_field, source_field)


def _href_for(node_id: str, source_field: str) -> str:
    if source_field == "rule_statement":
        return f"/graph/rule/{node_id}"
    if source_field == "domain_summary":
        return f"/graph/domain/{node_id}"
    if source_field in ("process_summary", "process_step"):
        return f"/graph/process/{node_id}"
    return f"/graph/node/{node_id}"


# ---------------------------------------------------------------------------
# Lexical search — pure BM25 over the node corpus.
# ---------------------------------------------------------------------------
# The on-ramp for a fresh KG. Embeddings cover the same surface once regen
# has run a pass with fastembed available, but lexical works *immediately*:
# no model load, no index file, no dossier authoring required. Answers
# "show me the Button component" the way a developer would with `grep -r`
# (#37).

_LEXICAL_CACHE: dict | None = None
_LEXICAL_MTIME: tuple[str | None, float] = (None, 0.0)


def _build_lexical_index() -> dict:
    """Materialize the per-node lexical-search index in memory. One row
    per non-package primitive; doc-bag terms are tokenized from the
    node id, source path, kind, primitive, and name."""
    rows: list[dict] = []
    doc_terms: list[list[str]] = []
    for n in loader.load_depgraph_nodes():
        if not isinstance(n, dict):
            continue
        nid = n.get("id") or ""
        if not nid:
            continue
        if n.get("primitive") == "package":
            continue
        src = n.get("source") or {}
        repo = src.get("repo") or ""
        rel = src.get("path") or ""
        kind = n.get("kind") or n.get("primitive") or ""
        name = n.get("name") or nid.rsplit("::", 1)[-1]
        path_str = f"{repo}/{rel}" if (repo and rel) else (repo or rel or "")
        terms = (
            tokenize(nid)
            + tokenize(name)
            + tokenize(kind)
            + tokenize(path_str)
        )
        rows.append({
            "node_id": nid,
            "kind": kind,
            "name": name,
            "path": path_str,
        })
        doc_terms.append(terms)
    return {"rows": rows, "doc_terms": doc_terms}


def _load_lexical_index() -> dict:
    """Cache the lexical index by (project_id, depgraph _meta.json mtime).
    Re-extracts on regen; otherwise served from memory."""
    global _LEXICAL_CACHE, _LEXICAL_MTIME
    proj = loader.current_project()
    meta_path = proj.depgraph_nodes_dir / "_meta.json"
    mtime = meta_path.stat().st_mtime if meta_path.exists() else 0.0
    key = (proj.id, mtime)
    if _LEXICAL_CACHE is not None and _LEXICAL_MTIME == key:
        return _LEXICAL_CACHE
    _LEXICAL_CACHE = _build_lexical_index()
    _LEXICAL_MTIME = key
    return _LEXICAL_CACHE


def lexical_search(query: str, *, limit: int = 30) -> list[dict]:
    """Pure-BM25 search over node id / path / kind / name. Returns the
    same hit shape as the semantic path so the template can render either.

    Use as the default tab on day-zero corpora; once fastembed has run a
    pass over the corpus, semantic mode covers the same surface plus
    dossier bodies and logigraph entries.
    """
    q = (query or "").strip()
    if not q:
        return []
    idx = _load_lexical_index()
    rows = idx["rows"]
    doc_terms = idx["doc_terms"]
    if not rows:
        return []
    scores = bm25_score(tokenize(q), doc_terms)
    order = np.argsort(-scores)[:limit]
    hits: list[dict] = []
    for i in order:
        s = float(scores[i])
        if s <= 0:
            continue
        r = rows[i]
        nid = r["node_id"]
        hits.append({
            "node_id": nid,
            "score": s,
            "kind_hint": _kind_hint("lexical"),
            "source_field": "lexical",
            "text_preview": f"{r['kind']} · {r['path']}" if r["path"] else r["kind"],
            "href": _href_for(nid, "lexical"),
        })
    return hits


def search(query: str, scopes: list[str] | None,
           mode: str = "semantic", limit: int = 20) -> list[dict]:
    """Hybrid BM25 + cosine search across both corpora.

    `mode` is the primary tab: "semantic" (all sources), "dep" (depgraph
    dossiers only), or "knowledge" (logigraph rules/domain/processes).
    `scopes` is an optional list of granular chips (rules/domain/processes/
    code/dossiers) that further narrows WITHIN the mode.

    Returns up to `limit` hits sorted by blended score desc. Each hit is a
    dict with keys `node_id`, `score`, `kind_hint`, `source_field`,
    `text_preview`, `href`.
    """
    q = (query or "").strip()
    if not q:
        return []

    # Lexical mode bypasses the embedding index entirely (#37).
    if mode == "lexical":
        return lexical_search(q, limit=limit)

    # Compute allowed source_fields: intersect mode + scopes (if any).
    allowed_fields = MODE_FIELDS.get(mode, MODE_FIELDS["semantic"])
    if scopes:
        scope_fields: set[str] = set()
        for s in scopes:
            scope_fields.update(_scope_to_source_fields(s))
        allowed_fields = allowed_fields & scope_fields if scope_fields else allowed_fields
    if not allowed_fields:
        return []

    idx = load_search_index()

    candidates: list[dict] = []
    vec_chunks: list[np.ndarray] = []
    doc_terms: list[list[str]] = []
    for corpus in idx.values():
        rows = corpus["rows"]
        vecs = corpus["vectors"]
        if not rows or vecs.size == 0:
            continue
        for r in rows:
            if r.get("source_field") not in allowed_fields:
                continue
            candidates.append(r)
            vec_chunks.append(vecs[r["row"]:r["row"] + 1])
            doc_terms.append(tokenize(r.get("text_preview") or "") +
                             tokenize(r.get("node_id") or ""))
    if not candidates:
        # Embedding index empty / not built yet — fall through to lexical
        # so day-zero corpora aren't search-dead (#37).
        if mode in ("semantic", "dep"):
            return lexical_search(q, limit=limit)
        return []

    cand_vecs = np.vstack(vec_chunks)

    # Embed the query (lazy import — first search triggers model load).
    try:
        from depgraph.lib.embeddings import embed_chunks  # noqa: F401
        q_vec = embed_chunks([q])
    except (EmbeddingUnavailable, ImportError):
        q_vec = None

    bm = bm25_score(tokenize(q), doc_terms)
    cos = (cosine_score(q_vec, cand_vecs)
           if q_vec is not None and q_vec.size > 0
           else np.zeros(len(candidates), dtype=np.float32))

    def _norm(arr: np.ndarray) -> np.ndarray:
        if arr.size == 0:
            return arr
        mx = float(arr.max())
        return arr / mx if mx > 0 else arr

    blended = _BLEND_BM25 * _norm(bm) + _BLEND_COSINE * _norm(cos)

    order = np.argsort(-blended)[:limit]
    hits: list[dict] = []
    for i in order:
        if blended[i] <= 0:
            continue
        r = candidates[i]
        source_field = r.get("source_field", "")
        node_id = r.get("node_id", "")
        hits.append({
            "node_id": node_id,
            "score": float(blended[i]),
            "kind_hint": _kind_hint(source_field),
            "source_field": source_field,
            "text_preview": r.get("text_preview", ""),
            "href": _href_for(node_id, source_field),
        })
    # Day-zero fallback: when the embedding index is missing or doesn't
    # cover the corpus (no regen with fastembed yet), semantic mode comes
    # up empty. Drop to lexical so the user gets *something* — without
    # this the tool reads as broken on first load (#37).
    if not hits and mode in ("semantic", "dep"):
        return lexical_search(q, limit=limit)
    return hits
