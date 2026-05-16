# Verification log: canonical helpers

**Last reviewed:** 2026-05-16 by Claude (haiku subagent under Opus controller)
**Components:** canonical_id, external_terminal, is_external_terminal, slugify_id_for_filename
**Source:** depgraph/lib/primitives.py

## Inputs exercised

For each input below, the "Predicted" column was filled in BEFORE running.
Discrepancies between Predicted and Observed (if any) are noted at the bottom.

| Input | Predicted | Observed |
|---|---|---|
| `canonical_id("a", "b.py", "C")` | `"a::b.py::C"` | `'a::b.py::C'` |
| `canonical_id("a", "b.py", "C.m")` | `"a::b.py::C.m"` | `'a::b.py::C.m'` |
| `canonical_id("repo with space", "b.py", "C")` | `"repo with space::b.py::C"` (spaces preserved in id, not slug) | `'repo with space::b.py::C'` |
| `canonical_id("", "", "")` | `"::::"` (empty strings produce bare separators) | `'::::'` |
| `canonical_id("a", "path/to/module.py", "MyClass")` | `"a::path/to/module.py::MyClass"` | `'a::path/to/module.py::MyClass'` |
| `external_terminal(ecosystem="pypi", package="sqlalchemy", symbol="Base")` | `"external::pypi::sqlalchemy::Base"` | `'external::pypi::sqlalchemy::Base'` |
| `external_terminal(ecosystem="npm", package="react", symbol="useState")` | `"external::npm::react::useState"` | `'external::npm::react::useState'` |
| `external_terminal(ecosystem="unresolved", package="", symbol="Cursor.execute")` | `"external::unresolved::Cursor.execute"` (assumed package would be skipped if empty) | `'external::unresolved::::Cursor.execute'` — **WRONG** — double `::` from empty package segment |
| `is_external_terminal("external::npm::react::useState")` | `True` | `True` |
| `is_external_terminal("concorda-api::routers/events.py::create")` | `False` | `False` |
| `is_external_terminal("external::")` | `True` (starts with "external::") | `True` |
| `is_external_terminal("")` | `False` | `False` |
| `is_external_terminal("External::upper::case")` | `True` (assumed case-insensitive or would match) | `False` — **WRONG** — `startswith("external::")` is strictly lowercase; capital E does not match |
| `slugify_id_for_filename("a::b/c.py::D.m")` | `"a__b_c_py__D_m"` | `'a__b_c_py__D_m'` |
| `slugify_id_for_filename("__leading::trailing__")` | `"leading__trailing"` | `'leading__trailing'` |
| `slugify_id_for_filename("unicode_é_in_path")` | `"unicode_é_in_path"` treated as `"unicode__in_path"` (é replaced with _) | `'unicode_é_in_path'` — **WRONG** — `é` survives because Python's `str.isalnum()` returns `True` for Unicode letters |
| `slugify_id_for_filename("a::b.py::C")` | `"a__b_py__C"` | `'a__b_py__C'` |
| `slugify_id_for_filename("repo with space::path::symbol")` | `"repo_with_space__path__symbol"` | `'repo_with_space__path__symbol'` |

## Observations

**Finding 1 — `external_terminal` with empty package produces malformed id:**
`external_terminal(ecosystem="unresolved", package="", symbol="Cursor.execute")` emits
`'external::unresolved::::Cursor.execute'` — a double `::`. This is valid Python (f-string just
concatenates) but the resulting id is not parseable by any splitter that expects exactly three
`::` separators after `external`. The docstring example shows `external::python-dbapi::Cursor.execute`
which omits the package segment. The function signature requires all three keyword args; callers
who want the two-segment form have no way to call it correctly. Either the signature should allow
`package=""` and collapse the empty segment, or the docstring example is misleading. Flagging as
a latent bug — not a crash, but produces an id that won't round-trip cleanly.

**Finding 2 — `is_external_terminal` is case-sensitive:**
The prefix check uses a bare string literal `"external::"` so `"External::..."` returns `False`.
This is probably correct behavior (ids are canonical-lowercase), but callers extracting ids from
mixed-case sources would silently miss these. Not a bug in isolation — worth documenting.

**Finding 3 — `slugify_id_for_filename` allows Unicode letters through:**
`é`, `ñ`, `ü`, and any Unicode letter satisfying `str.isalnum()` pass the character filter. The
docstring says "filename-safe slug" but most filesystems permit these characters, so this is
a design decision rather than a bug. The key risk is cross-platform: a slug generated on Linux may
differ from one generated on a case-insensitive macOS filesystem if any Unicode normalization differs.
Worth noting for future collision detection — two ids with composed vs. decomposed Unicode could
produce the same visual slug but different byte sequences, defeating collision detection.

## Status
✓ verified — 3 predictions were wrong (documented above); none are crashes but Finding 1 is a latent design defect worth tracking.
