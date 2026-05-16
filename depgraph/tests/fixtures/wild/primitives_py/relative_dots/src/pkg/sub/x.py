"""Module using multi-level relative imports — the import statements themselves
are not extracted in Phase 2 (no edges yet). Only the module primitive and
the variable it defines are emitted."""

# 2-level relative: goes up to src/pkg, then into sub
from ..sub import SUB_VERSION as _sub  # noqa: F401

# 3-level relative: goes up to src/, then into pkg.sub
# (would resolve to this same package — kept for syntactic stress)
from ...pkg.sub import SUB_VERSION as _sub2  # noqa: F401


EXPORT_KEY: str = "relative_dots.x"


def load() -> str:
    """Public function in the deepest sub-module."""
    return EXPORT_KEY
