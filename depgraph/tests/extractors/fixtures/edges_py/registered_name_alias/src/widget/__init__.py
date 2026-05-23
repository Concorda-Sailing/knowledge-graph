"""In-corpus package whose registered import name is `widget` but whose
on-disk path is `src/widget/__init__.py` (canonical src-layout). The
module index would record the dotted name `src.widget`; without the
cross-binding alias, `import widget` from a sibling subtree (examples/,
tests/, etc.) would fall back to `external::pypi::widget` even though
the package is in-corpus."""
from __future__ import annotations


def render() -> str:
    return "rendered"
