---
node_id: POST::/api/regattas/check-duplicates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 334e36c2508979efa17ea84f9f363cf3153b30e70f8fdef1792bfc28776da227
status: current
---

# POST /api/regattas/check-duplicates

## Purpose

The duplicate detection engine for regattas. It accepts a list of potential regatta objects and checks them against existing database entries to identify name or pattern collisions. This is used by the frontend to warn users of potential duplicates before a formal creation or update occurs.

## Invariants

- **Requires `_require_manager`** — only users with manager-level permissions can trigger a duplicate check.
- **Input is a list of objects** — the `DuplicateCheckRequest` expects an array of items containing at least a `name`.
- **Returns a list of `DuplicateMatch` objects** — each match includes the `match_id`, `match_name`, and the `match_type` (either "exact" or "fuzzy").
- **Case-insensitive matching** — both the input names and existing database names are normalized via `.strip().lower()` before comparison.

## Gotchas

- **Fuzzy match logic is length-dependent** — a match is only flagged as "fuzzy" if both the input name and the existing name are longer than 10 characters. This prevents short, common words from triggering false positives in the fuzzy logic.
- **The loop breaks early on match** — once an item in the input list matches an existing regatta (either via exact or fuzzy logic), the function `break`s the inner loop for that specific item. This ensures one input item doesn't return multiple duplicate warnings.

## Cross-cutting concerns

- **Auth**: Requires `_require_manager` dependency.
- **Side effects**: Used by the regatta creation flow in the web UI to prevent accidental duplicate entries.

## External consumers

- `concorda-web` via `regattaApi.checkDuplicates`.
