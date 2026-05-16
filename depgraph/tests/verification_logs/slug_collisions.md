# Verification log: slug collisions

**Last reviewed:** 2026-05-16 by Claude (haiku subagent under Opus controller)
**Components:** check_slug_collisions
**Source:** depgraph/lib/primitives.py

## Inputs exercised

For each input below, the "Predicted" column was filled in BEFORE running.
Discrepancies between Predicted and Observed (if any) are noted at the bottom.

| Input | Predicted | Observed |
|---|---|---|
| `check_slug_collisions([])` | `[]` | `[]` |
| `check_slug_collisions([{"id": "r::a.b::x"}, {"id": "r::a-b::x"}])` — both slugify to `r__a_b__x` | one collision string mentioning both ids | `["slug collision: ids ['r::a-b::x', 'r::a.b::x'] all slugify to 'r__a_b__x'"]` |
| `check_slug_collisions([{"id": "a::b::c"}, {"id": "d::e::f"}])` — distinct slugs | `[]` | `[]` |
| `check_slug_collisions([{"id": "a::b.c"}, {"id": "a::b-c"}, {"id": "a::b c"}])` — three-way collision | one collision string listing all three ids | `["slug collision: ids ['a::b c', 'a::b-c', 'a::b.c'] all slugify to 'a__b_c'"]` |
| `check_slug_collisions([{"id": "a::b::c"}])` — single element | `[]` | `[]` |
| `check_slug_collisions([{"id": "a::b::c"}, {"id": "a::b::c"}])` — exact duplicate id | Predicted `[]` — assumed the function would treat identical ids as one canonical node | `[]` ✓ (fixed) |

## Observations

**Finding 1 — Duplicate ids reported as slug collisions (FIXED):**
`check_slug_collisions` previously accumulated ids into a `list`, so a duplicate id appeared twice
in the same slug bucket and was flagged as a collision against itself. Fixed by switching the
accumulator to a `set` so duplicate ids collapse before the `len > 1` gate.
See "Implementation defects fixed" section below.

**Finding 2 — Ids in collision reports are `sorted()`:**
The error string calls `sorted(ids)` before formatting, so the ordering of ids in the message is
lexicographic, not insertion order. This is good for deterministic output in tests, but means the
"first" id in the report is not necessarily the one that was seen first in the input. Not a bug,
just worth knowing when reading collision reports.

**Finding 3 — Space in id slugifies correctly:**
`"repo with space::path::symbol"` slugifies to `"repo_with_space__path__symbol"` — the space
becomes `_`, not `__`. Spaces do not produce double underscores because the `::` → `__`
substitution happens first, and spaces are replaced character-by-character in the second pass.
This means `"repo_with_space"` and `"repo with space"` both slugify to `"repo_with_space"` — a
real slug collision that the current test suite does not exercise. Covered here as a boundary note.

## Implementation defects fixed during verification

**Bug surfaced by Finding 1:** The verification prediction for
`check_slug_collisions([{"id": "a::b::c"}, {"id": "a::b::c"}])` expected `[]` — two identical ids
should not constitute a slug collision (that's a duplicate-primitive problem, a separate concern).
The observed output was `["slug collision: ids ['a::b::c', 'a::b::c'] all slugify to 'a__b__c'"]`.

Root cause: the accumulator was `list`, so the same id appeared twice in the bucket, satisfying
`len(ids) > 1`.

Fix: changed accumulator to `set[str]`; duplicate ids collapse to one entry so the bucket never
exceeds size 1 for a single id. The docstring was updated to document the dedup intent explicitly.
Companion test `test_slug_collision_ignores_duplicate_ids` added to `test_primitives.py`.

Committed in: TBD (commit SHA appended after commit)

## Status
✓ verified — Finding 1 (false self-collision on duplicate ids) was a real bug and has been fixed. Findings 2 and 3 are by-design behavior, documented for future reference.
