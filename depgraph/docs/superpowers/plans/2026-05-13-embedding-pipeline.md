# Embedding Pipeline (Plan E)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a per-data-dir embedding index (`_index/embeddings.bin` + `_index/embeddings.jsonl`) that covers every dossier body (depgraph) and every rule statement / domain summary / process step description (logigraph). The index is incremental — chunks whose content hash matches the prior index carry forward with no re-embed. Plan F (graphui search route) consumes this index.

**Architecture:** A new shared lib lives in **depgraph** (`lib/chunker.py` + `lib/embeddings.py`); both depgraph's and logigraph's `reconcile.py` import it. Embedding model is **`BAAI/bge-small-en-v1.5`** via **`fastembed`** (ONNX runtime, ~80 MB installed footprint vs ~2 GB for `sentence-transformers`+torch). Model loads lazily on first call, runs CPU-only, ~140 MB on disk after first download. Failure mode is **block-only**: if the model can't load or an embed call raises, the embedding pass writes an `embedding_status: "failed"` flag to `_meta.json` and exits cleanly — the dependency-index work that ran before it stays intact.

**Tech Stack:** Python stdlib + `fastembed` + `numpy` (already a transitive dep of fastembed). The embedding model file (~140 MB) is downloaded lazily by fastembed; not vendored in the repo.

**Spec:** `~/tools/knowledge-graph/graphui/docs/superpowers/specs/2026-05-13-graphui-categories-design.md` § 5 ("Semantic search"). This plan implements only the offline indexing piece; the search route + UI is Plan F.

---

## File Structure

**New files (depgraph framework):**
- `lib/chunker.py` — text → 512-token chunks with 128-token overlap
- `lib/embeddings.py` — fastembed loader, batch embed, index reader/writer
- `tests/test_chunker.py`
- `tests/test_embeddings.py`
- `tests/test_reconcile_embeddings.py`
- `tests/fixtures/embed_fixture/project.toml`
- `tests/fixtures/embed_fixture/nodes/_meta.json`
- `tests/fixtures/embed_fixture/nodes/models/example_model.json`
- `tests/fixtures/embed_fixture/dossiers/models/example_model.md`

**Modified files (depgraph framework):**
- `requirements.txt` — add `fastembed>=0.3`
- `extractors/reconcile.py` — new `_run_embedding_pass(data_dir, kind)` step called after the reverse-index build

**Modified files (logigraph framework):**
- `extractors/reconcile.py` — same embedding pass, calling into depgraph's `lib.embeddings`
- `tests/test_reconcile_embeddings_logigraph.py` (new)
- `tests/fixtures/embed_fixture_logigraph/` (new — rule + domain + process nodes with body content)

**Index file format** (per data dir, written by reconcile):
- `nodes/_index/embeddings.bin` — raw fp16 little-endian, shape `(N_rows, 384)` for bge-small. Read via `numpy.frombuffer(...).reshape(N, 384)`. No header bytes — header is in the sidecar.
- `nodes/_index/embeddings.jsonl` — one JSON object per line, in order matching the rows:
  ```json
  {"row": 0, "node_id": "concorda-api::models/event.py::Event", "chunk_index": 0, "content_hash": "sha256:abcd...", "text_preview": "Event model — represents one sailing event...", "source_field": "dossier_body"}
  ```
  `source_field` is one of `"dossier_body"` · `"rule_statement"` · `"domain_summary"` · `"process_step"`.

**Out of scope (Plan F):**
- The `/graph/search` route in graphui
- The `/graph/api/search.json` typeahead backend
- BM25 + cosine hybrid retrieval logic (lives in graphui's loader)
- Top-bar search input wiring

---

## Conventions for this plan

- **Test-first** for every lib + reconcile change.
- **`fastembed` model downloads on first use** — tests should mock the embed function or use a small fixture. The integration tests can do a real first-run download but must complete in <60s on a CPU with a warm cache.
- **All commits via `pytest`** from the respective framework repo root.
- **Block-only failure semantics:** the embedding pass writes to `_meta.json::embedding_status` (`"ok"` · `"failed"` · `"skipped"`) and never raises out of `reconcile.main`.
- Trailer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

---

## Task 1: Add `fastembed` to depgraph requirements

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Read the current requirements**

```bash
cd ~/tools/knowledge-graph/depgraph
cat requirements.txt
```

- [ ] **Step 2: Append fastembed**

Append to `requirements.txt`:
```
fastembed>=0.3
```

If `numpy` isn't already pinned, do NOT add it — fastembed declares it as a transitive dep and we want their pin.

- [ ] **Step 3: Install in the depgraph venv**

```bash
cd ~/tools/knowledge-graph/depgraph
# If a venv exists at .venv:
.venv/bin/pip install -r requirements.txt
# Otherwise (system python): pip install --user -r requirements.txt
```

First install pulls ONNX runtime (~80 MB). Expect ~30s on a fresh box.

- [ ] **Step 4: Sanity-check the import**

```bash
.venv/bin/python -c "from fastembed import TextEmbedding; print('ok')"
```
Or with system python if there's no venv. Expected: `ok`.

- [ ] **Step 5: Commit**

```
git add requirements.txt
git commit -m "feat(deps): add fastembed for the embedding pipeline

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `lib/chunker.py` — sliding-window chunker

**Files:**
- Create: `lib/chunker.py`
- Create: `tests/test_chunker.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_chunker.py`:
```python
"""Tests for lib.chunker — sliding-window text chunking for the embedding pass.

Chunks short inputs to a single chunk. Long inputs get split into overlapping
512-token windows with 128-token overlap. Token count is approximated as
1 token ~= 4 characters (this is the fastembed-recommended back-of-envelope;
exact bge-small tokenization gives slightly different counts but the chunker
doesn't need precision — it just needs to not exceed the model context window)."""
from lib.chunker import chunk_text


def test_short_text_one_chunk():
    out = chunk_text("This is a short sentence.")
    assert len(out) == 1
    assert out[0] == "This is a short sentence."


def test_empty_text_no_chunks():
    assert chunk_text("") == []
    assert chunk_text(None) == []


def test_long_text_splits_with_overlap():
    # ~3000 chars ~= ~750 tokens — should yield 2 chunks with overlap.
    text = ("paragraph one. " * 50) + "\n\n" + ("paragraph two. " * 50) + "\n\n" + ("paragraph three. " * 100)
    out = chunk_text(text)
    assert len(out) >= 2
    # Each chunk under the 512-token approximation (~2048 chars).
    for c in out:
        assert len(c) <= 2200, f"chunk too long: {len(c)} chars"
    # Adjacent chunks overlap (the last ~128 tokens of chunk N == first ~128 tokens of N+1).
    # Approximate check: at least 200 chars of the end of out[0] appears in out[1].
    if len(out) >= 2:
        tail = out[0][-200:]
        assert tail[:50] in out[1] or tail[100:150] in out[1], "no overlap detected"


def test_paragraph_aware_splitting():
    """Chunker prefers to split at paragraph boundaries (`\\n\\n`) when possible."""
    para = "Sentence. " * 30
    text = para + "\n\n" + para + "\n\n" + para * 3  # last block forces a split
    out = chunk_text(text)
    # The first chunk should end at or before a paragraph boundary.
    if len(out) >= 2:
        assert out[0].endswith(".") or out[0].endswith("\n")
```

- [ ] **Step 2: Verify FAIL**

```bash
cd ~/tools/knowledge-graph/depgraph
DEPGRAPH_DATA_DIR=$(pwd) pytest tests/test_chunker.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement**

Create `lib/chunker.py`:
```python
"""Sliding-window text chunker for the embedding pipeline.

Targets ~512 tokens per chunk with 128-token overlap. Token count is
approximated as `len(text) / 4` — fastembed's bge-small tokenizer would
give slightly different real counts, but the chunker only needs to stay
under the model's context window (512 tokens for bge-small), and the
4-chars-per-token rule is comfortably conservative for English prose.

Prefers paragraph boundaries (`\\n\\n`) and sentence boundaries (`. `)
when splitting, falling back to a hard cut by character count.
"""
from __future__ import annotations

# Roughly 512 tokens ~= 2048 chars, leaving headroom under the 512-token cap.
_TARGET_CHARS = 1800
# Roughly 128 tokens ~= 512 chars.
_OVERLAP_CHARS = 400


def chunk_text(text: str | None) -> list[str]:
    """Split `text` into chunks of roughly _TARGET_CHARS, with _OVERLAP_CHARS
    of trailing context carried into the next chunk. Returns [] for empty
    input."""
    if not text:
        return []
    if len(text) <= _TARGET_CHARS:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + _TARGET_CHARS, n)
        if end < n:
            # Try to back off to a paragraph break, then to a sentence break.
            window = text[start:end]
            cut = window.rfind("\n\n")
            if cut < _TARGET_CHARS // 2:
                cut = window.rfind(". ")
                if cut >= 0:
                    cut += 1  # keep the period with the chunk
            if cut >= _TARGET_CHARS // 2:
                end = start + cut + (2 if window[cut:cut+2] == "\n\n" else 0)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = max(end - _OVERLAP_CHARS, start + 1)
    return chunks
```

- [ ] **Step 4: PASS**

`DEPGRAPH_DATA_DIR=$(pwd) pytest tests/test_chunker.py -v` → 4 passed.

- [ ] **Step 5: Commit**

```
git add lib/chunker.py tests/test_chunker.py
git commit -m "feat(lib): chunker — paragraph-aware sliding-window text chunker

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: `lib/embeddings.py` — fastembed loader + index I/O

**Files:**
- Create: `lib/embeddings.py`
- Create: `tests/test_embeddings.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_embeddings.py`:
```python
"""Tests for lib.embeddings — the fastembed-driven indexer.

The model is loaded lazily on first call. Tests use the real model (small
enough to be reasonable in CI); first-run download (~140 MB) caches under
~/.cache/huggingface — subsequent runs are fast."""
import json
import numpy as np
from lib.embeddings import (
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
```

- [ ] **Step 2: Verify FAIL**

`DEPGRAPH_DATA_DIR=$(pwd) pytest tests/test_embeddings.py -v`
Expected: ImportError. First-run download will start when implementation lands; allow up to a minute on the first PASS.

- [ ] **Step 3: Implement**

Create `lib/embeddings.py`:
```python
"""fastembed-backed embedding pipeline. Lazy model loader, batch embed,
index reader/writer.

Model: BAAI/bge-small-en-v1.5 — 384-dim, L2-normalized, CPU-friendly.
Storage on disk: fp16 binary matrix + JSONL row metadata side-by-side.

The model loads on first call to `embed_chunks` and is cached at module
level. Subsequent calls reuse it. If fastembed isn't installed or model
load fails, every public function raises EmbeddingUnavailable — callers
(reconcile) catch that and record `embedding_status: "failed"`."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np


VECTOR_DIM = 384  # bge-small-en-v1.5
MODEL_NAME = "BAAI/bge-small-en-v1.5"


class EmbeddingUnavailable(RuntimeError):
    """Raised when fastembed can't load or embed.  reconcile catches this."""


_model = None  # cached TextEmbedding instance


def vector_dim() -> int:
    return VECTOR_DIM


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from fastembed import TextEmbedding  # type: ignore
    except ImportError as e:
        raise EmbeddingUnavailable(f"fastembed not installed: {e}") from e
    try:
        _model = TextEmbedding(model_name=MODEL_NAME)
    except Exception as e:  # model download / init failure
        raise EmbeddingUnavailable(f"could not load {MODEL_NAME}: {e}") from e
    return _model


def embed_chunks(chunks: list[str]) -> np.ndarray:
    """Return a (len(chunks), VECTOR_DIM) fp16 matrix. Empty input returns
    a (0, VECTOR_DIM) array. Raises EmbeddingUnavailable on model failure."""
    if not chunks:
        return np.zeros((0, VECTOR_DIM), dtype=np.float16)
    model = _get_model()
    # fastembed returns a generator of np.ndarray (float32, normalized).
    try:
        vecs = np.array(list(model.embed(chunks)), dtype=np.float32)
    except Exception as e:
        raise EmbeddingUnavailable(f"embed call failed: {e}") from e
    return vecs.astype(np.float16)


def write_index(bin_path: Path, jsonl_path: Path,
                vecs: np.ndarray, rows: list[dict]) -> None:
    """Atomic-rename write. rows[i] describes vecs[i]."""
    assert vecs.dtype == np.float16, "vectors must be fp16"
    assert vecs.shape[1] == VECTOR_DIM, f"vectors must be {VECTOR_DIM}-dim"
    assert len(rows) == vecs.shape[0], "rows / vecs length mismatch"

    bin_tmp = bin_path.with_suffix(bin_path.suffix + ".tmp")
    jsonl_tmp = jsonl_path.with_suffix(jsonl_path.suffix + ".tmp")
    bin_path.parent.mkdir(parents=True, exist_ok=True)

    bin_tmp.write_bytes(vecs.tobytes(order="C"))
    with jsonl_tmp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    bin_tmp.replace(bin_path)
    jsonl_tmp.replace(jsonl_path)


def read_index(bin_path: Path, jsonl_path: Path) -> tuple[list[dict], np.ndarray]:
    """Read both files. Returns ([], (0, VECTOR_DIM) array) if either is missing."""
    if not bin_path.exists() or not jsonl_path.exists():
        return [], np.zeros((0, VECTOR_DIM), dtype=np.float16)
    rows: list[dict] = []
    for line in jsonl_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    raw = bin_path.read_bytes()
    expected_bytes = len(rows) * VECTOR_DIM * 2  # fp16
    if len(raw) != expected_bytes:
        # Mismatch — treat as missing rather than silently misaligned.
        return [], np.zeros((0, VECTOR_DIM), dtype=np.float16)
    vecs = np.frombuffer(raw, dtype=np.float16).reshape(len(rows), VECTOR_DIM)
    return rows, vecs
```

- [ ] **Step 4: PASS**

`DEPGRAPH_DATA_DIR=$(pwd) pytest tests/test_embeddings.py -v` → 4 passed. First run downloads ~140 MB; budget up to a minute.

- [ ] **Step 5: Commit**

```
git add lib/embeddings.py tests/test_embeddings.py
git commit -m "feat(lib): embeddings — fastembed + bge-small + fp16 index I/O

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: depgraph reconcile — embedding pass over dossiers

**Files:**
- Modify: `extractors/reconcile.py` — add `_run_embedding_pass` step + call site
- Create: `tests/test_reconcile_embeddings.py`
- Create: `tests/fixtures/embed_fixture/project.toml`
- Create: `tests/fixtures/embed_fixture/nodes/_meta.json`
- Create: `tests/fixtures/embed_fixture/nodes/models/example_model.json`
- Create: `tests/fixtures/embed_fixture/dossiers/models/example_model.md`

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/embed_fixture/project.toml`:
```toml
[project]
name = "embed-fixture"

[repos.api]
path = "/tmp/embed-fixture-api"
extractor = ["noop"]
```

Create `tests/fixtures/embed_fixture/nodes/_meta.json`:
```json
{"regen_status": "complete", "regen_at": "2026-05-13T10:00:00+00:00", "node_count": 1, "flags": []}
```

Create `tests/fixtures/embed_fixture/nodes/models/example_model.json`:
```json
{
  "schema_version": 1,
  "id": "embed-fixture-api::models/example.py::Example",
  "kind": "model",
  "title": "Example",
  "source": {"repo": "embed-fixture-api", "path": "models/example.py"},
  "signature": {},
  "structural_hash": "h1",
  "extractor": "noop",
  "depends_on": [],
  "dossier": "dossiers/models/example_model.md"
}
```

Create `tests/fixtures/embed_fixture/dossiers/models/example_model.md`:
```markdown
---
status: current
last_reviewed_against_hash: h1
---

# Example model

The Example model represents an entity in the system. It is used to
demonstrate the embedding pipeline against a realistic dossier shape —
free-form prose that the chunker will see end-to-end.

## Why it exists

Because the embedding test needs at least one dossier with prose long
enough to be interesting but short enough to fit in one chunk.
```

- [ ] **Step 2: Write the failing integration test**

Create `tests/test_reconcile_embeddings.py`:
```python
"""Integration test: depgraph reconcile builds the embedding index for
every dossier body in the corpus."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

FIXTURE = Path(__file__).parent / "fixtures" / "embed_fixture"


def _setup_work(tmp_path):
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)
    # detect_orphans needs the repo dir to exist + the source file to exist
    # (matches the test_reconcile_route_calls pattern from Plan 4).
    api_root = tmp_path / "embed-fixture-api"
    (api_root / "models").mkdir(parents=True)
    (api_root / "models" / "example.py").touch()
    cfg_path = work / "project.toml"
    txt = cfg_path.read_text().replace("/tmp/embed-fixture-api", str(api_root))
    cfg_path.write_text(txt)
    return work


def test_reconcile_writes_embedding_index(tmp_path):
    work = _setup_work(tmp_path)
    repo_root = Path(__file__).resolve().parent.parent

    result = subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        capture_output=True, text=True, timeout=120,  # first-run model download
    )
    assert result.returncode == 0, f"reconcile failed: {result.stderr}"

    bin_path = work / "nodes" / "_index" / "embeddings.bin"
    jsonl_path = work / "nodes" / "_index" / "embeddings.jsonl"
    assert bin_path.exists()
    assert jsonl_path.exists()

    rows = [json.loads(l) for l in jsonl_path.read_text().splitlines() if l.strip()]
    assert len(rows) >= 1
    # Every row maps to our one fixture node.
    assert all(r["node_id"] == "embed-fixture-api::models/example.py::Example" for r in rows)
    # Each row has the expected metadata.
    r0 = rows[0]
    assert set(r0.keys()) >= {"row", "node_id", "chunk_index", "content_hash",
                              "text_preview", "source_field"}
    assert r0["source_field"] == "dossier_body"
    assert r0["content_hash"].startswith("sha256:")

    # Vectors are fp16, 384-dim, count matches rows.
    raw = bin_path.read_bytes()
    expected_bytes = len(rows) * 384 * 2
    assert len(raw) == expected_bytes, f"bin size {len(raw)} != expected {expected_bytes}"

    # _meta.json gets an embedding_status field.
    meta = json.loads((work / "nodes" / "_meta.json").read_text())
    assert meta.get("embedding_status") == "ok"


def test_reconcile_skips_unchanged_dossier(tmp_path):
    """Second reconcile run with no changes should be a no-op for embeddings."""
    work = _setup_work(tmp_path)
    repo_root = Path(__file__).resolve().parent.parent

    # First run
    subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        check=True, timeout=120, capture_output=True,
    )
    bin_path = work / "nodes" / "_index" / "embeddings.bin"
    first_mtime = bin_path.stat().st_mtime
    first_bytes = bin_path.read_bytes()

    # Second run — no source change
    subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        check=True, timeout=120, capture_output=True,
    )
    # The bin can be rewritten (deterministic content), but the bytes match.
    assert bin_path.read_bytes() == first_bytes
```

- [ ] **Step 3: Verify FAIL**

`pytest tests/test_reconcile_embeddings.py -v`
Expected: the index files don't exist (reconcile doesn't yet run an embedding pass).

- [ ] **Step 4: Implement the embedding pass**

In `extractors/reconcile.py`, after the section that builds `by_target` and writes `dependents.json` (so the dep-index work is complete first — block-only failure semantics), add:

```python
# Imports at top of file:
import hashlib
from pathlib import Path

# Embedding lib lives one level up in lib/.
try:
    from lib.chunker import chunk_text
    from lib.embeddings import (
        EmbeddingUnavailable, embed_chunks, read_index, write_index,
    )
    _EMBEDDING_AVAILABLE = True
except ImportError:
    _EMBEDDING_AVAILABLE = False


def _dossier_text(node: dict, data_dir: Path) -> str | None:
    """Read the dossier body for a node. Returns the markdown content past
    the YAML frontmatter, or None if no dossier."""
    rel = node.get("dossier")
    if not rel:
        return None
    full = data_dir / rel
    if not full.exists():
        return None
    text = full.read_text()
    # Strip frontmatter (between leading "---\n" lines).
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text = text[end + 5:]
    return text.strip() or None


def _chunk_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_embedding_pass(nodes: list[dict], data_dir: Path) -> str:
    """Build the embedding index. Returns "ok" / "failed" / "skipped".
    Block-only failure — never raises out of reconcile."""
    if not _EMBEDDING_AVAILABLE:
        return "skipped"

    index_dir = data_dir / "nodes" / "_index"
    bin_path = index_dir / "embeddings.bin"
    jsonl_path = index_dir / "embeddings.jsonl"
    prior_rows, prior_vecs = read_index(bin_path, jsonl_path)
    prior_by_hash = {r["content_hash"]: (r, prior_vecs[r["row"]])
                     for r in prior_rows if "content_hash" in r}

    new_rows: list[dict] = []
    new_chunks_to_embed: list[str] = []
    new_chunks_meta: list[dict] = []  # parallel array — index into new_rows

    for n in nodes:
        body = _dossier_text(n, data_dir)
        if not body:
            continue
        chunks = chunk_text(body)
        for i, ch in enumerate(chunks):
            h = _chunk_hash(ch)
            meta = {
                "node_id": n.get("id"),
                "chunk_index": i,
                "content_hash": h,
                "text_preview": ch[:120].replace("\n", " "),
                "source_field": "dossier_body",
            }
            new_rows.append(meta)
            if h in prior_by_hash:
                pass  # will reuse prior vec
            else:
                new_chunks_to_embed.append(ch)
                new_chunks_meta.append(meta)

    # Embed only the chunks that weren't in the prior index.
    try:
        new_vecs = embed_chunks(new_chunks_to_embed)
    except EmbeddingUnavailable:
        return "failed"

    # Assemble the final vec matrix in row order.
    import numpy as np
    vecs = np.zeros((len(new_rows), 384), dtype=np.float16)
    new_idx = 0
    for i, meta in enumerate(new_rows):
        meta["row"] = i
        h = meta["content_hash"]
        if h in prior_by_hash:
            vecs[i] = prior_by_hash[h][1]
        else:
            vecs[i] = new_vecs[new_idx]
            new_idx += 1

    write_index(bin_path, jsonl_path, vecs, new_rows)
    return "ok"
```

Then at the END of `main()` in reconcile (after `write_dependents_index` succeeds), add:

```python
    # Embedding pass — block-only failure semantics. The dep-index work above
    # is already on disk; this either succeeds, fails, or is skipped.
    embedding_status = _run_embedding_pass(list(nodes.values()), data_dir)  # adapt to nodes' actual shape
    # Write status to _meta.json.
    meta_path = data_dir / "nodes" / "_meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except (OSError, json.JSONDecodeError):
            meta = {}
        meta["embedding_status"] = embedding_status
        meta_path.write_text(json.dumps(meta, indent=2))
```

(Adapt the `nodes` reference to whatever variable reconcile's `main()` has it bound to — likely `list(nodes_by_id.values())` or similar. Look at the prior route-call join wiring for the pattern.)

- [ ] **Step 5: PASS**

`pytest tests/test_reconcile_embeddings.py -v` → 2 passed. First run downloads the model (~140 MB) and takes 30-60s.

- [ ] **Step 6: Full suite — no regressions**

`pytest tests/ -v` — all prior tests still pass.

- [ ] **Step 7: Commit**

```
git add extractors/reconcile.py tests/test_reconcile_embeddings.py tests/fixtures/embed_fixture/
git commit -m "feat(reconcile): embedding pass over dossier bodies

Runs after the dep-index pass. Incremental by SHA-256 of each chunk's
text — unchanged chunks carry forward without re-embedding. Failure
in the embedding step doesn't fail reconcile; it writes
embedding_status to _meta.json and exits cleanly.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: logigraph reconcile — embedding pass over rules / domain / processes

**Files:**
- Modify (in logigraph repo): `extractors/reconcile.py`
- Create (in logigraph repo): `tests/test_reconcile_embeddings.py`
- Create (in logigraph repo): `tests/fixtures/embed_fixture_logigraph/`

Working dir for this task: `~/tools/knowledge-graph/logigraph`

- [ ] **Step 1: Confirm logigraph imports from depgraph's lib**

```bash
grep -n "from lib\|sys.path.*depgraph" ~/tools/knowledge-graph/logigraph/extractors/reconcile.py | head
```

Logigraph already adds depgraph's repo to sys.path (per the framework convention). If it doesn't, add at the top of the file:

```python
import sys
from pathlib import Path
_LOGIGRAPH_ROOT = Path(__file__).resolve().parent.parent
_DEPGRAPH_ROOT = _LOGIGRAPH_ROOT.parent / "depgraph"
if str(_DEPGRAPH_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_ROOT))
```

- [ ] **Step 2: Fixture setup**

Create `tests/fixtures/embed_fixture_logigraph/project.toml`:
```toml
[project]
name = "embed-fixture-lg"

[depgraph]
data_dir = "/tmp/embed-fixture-depgraph"
```

Create `tests/fixtures/embed_fixture_logigraph/nodes/_meta.json`:
```json
{"regen_status": "complete", "regen_at": "2026-05-13T10:00:00+00:00", "node_count": 3, "flags": []}
```

Create `tests/fixtures/embed_fixture_logigraph/nodes/rules/rule__example__test.json`:
```json
{
  "schema_version": 1,
  "id": "rule::example::test",
  "kind": "rule",
  "title": "Example rule",
  "statement": "An example rule statement long enough to embed meaningfully and to round-trip through chunking + indexing without losing the structural shape.",
  "claims_code": [],
  "references_domain": [],
  "structural_hash": "rh1",
  "definition_status": "human_reviewed"
}
```

Create `tests/fixtures/embed_fixture_logigraph/nodes/domain/resource__example__entity.json`:
```json
{
  "schema_version": 1,
  "id": "resource::example::entity",
  "kind": "domain",
  "subkind": "resource",
  "title": "Example entity",
  "summary": "An example resource describing a kind of thing in the system. Used for testing the embedding pipeline against the domain corpus.",
  "structural_hash": "dh1",
  "definition_status": "human_reviewed"
}
```

Create `tests/fixtures/embed_fixture_logigraph/nodes/processes/process__example__flow.json`:
```json
{
  "schema_version": 1,
  "id": "process::example::flow",
  "kind": "process",
  "title": "Example flow",
  "flow": {"action": "user opens example"},
  "steps": [
    {"description": "User does the first step — example prose for the embedding pipeline to chew on.", "claims_code": []},
    {"description": "Then the second step happens, with enough detail to make it a real embedding target.", "claims_code": []}
  ],
  "structural_hash": "ph1",
  "definition_status": "human_reviewed"
}
```

- [ ] **Step 3: Write the failing test**

Create `tests/test_reconcile_embeddings.py`:
```python
"""Integration test: logigraph reconcile embeds rule statements, domain
summaries, and process step descriptions."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "embed_fixture_logigraph"


def _setup_work(tmp_path):
    work = tmp_path / "logigraph"
    shutil.copytree(FIXTURE, work)
    return work


def test_reconcile_embeds_rule_domain_process(tmp_path):
    work = _setup_work(tmp_path)
    repo_root = Path(__file__).resolve().parent.parent  # logigraph repo root

    result = subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"reconcile failed: {result.stderr}"

    jsonl_path = work / "nodes" / "_index" / "embeddings.jsonl"
    assert jsonl_path.exists()
    rows = [json.loads(l) for l in jsonl_path.read_text().splitlines() if l.strip()]

    # Expect at least: 1 rule statement + 1 domain summary + 2 process steps = 4 rows.
    fields = {r["source_field"] for r in rows}
    assert "rule_statement" in fields
    assert "domain_summary" in fields
    assert "process_step" in fields
    # Each row has the standard metadata keys.
    for r in rows:
        assert set(r.keys()) >= {"row", "node_id", "chunk_index",
                                 "content_hash", "text_preview", "source_field"}

    meta = json.loads((work / "nodes" / "_meta.json").read_text())
    assert meta.get("embedding_status") == "ok"
```

- [ ] **Step 4: Verify FAIL**

```bash
cd ~/tools/knowledge-graph/logigraph
pytest tests/test_reconcile_embeddings.py -v
```

- [ ] **Step 5: Implement in logigraph reconcile**

In `~/tools/knowledge-graph/logigraph/extractors/reconcile.py`, add the same imports + a helper that visits the three text sources, then call `_run_embedding_pass`:

```python
# Imports at the top of the file (after the sys.path hack to depgraph):
import hashlib

try:
    from lib.chunker import chunk_text
    from lib.embeddings import (
        EmbeddingUnavailable, embed_chunks, read_index, write_index,
    )
    _EMBEDDING_AVAILABLE = True
except ImportError:
    _EMBEDDING_AVAILABLE = False


def _chunk_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text_sources_for_node(node: dict) -> list[tuple[str, str]]:
    """Return [(source_field, text), ...] for the prose sources on a node."""
    out: list[tuple[str, str]] = []
    kind = node.get("kind")
    if kind == "rule":
        s = (node.get("statement") or "").strip()
        if s:
            out.append(("rule_statement", s))
    elif kind == "domain":
        s = (node.get("summary") or "").strip()
        if s:
            out.append(("domain_summary", s))
    elif kind == "process":
        for step in node.get("steps") or []:
            d = (step.get("description") or "").strip()
            if d:
                out.append(("process_step", d))
    return out


def _run_embedding_pass(nodes: list[dict], data_dir) -> str:
    if not _EMBEDDING_AVAILABLE:
        return "skipped"
    import numpy as np
    index_dir = data_dir / "nodes" / "_index"
    bin_path = index_dir / "embeddings.bin"
    jsonl_path = index_dir / "embeddings.jsonl"
    prior_rows, prior_vecs = read_index(bin_path, jsonl_path)
    prior_by_hash = {r["content_hash"]: (r, prior_vecs[r["row"]])
                     for r in prior_rows if "content_hash" in r}

    new_rows: list[dict] = []
    new_chunks_to_embed: list[str] = []

    for n in nodes:
        for source_field, text in _text_sources_for_node(n):
            chunks = chunk_text(text)
            for i, ch in enumerate(chunks):
                h = _chunk_hash(ch)
                meta = {
                    "node_id": n.get("id"),
                    "chunk_index": i,
                    "content_hash": h,
                    "text_preview": ch[:120].replace("\n", " "),
                    "source_field": source_field,
                }
                new_rows.append(meta)
                if h not in prior_by_hash:
                    new_chunks_to_embed.append(ch)

    try:
        new_vecs = embed_chunks(new_chunks_to_embed)
    except EmbeddingUnavailable:
        return "failed"

    vecs = np.zeros((len(new_rows), 384), dtype=np.float16)
    new_idx = 0
    for i, meta in enumerate(new_rows):
        meta["row"] = i
        h = meta["content_hash"]
        if h in prior_by_hash:
            vecs[i] = prior_by_hash[h][1]
        else:
            vecs[i] = new_vecs[new_idx]
            new_idx += 1

    write_index(bin_path, jsonl_path, vecs, new_rows)
    return "ok"
```

Then at the end of logigraph reconcile's `main()`, add the same call + `_meta.json` status write as in Task 4 step 4.

- [ ] **Step 6: PASS**

`pytest tests/test_reconcile_embeddings.py -v` → 1 passed.

- [ ] **Step 7: Full suite**

`pytest tests/ -v` — no regressions.

- [ ] **Step 8: Commit (in logigraph)**

```
cd ~/tools/knowledge-graph/logigraph
git add extractors/reconcile.py tests/test_reconcile_embeddings.py tests/fixtures/embed_fixture_logigraph/
git commit -m "feat(reconcile): embedding pass over rule/domain/process prose

Embeds rule.statement, domain.summary, and each process step description.
Imports lib.chunker + lib.embeddings from sibling depgraph repo.
Block-only failure semantics: status to _meta.json, never raises.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Failure-mode test — embedding step blocks but reconcile continues

**Files:**
- Modify (in depgraph): `tests/test_reconcile_embeddings.py` — append a test

- [ ] **Step 1: Append the test**

Add to `~/tools/knowledge-graph/depgraph/tests/test_reconcile_embeddings.py`:
```python
def test_reconcile_records_failed_status_when_embed_raises(tmp_path, monkeypatch):
    """If embed_chunks raises EmbeddingUnavailable, reconcile still produces
    the dependency index but records embedding_status: 'failed' on _meta.json."""
    work = _setup_work(tmp_path)
    repo_root = Path(__file__).resolve().parent.parent

    # Inject a poison fastembed shim that raises on import OR on embed.
    # We do this by writing a sitecustomize stub into a parallel install dir
    # and pointing PYTHONPATH at it.
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    (shim_dir / "fastembed.py").write_text(
        "raise ImportError('shim: fastembed disabled for this test')\n"
    )
    env = {**__import__("os").environ, "PYTHONPATH": str(shim_dir)}

    result = subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        capture_output=True, text=True, timeout=20, env=env,
    )
    assert result.returncode == 0, f"reconcile should not fail: {result.stderr}"

    # Dep-index work still happened.
    assert (work / "nodes" / "_index" / "dependents.json").exists()
    # Embedding index is NOT written (or is empty).
    bin_path = work / "nodes" / "_index" / "embeddings.bin"
    jsonl_path = work / "nodes" / "_index" / "embeddings.jsonl"
    if jsonl_path.exists():
        rows = [json.loads(l) for l in jsonl_path.read_text().splitlines() if l.strip()]
        assert rows == [], "embedding rows should be empty when fastembed is unavailable"

    meta = json.loads((work / "nodes" / "_meta.json").read_text())
    assert meta.get("embedding_status") in ("failed", "skipped"), \
        f"expected failed/skipped, got {meta.get('embedding_status')}"
```

- [ ] **Step 2: Run**

`pytest tests/test_reconcile_embeddings.py::test_reconcile_records_failed_status_when_embed_raises -v` → 1 passed.

- [ ] **Step 3: Commit**

```
git add tests/test_reconcile_embeddings.py
git commit -m "test(reconcile): failure-mode — embed unavailable doesn't fail regen

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Real-corpus smoke test — run against Concorda

**Files:** (none modified in framework or graphui; touches Concorda's data dir during regen)

- [ ] **Step 1: Run depgraph regen against the real corpus**

```bash
cd ~/concorda
DEPGRAPH_DATA_DIR=$HOME/concorda/knowledge-graph/depgraph \
  $HOME/tools/knowledge-graph/depgraph/bin/depgraph regen 2>&1 | tail -20
```

Watch the output. Expect:
- The dep-index work to complete as before
- An additional ~30-60s of embedding time on first run (model download + ~1.5k embeddings)
- `nodes/_index/embeddings.bin` + `nodes/_index/embeddings.jsonl` to appear
- `_meta.json::embedding_status` to be `"ok"`

- [ ] **Step 2: Run logigraph regen against the real corpus**

```bash
cd ~/concorda
LOGIGRAPH_DATA_DIR=$HOME/concorda/knowledge-graph/logigraph \
DEPGRAPH_DATA_DIR=$HOME/concorda/knowledge-graph/depgraph \
  $HOME/tools/knowledge-graph/logigraph/bin/logigraph regen 2>&1 | tail -20
```

Expect ~5s of embedding time (only ~50 logigraph nodes). `_index/embeddings.bin` appears under the logigraph data dir.

- [ ] **Step 3: Sanity-check the index files**

```bash
python3 -c "
import json, pathlib, numpy as np
for label in ('depgraph', 'logigraph'):
    base = pathlib.Path.home() / 'concorda' / 'knowledge-graph' / label / 'nodes' / '_index'
    bin_p = base / 'embeddings.bin'
    js_p = base / 'embeddings.jsonl'
    if not bin_p.exists():
        print(f'{label}: no embeddings.bin')
        continue
    rows = [json.loads(l) for l in js_p.read_text().splitlines() if l.strip()]
    raw = bin_p.read_bytes()
    print(f'{label}: {len(rows)} rows, bin size {len(raw)} bytes, '
          f'first preview: {rows[0][\"text_preview\"][:60]!r}')
"
```

Expected: depgraph reports ~1500-2500 rows; logigraph reports ~50-150 rows.

- [ ] **Step 4: Run regen a second time and verify incremental behavior**

```bash
time DEPGRAPH_DATA_DIR=$HOME/concorda/knowledge-graph/depgraph \
  $HOME/tools/knowledge-graph/depgraph/bin/depgraph regen 2>&1 | tail -5
```

Second run should be noticeably faster — all chunks are unchanged, so no re-embedding happens.

- [ ] **Step 5: If anything looks wrong, fix it in its own commit**

Common issues:
- The first run hangs on the model download — fastembed downloads from HuggingFace; check network. If on a private box, may need to set `HF_HOME=~/.cache/huggingface` explicitly.
- Some nodes don't have dossiers — that's expected; only nodes with dossier prose get embedded.
- `_meta.json` shape changed — if reconcile rewrites it minus `node_count` or `flags`, that's a bug in the meta-write step. Preserve existing keys.

- [ ] **Step 6: If the corpus is git-tracked, commit the regen artifacts in ~/concorda**

```bash
cd ~/concorda
git status knowledge-graph/depgraph/nodes/_index/ knowledge-graph/logigraph/nodes/_index/
# If those paths show up modified, commit:
git add knowledge-graph/{depgraph,logigraph}/nodes/_index/embeddings.{bin,jsonl}
git add knowledge-graph/{depgraph,logigraph}/nodes/_meta.json
git commit -m "chore(graph): first embedding index generation"
```

(If the index dirs are in `.gitignore`, skip this step.)

---

## Self-Review Checklist

1. **Spec coverage** (graphui categories spec § 5 "Embedding pipeline"):
   - ✓ Triggered by depgraph + logigraph regen — Tasks 4, 5
   - ✓ Embeds dossier body / rule.statement / domain.summary / process step.description — Tasks 4, 5
   - ✓ Incremental by content hash — Tasks 4, 5
   - ✓ fp16 storage — Task 3
   - ✓ Sidecar JSONL mapping — Task 3
   - ✓ ~/_index/embeddings.{bin,jsonl} per data dir — Tasks 4, 5
   - ✗ "Server-side retrieval in the FastAPI app: load both files into memory on app start; cosine search is brute-force at this corpus size (< 10k chunks). Re-load on file mtime change." — that's Plan F (graphui), not this plan.

2. **Placeholder scan:** no TBD / TODO. Every step has concrete code or a concrete command.

3. **Type consistency:**
   - `vector_dim()` returns 384 everywhere (`VECTOR_DIM` constant) — Task 3.
   - `read_index` / `write_index` exchange `(rows: list[dict], vecs: np.ndarray)` — same shape on both sides.
   - `EmbeddingUnavailable` raised by `embed_chunks` is caught by `_run_embedding_pass` in both reconcile.py files — same exception type imported from the same `lib.embeddings`.
   - `source_field` values (`"dossier_body"`, `"rule_statement"`, `"domain_summary"`, `"process_step"`) are used identically in Tasks 4, 5 and asserted in tests.

---

## Execution Handoff

Plan complete and saved to `~/tools/knowledge-graph/depgraph/docs/superpowers/plans/2026-05-13-embedding-pipeline.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review, fast iteration.
**2. Inline Execution** — execute here with checkpoints.

Which approach?
