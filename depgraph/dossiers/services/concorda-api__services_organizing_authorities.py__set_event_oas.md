---
node_id: concorda-api::services/organizing_authorities.py::set_event_oas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d98ec2e71589d20bb36d29accd2c3571d5a33a09b001be7d6ec405a7b2819972
status: current
---

# set_event_oas

## Purpose
Replace the full set of `OrganizationEvent` join rows tagged with `relationship='organizing_authority'` for a given event so it matches the caller-supplied UUID list. This is how an event learns which clubs are running it (the multi-OA model that superseded the legacy single-column `Event.organizing_club_id`). It is the only sanctioned write path for OA membership on events — admin endpoints call this rather than touching `OrganizationEvent` directly so the diff/validate behavior in `_set_oas` stays in one place. Three admin paths flow through it: event create (`POST /api/events`), event update (`PUT /api/events/{id}`), and event duplicate (`POST /api/events/{id}/duplicate`, which carries the source's OA list forward).

## Invariants
- Operates only on rows with `relationship == 'organizing_authority'`. Other relationship values on `OrganizationEvent` (if/when added) must remain untouched by this function.
- Diff-style writes: existing rows whose org UUID is still desired are kept (no churn / no row-id change); only the symmetric difference is mutated.
- Unknown organization UUIDs are silently dropped — `_set_oas` validates the additions against `Organization.id` and skips misses without raising. Caller cannot rely on this function to surface bad input.
- Empty/falsy UUIDs in the input iterable are filtered out before the diff.
- Does not commit. The router owns the transaction; `db.flush()` is the caller's responsibility before this runs on freshly-created events (see create path at events.py:1254).
- `Event.organizing_club_id` (legacy single-org column) is NOT modified by this function. `get_owning_org_ids_for_event` still unions both, so the legacy column remains authoritative for any event whose OA list isn't populated.

## Gotchas
- The "skip unknown UUID silently" behavior means a typo in an admin form just produces a smaller OA list than expected, with no error. If a future caller needs strict validation, do it before calling, not inside.
- Passing `oa_uuids=[]` is a real "clear all OAs" operation. Routers guard this by only calling `set_event_oas` when `oa_uuids is not None` (see the `pop(... , None)` pattern at events.py:1248 and 1322) — preserving that distinction matters: `None` = "field not in payload, leave alone", `[]` = "remove all OAs".
- The duplicate path (events.py:1402-1404) reads via `get_event_oas` then writes via `set_event_oas`. If `get_event_oas` is ever changed to return non-OA relationships, duplicate will start copying them as OAs. Keep the relationship filter symmetric across the get/set pair.
- Tier-C cross-org scope enforcement (commit 058aa8c) reads ownership via `get_owning_org_ids_for_event`, which depends on these rows being present. Forgetting to call `set_event_oas` on create produces an event with no organizational owners and falls back to the legacy `organizing_club_id` for scope checks — easy to miss in tests if the legacy column happens to be set.

## Cross-cutting concerns
- Authorization: writes here directly determine which org_admins can subsequently edit the event (`_require_can_modify_event` in events.py:1262). Removing an org from the OA list revokes its admins' edit access on the next request.
- Scope checks: `get_owning_org_ids_for_event` (same module) is consumed by Tier-C scoping to filter list endpoints. A miswrite here cascades into visibility/access decisions org-wide.
- No audit log, no websocket emission, no cache invalidation — all of that lives at the router/transaction layer.
- No rate limiting at this layer; the endpoints in front of it inherit the global `auth.py` limiter (single-worker constraint).

## External consumers
None known. Internal service helper only — not exposed directly through any API or background job. The Expo app and web frontend interact with it indirectly through the three event admin endpoints listed above.

## Open questions
- Should unknown-org-UUID inputs raise instead of silently dropping? Current behavior is convenient for partial-failure tolerance but obscures admin-form bugs.
- Migration off `Event.organizing_club_id` is incomplete (commit fdc87b4 introduced multi-OA but the legacy column is still read by `get_owning_org_ids_for_event`). When that column is retired, this function becomes the sole source of event ownership and the "skip unknown UUID" leniency may need to tighten.
