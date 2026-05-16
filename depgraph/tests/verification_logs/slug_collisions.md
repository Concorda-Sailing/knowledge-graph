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
| `check_slug_collisions([{"id": "a::b::c"}, {"id": "a::b::c"}])` — exact duplicate id | Predicted `[]` — assumed the function would treat identical ids as one canonical node | `["slug collision: ids ['a::b::c', 'a::b::c'] all slugify to 'a__b__c'"]` — **WRONG** — duplicate ids are treated as two separate entries and flagged as a collision |

## Observations

**Finding 1 — Duplicate ids report as slug collisions:**
`check_slug_collisions` has no deduplication step before building `by_slug`. If the same id appears
twice in the input list (e.g., an extractor emits the same primitive twice due to a bug), the
function reports a slug collision for that id against itself. The error message reads
`"ids ['a::b::c', 'a::b::c'] all slugify to 'a__b__c'"` — two copies of the same string.

This is not wrong per se (a slug-collision report is still a useful signal that the input list is
malformed), but a caller reading the output might be confused: the collision report implies two
*different* primitives would write to the same file, when the real problem is a duplicate primitive.
A guard like `ids = list(dict.fromkeys(ids))` before the collision report, or a separate
deduplicate-id pass upstream, would produce a cleaner diagnostic.

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

## Status
✓ verified — one prediction was wrong (duplicate-id case); the behavior is a real diagnostic rough edge worth tracking.
