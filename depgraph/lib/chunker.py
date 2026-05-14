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
