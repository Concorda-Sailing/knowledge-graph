"""Sibling consumer of the registered package. `import widget` here MUST
resolve to the in-corpus `src/widget/__init__.py` module — the
cross-binding aliasing in `_attach_imports_edges` reads pyproject.toml's
`[project].name`, finds the in-corpus module whose dotted name ends with
`.widget` AND lives in an `__init__.py`, and aliases the bare name."""
from __future__ import annotations

import widget


def demo():
    return widget.render()
