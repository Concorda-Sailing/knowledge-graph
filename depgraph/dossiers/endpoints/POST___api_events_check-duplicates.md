---
node_id: POST::/api/events/check-duplicates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e6da79a70595d0fb2362d91a56e74ec72521ee566ec77359ece3b73ec667edd0
status: llm_drafted
---

# POST /api/events/check-duplicates

## Purpose

The endpoint checks for existing events that might conflict with a new event submission. It performs both an "exact" match on the name and a "fuzzy" match (substring check) to identify potential duplicates. This is used by the event creation UI to warn users before they commit a new event that might already exist in the system.

## Invariants

- **Requires `events.create` permission** via the `require_permission` dependency.
- **Input is a list of objects** containing at least a `name` and a `match_id`.
- **Returns a list of `EventDuplicateMatch` objects**, which includes the `match_id` and the `match_type` ("exact" or "fuzzy").
- **Matches are case-insensitive and whitespace-insensitive** due to `.strip().lower()` normalization on both input and existing event names.

## Gotchas

- **Fuzzy match logic is a substring check.** A match is triggered if `item_name in ex_name` or `ex_name in item_name`. This can lead to false positives if one event name is a common word contained within a longer, unrelated event name.
- **The fuzzy match is limited to names > 10 characters.** Per the implementation, the `if len(item_name) > 10 and len(ex_name) > 10` guard prevents short, common words from triggering excessive duplicate warnings.
- **The loop breaks after the first match per item.** The `break` statements on lines 1209 and 1221 mean that for a single input item, only the first matching existing event is returned, even if multiple matches exist.

## Cross-cutting concerns

- **Auth**: Requires `events.create` permission.
- **Side effects**: Used by the event creation flow in `concorda-web` to provide pre-submission warnings.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.checkDuplicates`
