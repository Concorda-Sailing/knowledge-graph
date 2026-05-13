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

import numpy as np


VECTOR_DIM = 384  # bge-small-en-v1.5
MODEL_NAME = "BAAI/bge-small-en-v1.5"


class EmbeddingUnavailable(RuntimeError):
    """Raised when fastembed can't load or embed. reconcile catches this."""


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
        # threads=1 caps ONNX intra-op parallelism. Without this, the runtime
        # allocates per-core working buffers and RSS spikes 4-5x on a 4-core
        # host — enough to OOM-kill the process even when free memory looks
        # sufficient. Single-threaded is still fast enough for batch regen
        # (2400 chunks in ~30s on this hardware).
        _model = TextEmbedding(model_name=MODEL_NAME, threads=1)
    except Exception as e:  # model download / init failure
        raise EmbeddingUnavailable(f"could not load {MODEL_NAME}: {e}") from e
    return _model


_EMBED_BATCH_SIZE = 64  # chunks per ONNX call; bounds peak RSS on memory-constrained hosts


def embed_chunks(chunks: list[str]) -> np.ndarray:
    """Return a (len(chunks), VECTOR_DIM) fp16 matrix. Empty input returns
    a (0, VECTOR_DIM) array. Raises EmbeddingUnavailable on model failure.

    Processes chunks in batches of _EMBED_BATCH_SIZE to cap peak RSS.
    Without batching, a 2400-chunk corpus on long dossier text can push
    onnxruntime past 5 GB and trigger OOM on a memory-constrained host."""
    if not chunks:
        return np.zeros((0, VECTOR_DIM), dtype=np.float16)
    model = _get_model()
    try:
        result_batches: list[np.ndarray] = []
        for i in range(0, len(chunks), _EMBED_BATCH_SIZE):
            batch = chunks[i:i + _EMBED_BATCH_SIZE]
            # fastembed returns a generator of np.ndarray (float32, normalized).
            batch_vecs = np.array(list(model.embed(batch)), dtype=np.float32)
            result_batches.append(batch_vecs.astype(np.float16))
        return np.concatenate(result_batches, axis=0) if result_batches else np.zeros((0, VECTOR_DIM), dtype=np.float16)
    except Exception as e:
        raise EmbeddingUnavailable(f"embed call failed: {e}") from e


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
    expected_bytes = len(rows) * VECTOR_DIM * 2  # fp16 = 2 bytes/elem
    if len(raw) != expected_bytes:
        # Mismatch — treat as missing rather than silently misaligned.
        return [], np.zeros((0, VECTOR_DIM), dtype=np.float16)
    # .copy() because np.frombuffer returns a read-only view tied to the
    # bytes object; downstream callers (Plan F search path) cast to float32
    # in place, which would fail on a read-only array.
    vecs = np.frombuffer(raw, dtype=np.float16).reshape(len(rows), VECTOR_DIM).copy()
    return rows, vecs
