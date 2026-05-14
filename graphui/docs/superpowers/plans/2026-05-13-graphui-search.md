# graphui — Search (Plan F)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hybrid (BM25 + semantic) search across the depgraph + logigraph corpus, surfaced via a top-bar input that takes the user to a results page at `/graph/search?q=…`. Reads the `_index/embeddings.bin` + `embeddings.jsonl` files Plan E produced.

**Architecture:** A new `app/search.py` module loads both corpora's embeddings on app start (cached, re-loaded on mtime change), computes BM25 over node titles + IDs in-process, and combines with cosine similarity over chunk vectors. Single Jinja results template renders the unified hit list with kind badges, match scores, and a matched-text snippet. The query embedder is the same `lib.embeddings` from depgraph framework — graphui imports it via the existing `sys.path` hack to the sibling depgraph repo. fastembed gets added to graphui's `requirements.txt` so the model loads on demand inside the FastAPI worker.

**Tech Stack:** FastAPI · Jinja2 · `numpy` (already a transitive dep) · `fastembed` (new direct dep). BM25 implemented inline — pure Python, ~30 lines, no extra dep.

**Spec:** `~/tools/knowledge-graph/graphui/docs/superpowers/specs/2026-05-13-graphui-categories-design.md` § 5 "Semantic search". Plan E shipped the offline indexer; this plan ships the online surface.

---

## File Structure

**New files:**
- `app/search.py` — `load_search_index()` (cached, mtime-aware), `bm25_score()`, `cosine_score()`, `search(query, scopes, limit) -> [hit]`
- `app/templates/search.html` — full-page results, hit list with badges + scores + snippets
- `tests/test_search.py` — covers BM25, cosine, hybrid, scope filtering, snippet retrieval
- `tests/test_search_route.py` — integration test for `GET /graph/search?q=…`
- `tests/fixtures/embeddings/` — synthetic `embeddings.bin` + `embeddings.jsonl` under both depgraph and logigraph fixtures (small enough to commit)

**Modified files:**
- `requirements.txt` — add `fastembed>=0.3`
- `app/templates/base.html` — add a `<form action="/graph/search" method="get">` with a single `q` input in the topbar (between the brand button and the nav links)
- `app/main.py` — add `/graph/search` route + (optional) `/graph/api/search.json` for typeahead
- `app/loader.py` — small additions: `embeddings_status()` reads `_meta.json::embedding_status` for both corpora so the search page can warn if the index is stale/missing
- `app/static/style.css` — search input + results page styles

**Out of scope (later):**
- Typeahead overlay JS (the input submits to a full-page result for now; a JS overlay is its own polish plan)
- `⌘K` keyboard shortcut focus + arrow navigation
- Match-reason highlighting via `<mark>` spans
- Tunable `weights=` query param (we ship with `0.4*BM25 + 0.6*cosine` fixed; a `?w=` knob can be added later)
- Caching warmed in-memory at app startup (we lazy-load on first query and cache by mtime — startup stays fast)

---

## Conventions

- All commits via `.venv/bin/pytest` from the graphui repo root.
- Pure-additive in `loader.py`. The search module is new.
- Trailer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.
- Embedding scoring: cosine sim of L2-normalized vectors == dot product. Cast fp16 to float32 once when loading; keep float32 in memory.

---

## Task 1: Add fastembed to graphui requirements

**Files:** `requirements.txt`

- [ ] **Step 1:** Append `fastembed>=0.3` to `requirements.txt`.
- [ ] **Step 2:** `cd ~/tools/knowledge-graph/graphui && .venv/bin/pip install -r requirements.txt` — ~80 MB install (ONNX runtime + tokenizers + huggingface-hub).
- [ ] **Step 3:** Smoke import: `.venv/bin/python -c "from fastembed import TextEmbedding; print('ok')"` → `ok`.
- [ ] **Step 4:** Run existing test suite: `.venv/bin/pytest tests/ -v` → 45 still passing.
- [ ] **Step 5:** Commit:
  ```
  git add requirements.txt
  git commit -m "feat(deps): add fastembed for the search query embedder

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 2: Fixture — synthetic embedding indexes

**Files:**
- Create: `tests/fixtures/depgraph/nodes/_index/embeddings.bin`
- Create: `tests/fixtures/depgraph/nodes/_index/embeddings.jsonl`
- Create: `tests/fixtures/logigraph/nodes/_index/embeddings.bin`
- Create: `tests/fixtures/logigraph/nodes/_index/embeddings.jsonl`

Tests need a real-shape index to load. We generate it once with the real model and commit the bytes — that way unit tests don't need fastembed installed to read the index, and the synthetic vectors are deterministic.

- [ ] **Step 1:** Write `tests/conftest_helpers/build_fixture_embeddings.py` (a one-shot script, not part of the runtime). Contents:

```python
#!/usr/bin/env python3
"""Run once to regenerate the test fixture embedding indexes.

Reads the fixture node IDs from tests/fixtures/{depgraph,logigraph}/nodes/,
embeds a small set of synthetic strings, writes embeddings.{bin,jsonl} into
each fixture's _index/ dir. Commit the result.
"""
import json
import sys
from pathlib import Path

# Use depgraph's lib via the same sys.path hack the real loader uses.
HERE = Path(__file__).resolve().parent
GRAPHUI = HERE.parent.parent
DEPGRAPH = GRAPHUI.parent / "depgraph"
sys.path.insert(0, str(DEPGRAPH))
from lib.embeddings import embed_chunks, write_index  # noqa: E402


def build_depgraph_fixture():
    base = GRAPHUI / "tests" / "fixtures" / "depgraph" / "nodes" / "_index"
    base.mkdir(parents=True, exist_ok=True)
    rows = [
        {"row": 0, "node_id": "concorda-web::app/page.tsx::Page",
         "chunk_index": 0, "content_hash": "sha256:fixture-page-0",
         "text_preview": "Landing page component.",
         "source_field": "dossier_body"},
    ]
    vecs = embed_chunks(["Landing page component. Renders the dashboard."])
    write_index(base / "embeddings.bin", base / "embeddings.jsonl", vecs, rows)


def build_logigraph_fixture():
    base = GRAPHUI / "tests" / "fixtures" / "logigraph" / "nodes" / "_index"
    base.mkdir(parents=True, exist_ok=True)
    rows = [
        {"row": 0, "node_id": "rule::category::example",
         "chunk_index": 0, "content_hash": "sha256:fixture-rule-0",
         "text_preview": "Always do the right thing.",
         "source_field": "rule_statement"},
    ]
    vecs = embed_chunks(["Always do the right thing. This is a rule about correctness."])
    write_index(base / "embeddings.bin", base / "embeddings.jsonl", vecs, rows)


if __name__ == "__main__":
    build_depgraph_fixture()
    build_logigraph_fixture()
    print("fixture embeddings rebuilt")
```

- [ ] **Step 2:** Run it:
  ```bash
  cd ~/tools/knowledge-graph/graphui
  mkdir -p tests/conftest_helpers && mv tests/conftest_helpers/build_fixture_embeddings.py tests/conftest_helpers/build_fixture_embeddings.py  # if you wrote to a different location, move it
  .venv/bin/python tests/conftest_helpers/build_fixture_embeddings.py
  ```
- [ ] **Step 3:** Verify the index files exist + are non-zero:
  ```bash
  ls -la tests/fixtures/depgraph/nodes/_index/embeddings.{bin,jsonl}
  ls -la tests/fixtures/logigraph/nodes/_index/embeddings.{bin,jsonl}
  ```
  Each `.bin` should be 768 bytes (1 row × 384 dims × 2 bytes fp16). Each `.jsonl` should have one line.
- [ ] **Step 4:** Commit the helper and the generated fixtures:
  ```
  git add tests/conftest_helpers/build_fixture_embeddings.py tests/fixtures/depgraph/nodes/_index/ tests/fixtures/logigraph/nodes/_index/
  git commit -m "test(fixtures): seed embedding indexes for search tests

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 3: `app/search.py` — index loader + scoring functions

**Files:**
- Create: `app/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1:** Write `tests/test_search.py`:
  ```python
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
      idx = load_search_index()
      # Should expose row counts per scope.
      assert idx["depgraph"]["row_count"] >= 1
      assert idx["logigraph"]["row_count"] >= 1
      # And per-row metadata + a stacked vector matrix.
      assert idx["depgraph"]["rows"][0]["node_id"] == "concorda-web::app/page.tsx::Page"
      assert idx["depgraph"]["vectors"].shape[1] == 384


  def test_search_returns_hits_for_relevant_query(loader):
      hits = search("landing page", scopes=None, limit=5)
      assert len(hits) >= 1
      h = hits[0]
      # Hit shape contract.
      for k in ("node_id", "score", "kind_hint", "source_field",
                "text_preview", "href"):
          assert k in h, f"missing key: {k}"
      assert 0.0 <= h["score"] <= 1.0


  def test_search_scope_filter_excludes_other_corpora(loader):
      # rules-only scope should not return depgraph code hits.
      hits = search("landing page", scopes=["rules"], limit=5)
      # Either zero hits or only logigraph-rule hits.
      for h in hits:
          assert h["source_field"] in ("rule_statement",), \
              f"unexpected source_field: {h['source_field']}"


  def test_search_handles_empty_query(loader):
      assert search("", scopes=None, limit=5) == []
      assert search("   ", scopes=None, limit=5) == []
  ```

- [ ] **Step 2:** Verify FAIL: `.venv/bin/pytest tests/test_search.py -v` → ImportError.
- [ ] **Step 3:** Write `app/search.py`:
  ```python
  """Hybrid search over the depgraph + logigraph embedding indexes.

  - BM25 over node titles + IDs (computed on-demand from loaded node list).
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
  import time
  from pathlib import Path
  from typing import Any

  import numpy as np

  # Reuse depgraph's lib.embeddings.read_index — same module already imported
  # by the loader via the sibling-repo sys.path hack.
  _GRAPHUI_TOOL_ROOT = Path(__file__).resolve().parent.parent
  _DEPGRAPH_TOOL_ROOT = _GRAPHUI_TOOL_ROOT.parent / "depgraph"
  if str(_DEPGRAPH_TOOL_ROOT) not in sys.path:
      sys.path.insert(0, str(_DEPGRAPH_TOOL_ROOT))
  from lib.embeddings import read_index, EmbeddingUnavailable  # noqa: E402

  from . import loader  # noqa: E402


  _BM25_K1 = 1.5
  _BM25_B = 0.75
  _BLEND_BM25 = 0.4
  _BLEND_COSINE = 0.6

  _TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

  _index_cache: dict | None = None
  _index_mtimes: dict[str, float] = {}


  def tokenize(text: str) -> list[str]:
      if not text:
          return []
      return [t.lower() for t in _TOKEN_RE.findall(text)]


  def bm25_score(query_terms: list[str], docs: list[list[str]]) -> np.ndarray:
      """Standard Okapi BM25. Returns one score per doc."""
      n = len(docs)
      if n == 0 or not query_terms:
          return np.zeros(n, dtype=np.float32)
      doc_lens = np.array([len(d) for d in docs], dtype=np.float32)
      avgdl = doc_lens.mean() if doc_lens.mean() > 0 else 1.0
      # Document frequency for each query term.
      df: dict[str, int] = {}
      for t in set(query_terms):
          df[t] = sum(1 for d in docs if t in d)
      scores = np.zeros(n, dtype=np.float32)
      for i, d in enumerate(docs):
          dl = doc_lens[i] or 1.0
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
      outputs are). query_vecs: (1, D); doc_vecs: (N, D). Returns (N,)."""
      if doc_vecs.shape[0] == 0:
          return np.zeros(0, dtype=np.float32)
      # Single-query path: dot product on normalized vectors == cosine sim.
      q = query_vecs.astype(np.float32, copy=False).reshape(-1)
      d = doc_vecs.astype(np.float32, copy=False)
      return d @ q


  def _scope_to_source_fields(scope: str) -> set[str]:
      """Map a UI scope chip to the set of source_field values it covers."""
      return {
          "code": {"dossier_body"},  # depgraph dossiers describe code
          "dossiers": {"dossier_body"},
          "rules": {"rule_statement"},
          "domain": {"domain_summary"},
          "processes": {"process_summary", "process_step"},
      }.get(scope, set())


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
      """Load both corpora's indexes, cached by mtime. Returns
      {"depgraph": {...}, "logigraph": {...}}."""
      global _index_cache
      cur_mtimes = {}
      for label, base in (("depgraph", loader.DEPGRAPH_NODES),
                          ("logigraph", loader.LOGIGRAPH_NODES)):
          bin_p = base / "_index" / "embeddings.bin"
          cur_mtimes[label] = bin_p.stat().st_mtime if bin_p.exists() else 0.0
      if _index_cache is not None and cur_mtimes == _index_mtimes:
          return _index_cache
      _index_cache = {
          "depgraph": _load_corpus("depgraph", loader.DEPGRAPH_NODES),
          "logigraph": _load_corpus("logigraph", loader.LOGIGRAPH_NODES),
      }
      _index_mtimes.clear()
      _index_mtimes.update(cur_mtimes)
      return _index_cache


  def _kind_hint(source_field: str) -> str:
      return {
          "dossier_body": "code",
          "rule_statement": "rule",
          "domain_summary": "domain",
          "process_summary": "process",
          "process_step": "process",
      }.get(source_field, source_field)


  def _href_for(node_id: str, source_field: str) -> str:
      if source_field == "rule_statement":
          return f"/graph/rule/{node_id}"
      if source_field == "domain_summary":
          return f"/graph/domain/{node_id}"
      if source_field in ("process_summary", "process_step"):
          return f"/graph/process/{node_id}"
      return f"/graph/node/{node_id}"


  def search(query: str, scopes: list[str] | None, limit: int = 20) -> list[dict]:
      """Hybrid BM25 + cosine search across both corpora. `scopes` is a list
      of UI scope chips (`rules`, `domain`, `processes`, `code`, `dossiers`)
      or None for all. Returns up to `limit` hits sorted by blended score desc.
      """
      q = (query or "").strip()
      if not q:
          return []

      # Gather candidate rows across both corpora, filtered by scope.
      idx = load_search_index()
      allowed_fields: set[str] | None = None
      if scopes:
          allowed_fields = set()
          for s in scopes:
              allowed_fields.update(_scope_to_source_fields(s))
          if not allowed_fields:
              return []

      candidates: list[dict] = []
      vec_chunks: list[np.ndarray] = []
      doc_terms: list[list[str]] = []
      for corpus in idx.values():
          rows = corpus["rows"]
          vecs = corpus["vectors"]
          if not rows or vecs.size == 0:
              continue
          for r in rows:
              if allowed_fields and r.get("source_field") not in allowed_fields:
                  continue
              candidates.append(r)
              vec_chunks.append(vecs[r["row"]:r["row"] + 1])
              # BM25 over title-like text: text_preview is the best human-readable
              # proxy we have without re-reading the node JSON every search.
              doc_terms.append(tokenize(r.get("text_preview") or "") +
                               tokenize(r.get("node_id") or ""))
      if not candidates:
          return []

      cand_vecs = np.vstack(vec_chunks)

      # Embed the query.
      try:
          from lib.embeddings import embed_chunks  # local import — avoid model
                                                    # load until first search call
          q_vec = embed_chunks([q])
      except (EmbeddingUnavailable, ImportError):
          q_vec = None

      bm = bm25_score(tokenize(q), doc_terms)
      cos = (cosine_score(q_vec, cand_vecs) if q_vec is not None and q_vec.size > 0
             else np.zeros(len(candidates), dtype=np.float32))

      # Normalize each component to [0, 1] across the candidate set.
      def _norm(arr: np.ndarray) -> np.ndarray:
          if arr.size == 0:
              return arr
          mx = float(arr.max())
          return arr / mx if mx > 0 else arr

      blended = _BLEND_BM25 * _norm(bm) + _BLEND_COSINE * _norm(cos)

      # Top-k by blended score.
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
      return hits
  ```

- [ ] **Step 4:** Verify PASS: `.venv/bin/pytest tests/test_search.py -v` → 7 passed. (First run may include a fastembed model load if the cache isn't warm from the same machine that ran Plan E — usually it is.)
- [ ] **Step 5:** Full suite: `.venv/bin/pytest tests/ -v` → 52 (45 prior + 7 new).
- [ ] **Step 6:** Commit:
  ```
  git add app/search.py tests/test_search.py
  git commit -m "feat(search): hybrid BM25 + cosine over corpus embeddings

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 4: `/graph/search` route + results template

**Files:**
- Modify: `app/main.py` — add the route
- Create: `app/templates/search.html`
- Modify: `app/static/style.css` — append search-result styles
- Create: `tests/test_search_route.py`

- [ ] **Step 1:** Failing test. Create `tests/test_search_route.py`:
  ```python
  def test_search_renders_empty_query(client):
      r = client.get("/graph/search")
      assert r.status_code == 200
      body = r.text
      assert "Search" in body
      # Empty query → empty results, but the page renders without error.
      assert "search-results" in body or "search-empty" in body or "search-form" in body


  def test_search_returns_hits_for_query(client):
      r = client.get("/graph/search?q=landing+page")
      assert r.status_code == 200
      body = r.text
      # The fixture has a dossier with the text "Landing page component."
      assert "concorda-web::app/page.tsx::Page" in body or "Landing page" in body


  def test_search_scope_chip_param_accepted(client):
      for s in ("rules", "domain", "processes", "code", "dossiers"):
          r = client.get(f"/graph/search?q=example&scope={s}")
          assert r.status_code == 200, f"scope={s} failed: {r.status_code}"
  ```

- [ ] **Step 2:** Verify FAIL: `.venv/bin/pytest tests/test_search_route.py -v` → 3 failures (404 on the route).

- [ ] **Step 3:** Add the route in `app/main.py`. Place it next to the other page routes (after `activity_page`). Add this import near the top of `app/main.py`:
  ```python
  from . import search as search_module
  ```
  Then add:
  ```python
  @app.get("/graph/search", response_class=HTMLResponse)
  def search_page(
      request: Request,
      q: str = "",
      scope: list[str] | None = None,
      limit: int = 30,
  ) -> HTMLResponse:
      """Hybrid search results. `q` is the query; `scope` may be repeated
      (e.g. ?scope=rules&scope=code) to narrow."""
      scope_list = scope if scope else None
      hits = search_module.search(q, scopes=scope_list, limit=limit) if q else []
      return TEMPLATES.TemplateResponse(
          request,
          "search.html",
          {
              "q": q,
              "scopes_selected": set(scope_list or []),
              "all_scopes": ["rules", "domain", "processes", "code", "dossiers"],
              "hits": hits,
              "limit": limit,
              "meta": loader.load_meta(),
          },
      )
  ```

- [ ] **Step 4:** Create `app/templates/search.html`:
  ```jinja
  {% extends "base.html" %}
  {% block title %}search{% endblock %}
  {% block content %}

  <div class="repo-detail-breadcrumb">
    <a href="/graph/">graphui</a> &nbsp;/&nbsp; <span>search</span>
  </div>

  <section class="search-page">
    <form action="/graph/search" method="get" class="search-form">
      <input class="search-input" type="text" name="q" value="{{ q }}" placeholder="rules, components, processes, dossiers…" autofocus>
      <button type="submit" class="search-submit">Search</button>
    </form>

    <div class="search-scopes">
      <span class="search-scopes-label">scope:</span>
      <a href="/graph/search?q={{ q }}" class="search-scope-chip{% if not scopes_selected %} search-scope-active{% endif %}">all</a>
      {% for s in all_scopes %}
        <a href="/graph/search?q={{ q }}&scope={{ s }}" class="search-scope-chip{% if s in scopes_selected %} search-scope-active{% endif %}">{{ s }}</a>
      {% endfor %}
    </div>

    {% if q and hits %}
      <p class="search-meta">{{ hits|length }} result{{ '' if hits|length == 1 else 's' }} for <code>{{ q }}</code></p>
      <ul class="search-results">
        {% for h in hits %}
        <li class="search-hit">
          <a href="{{ h.href }}" class="search-hit-title">
            <span class="search-hit-kind kind-{{ h.kind_hint }}">{{ h.kind_hint }}</span>
            <code class="search-hit-id">{{ h.node_id }}</code>
            <span class="search-hit-score">{{ "%.2f"|format(h.score) }}</span>
          </a>
          <p class="search-hit-preview">{{ h.text_preview }}</p>
        </li>
        {% endfor %}
      </ul>
    {% elif q %}
      <p class="empty">No matches for <code>{{ q }}</code>{% if scopes_selected %} in scope{{ '' if scopes_selected|length == 1 else 's' }} {{ scopes_selected|join(', ') }}{% endif %}.</p>
    {% else %}
      <p class="search-empty">Enter a query above. Search runs against rule statements, domain summaries, process steps, and component/service dossiers.</p>
    {% endif %}
  </section>

  {% endblock %}
  ```

- [ ] **Step 5:** Append to `app/static/style.css`:
  ```css
  .search-page { max-width: 900px; }
  .search-form { display: flex; gap: 6px; margin: 14px 0 8px; }
  .search-input { flex: 1; background: #0f172a; border: 1px solid #1e293b; color: #e5e7eb; padding: 8px 12px; border-radius: 4px; font-size: 14px; font-family: inherit; }
  .search-input:focus { outline: none; border-color: #3b82f6; }
  .search-submit { background: #1e3a8a; color: #bfdbfe; border: 1px solid #1e3a8a; padding: 8px 16px; border-radius: 4px; font-size: 12px; cursor: pointer; }
  .search-submit:hover { background: #1e40af; }
  .search-scopes { display: flex; gap: 6px; align-items: center; margin-bottom: 14px; }
  .search-scopes-label { color: #94a3b8; font-size: 11px; }
  .search-scope-chip { background: #0f172a; border: 1px solid #1e293b; color: #94a3b8; padding: 3px 10px; border-radius: 12px; font-size: 11px; text-decoration: none; }
  .search-scope-active { background: #1e3a8a; color: #bfdbfe; border-color: #1e3a8a; }
  .search-meta { color: #94a3b8; font-size: 12px; margin-bottom: 8px; }
  .search-results { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .search-hit { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 12px; }
  .search-hit-title { display: flex; align-items: baseline; gap: 10px; text-decoration: none; }
  .search-hit-kind { padding: 1px 8px; border-radius: 3px; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
  .kind-rule { background: #581c87; color: #e9d5ff; }
  .kind-domain { background: #14532d; color: #bbf7d0; }
  .kind-process { background: #1e3a8a; color: #bfdbfe; }
  .kind-code { background: #0c4a6e; color: #bae6fd; }
  .search-hit-id { color: #e5e7eb; font-size: 12px; flex: 1; }
  .search-hit-score { color: #94a3b8; font-size: 11px; }
  .search-hit-preview { color: #94a3b8; font-size: 12px; margin: 4px 0 0; font-style: italic; padding-left: 4px; border-left: 2px solid #3b82f6; }
  .search-empty { color: #94a3b8; font-size: 12px; margin-top: 16px; }
  ```

- [ ] **Step 6:** PASS: `.venv/bin/pytest tests/test_search_route.py -v` → 3 passed.
- [ ] **Step 7:** Full: `.venv/bin/pytest tests/ -v` → 55 passed (52 prior + 3 new).
- [ ] **Step 8:** Commit:
  ```
  git add app/main.py app/templates/search.html app/static/style.css tests/test_search_route.py
  git commit -m "feat(graphui): /graph/search route + results template

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 5: Top-bar search input

**Files:**
- Modify: `app/templates/base.html`

- [ ] **Step 1:** Add a search form to the topbar in `base.html`. Locate the `<nav>` block. Insert before it:
  ```jinja
      <form action="/graph/search" method="get" class="topbar-search">
        <input type="text" name="q" value="{{ request.query_params.get('q', '') }}" placeholder="search…" class="topbar-search-input">
      </form>
  ```

- [ ] **Step 2:** Append to `app/static/style.css`:
  ```css
  .topbar-search { flex: 1; max-width: 360px; margin: 0 12px; }
  .topbar-search-input { width: 100%; background: #0f172a; border: 1px solid #1e293b; color: #e5e7eb; padding: 5px 10px; border-radius: 3px; font-size: 12px; }
  .topbar-search-input:focus { outline: none; border-color: #3b82f6; }
  ```

- [ ] **Step 3:** Make sure base.html's flex layout accommodates the new element. The `.topbar` selector should already have `display: flex` per Plan A; the search bar takes the middle space between brand and nav.

- [ ] **Step 4:** Restart graphui + manual smoke:
  ```bash
  systemctl --user restart graphui
  sleep 2
  curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8081/graph/search?q=event"
  curl -s "http://localhost:8081/graph/" | grep -c "topbar-search-input"
  ```
  Expect: `200` for the search route; at least `1` for the search input on the dashboard.

- [ ] **Step 5:** Commit:
  ```
  git add app/templates/base.html app/static/style.css
  git commit -m "feat(graphui): topbar search input → /graph/search

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 6: Manual browser verification

**Files:** (none modified)

- [ ] **Step 1:** Open `http://localhost:8081/graph/` and type a real query into the topbar input. Examples to try:
  - `event` — should surface event-related rules, models, components
  - `crew invite` — should rank the crew-invite rule + process near the top
  - `boat` — broad query; check spread across kinds
  - `landing page` — should rank `concorda-web::app/page.tsx` near the top
- [ ] **Step 2:** Try the scope chips: from a results page, click `rules` → only rule_statement hits remain. Click `code` → only dossier_body hits.
- [ ] **Step 3:** Try a query with zero matches (e.g. `xyzqwerty123`). Confirm the empty-state copy renders.
- [ ] **Step 4:** Try the empty `/graph/search` (no `q`). Should show the form + "Enter a query above" placeholder.
- [ ] **Step 5:** Click a search result. It should navigate to the right detail page (rule, domain, process, or node).
- [ ] **Step 6:** Refresh the search input from a detail page (the `Back` link should still work alongside the search).
- [ ] **Step 7:** If anything looks wrong, fix it in its own commit. Common issues:
  - Search hangs on first query → fastembed model not yet downloaded. Wait or pre-download.
  - All hits have score 0.0 → BM25 + cosine both returned zeros. Check `tokenize` for tokenization edge cases or whether the embedding index is empty/stale.
  - Wrong kind badge → adjust `_kind_hint` mapping or the CSS class names.

---

## Self-Review Checklist

1. **Spec coverage** (§ 5 "Semantic search"):
   - ✓ Search input wired (topbar form) — Task 5
   - ✓ Hybrid BM25 + cosine — Task 3
   - ✗ Modes (`semantic` / `keyword` / `id prefix`) — **not implemented** in v1. The blend is fixed; mode pinning is a follow-up. The blended score does include both BM25 and cosine, so behavior is close to "semantic" by default.
   - ✓ Scope chips — Task 4 (chips render + filter; UI matches spec)
   - ✗ Match-reason snippet with highlighting — partial. We show `text_preview` (the first 120 chars of each chunk) as the snippet; we don't `<mark>` the matched phrases yet. Highlighting is a follow-up.
   - ✗ `⌘K` shortcut + arrow nav + `↵`/`esc` — none of the keyboard shortcuts. Follow-up.
   - ✗ Results overlay vs full-page — we ship full-page only; the overlay is JS-heavy. Follow-up.

2. **Placeholder scan:** No TBD / TODO. Every step has concrete code or commands.

3. **Type consistency:**
   - `search()` returns `[{node_id, score, kind_hint, source_field, text_preview, href}]` — Tasks 3, 4 use these keys consistently.
   - `_kind_hint` maps to `code`, `rule`, `domain`, `process` — CSS class names match in Task 4.
   - `_scope_to_source_fields` maps `rules` → `{rule_statement}` etc. — matches what reconcile actually writes in Plan E.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-graphui-search.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review, fast iteration.
**2. Inline Execution** — execute here with checkpoints.

Which approach?
