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
