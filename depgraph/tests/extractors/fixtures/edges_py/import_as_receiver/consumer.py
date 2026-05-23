"""`import pkg; pkg.do_thing()` — the receiver name `pkg` is in the
imports table (bound to the in-corpus package module id), but NOT in
`var_types`. Before #91 (b2), `_resolve_call_edge` only consulted
`var_types`, so this call leaked to `external::unresolved::pkg.do_thing`.
The fix adds an imports-table fallback that resolves the attribute to
the top-level symbol (or re-exported name) of the imported module."""
from __future__ import annotations

import pkg


def caller():
    # Directly-defined symbol in pkg/__init__.py.
    pkg.do_thing()
    # Re-exported symbol (`from .utils import echo as echo`). Must also
    # resolve — the b2 fix indexes both directly-defined names AND
    # re-exported names in `symbols_by_module`.
    pkg.echo("hi")
