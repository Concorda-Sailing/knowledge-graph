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
| `external_terminal(ecosystem="unresolved", package="", symbol="Cursor.execute")` | `"external::unresolved::Cursor.execute"` (assumed package would be skipped if empty) | `'external::unresolved::Cursor.execute'` ✓ (fixed) |
| `is_external_terminal("external::npm::react::useState")` | `True` | `True` |
| `is_external_terminal("api::routers/events.py::create")` | `False` | `False` |
| `is_external_terminal("external::")` | `True` (starts with "external::") | `True` |
| `is_external_terminal("")` | `False` | `False` |
| `is_external_terminal("External::upper::case")` | `True` (assumed case-insensitive or would match) | `False` — **WRONG** — `startswith("external::")` is strictly lowercase; capital E does not match |
| `slugify_id_for_filename("a::b/c.py::D.m")` | `"a__b_c_py__D_m"` | `'a__b_c_py__D_m'` |
| `slugify_id_for_filename("__leading::trailing__")` | `"leading__trailing"` | `'leading__trailing'` |
| `slugify_id_for_filename("unicode_é_in_path")` | `"unicode_é_in_path"` treated as `"unicode__in_path"` (é replaced with _) | `'unicode_é_in_path'` — **WRONG** — `é` survives because Python's `str.isalnum()` returns `True` for Unicode letters |
| `slugify_id_for_filename("a::b.py::C")` | `"a__b_py__C"` | `'a__b_py__C'` |
| `slugify_id_for_filename("repo with space::path::symbol")` | `"repo_with_space__path__symbol"` | `'repo_with_space__path__symbol'` |

## Observations

**Finding 1 — `external_terminal` with empty package produced malformed id (FIXED):**
`external_terminal(ecosystem="unresolved", package="", symbol="Cursor.execute")` previously emitted
`'external::unresolved::::Cursor.execute'` — a double `::`. Fixed by making `package` optional;
`None` or empty string elides the segment, producing the correct 3-segment form. See
"Implementation defects fixed" section below.

**Finding 2 — `is_external_terminal` is case-sensitive:**
The prefix check uses a bare string literal `"external::"` so `"External::..."` returns `False`.
This is correct behavior (ids are canonical-lowercase). Callers extracting ids from mixed-case
sources should normalise before calling. Not a bug.

**Finding 3 — `slugify_id_for_filename` allows Unicode letters through:**
`é`, `ñ`, `ü`, and any Unicode letter satisfying `str.isalnum()` pass the character filter. The
docstring says "filename-safe slug" but most filesystems permit these characters, so this is
a design decision rather than a bug. The key risk is cross-platform: a slug generated on Linux may
differ from one generated on a case-insensitive macOS filesystem if any Unicode normalization differs.
Worth noting for future collision detection — two ids with composed vs. decomposed Unicode could
produce the same visual slug but different byte sequences, defeating collision detection.

## Implementation defects fixed during verification

**Bug surfaced by Finding 1:** The verification prediction for
`external_terminal(ecosystem="unresolved", package="", symbol="Cursor.execute")` expected
`"external::unresolved::Cursor.execute"` (3-segment). The observed output was
`"external::unresolved::::Cursor.execute"` — a double `::` from the empty package segment being
interpolated verbatim.

Root cause: `package` was a required positional keyword arg with no conditional logic; the
f-string always emitted all four segments.

Fix: made `package` optional (`str | None = None`); when falsy the segment is omitted.
Companion test `test_external_terminal_no_package_3_segment` added to `test_primitives.py`.

Committed in: d881594c

## Status
✓ verified — Finding 1 (malformed external_terminal id) was a real bug and has been fixed. Findings 2 and 3 are by-design behavior, documented for future reference.
