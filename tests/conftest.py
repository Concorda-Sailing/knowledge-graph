"""Root test conftest.

Ensures the framework root is on sys.path so tests can import
`depgraph.lib.X` and `logigraph.lib.X` directly.

Before the lib-namespace rename, this file contained a sys.modules
eviction hack to work around the `lib` package collision between
depgraph/lib/ and logigraph/lib/. That's gone now — fully-qualified
imports make the namespaces distinct.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent.parent
if str(_TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOL_ROOT))
