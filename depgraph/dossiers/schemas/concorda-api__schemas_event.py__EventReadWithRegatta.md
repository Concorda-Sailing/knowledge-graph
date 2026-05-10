---
node_id: concorda-api::schemas/event.py::EventReadWithRegatta
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0c8274a0b410bb7cf4035087186739c4627abac2c1e3fac8d6e4ae1ad77cd513
status: current
---

# EventReadWithRegatta

## Purpose
Subclass of `EventRead` that adds regatta-specific fields (`regatta_type`, `notice_of_race_url`, `sailing_instructions_url`) for the five endpoints that surface regatta detail — list, upcoming, by-id, by-slug, and the duplicate POST. It exists because the bare `EventRead` shape is used everywhere (write paths, my-schedule, custom events, image upload), so regatta extras are layered on a separate response model rather than bolted onto the base. If you're touching this, you're almost certainly working on a read endpoint that needs to render NOR/SI links or distinguish regatta sub-types in the UI.

## Invariants
- Stays a strict subclass of `EventRead` — every field on the parent must remain valid here. If you split the hierarchy, audit all 5 dependent endpoints.
- `regatta_id` is redeclared but must stay shape-compatible with the parent (`Optional[str]`) — the redeclaration is a no-op today; don't let it drift to a different type.
- All three regatta-extra fields are `Optional[str]` because not every event with this response model is actually a regatta (e.g., `/api/events` returns this shape for social events too — they just have `None` here).
- `notice_of_race_url` / `sailing_instructions_url` are URL strings, not file paths or media IDs.

## Gotchas
- Easy to assume "WithRegatta" means "guaranteed regatta" — it doesn't. The endpoints return this model for *all* events; only events with an attached `Regatta` row populate the extra fields. UI must null-check.
- The `regatta_id` redeclaration on line 81 is redundant with `EventRead.regatta_id` (line 71). Removing it is safe but not required; leave it unless you're cleaning up.
- `regatta_type` is a free string here — the source of truth for valid values lives on the `Regatta` model, not on this schema. Don't add an Enum without coordinating.

## Cross-cutting concerns
- Same auth/visibility rules as `EventRead` — this schema adds no gating of its own. Members-only filtering happens in the router, not here.
- The duplicate endpoint (`POST /api/events/{id}/duplicate`) returns this shape; if regatta fields should *not* copy on duplicate, that's a router-side decision, not a schema one.

## External consumers
Web app and Expo iOS app both consume the five endpoints. None known beyond first-party clients.

## Open questions
- Should this collapse into `EventRead` now that the base already carries `regatta_id`? The three URL fields are the only real differentiator; the split may be vestigial.
