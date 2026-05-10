---
node_id: concorda-web::src/lib/api.ts::eventsApi.upsertSailingEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: be3fa3ad5d1f4e49918a7c06fac8486b8998628cc3b1cc0d38f27062aaf0cfba
status: current
---

# eventsApi.upsertSailingEvent

## Purpose
Client-side mirror for an owner creating or updating their per-boat `SailingEvent` — captures `dock_time`, `departure_time`, `estimated_duration`, `crew_pool_id`, `accept_crew_requests`, positions, and notes for a specific (event, boat) pair. This is the captain's per-race plan: the row that turns a bookmarked Event into a real outing with a roster, a pool, and a calendar payload. It is the only path that creates a brand-new `SailingEvent` from the captain's chair (vs. the bulk `addRegattas`/`addSeries` paths) and the only one that mutates an existing one's logistics. The endpoint is `PUT /api/events/{eventId}/sailing-event` — note the URL is event-scoped, but the backend resolves WHICH `SailingEvent` to touch by joining through `BoatCrew` to the *caller's* owned boat. That scoping is load-bearing: multiple captains can each have their own SE on the same Event, and an unscoped lookup would silently overwrite a stranger's race plan.

## Invariants
- A first-time call (no existing SE for caller on this event) MUST include `boat_uuid` — backend returns 400 otherwise (anti-orphan guard).
- `crew_pool_id` must reference a pool whose `boat_uuid` matches the SE's resolved boat — backend 400s otherwise.
- The boat being set or moved-to must be one the caller owns (`BoatCrew.role == "owner"`, `status == "active"`).
- Caller-scoping by ownership is non-negotiable: never look up the SE by `event_uuid` alone.
- Response shape is a single `SailingEventRead` rendered through `_sailing_event_to_read` with viewer context — callers should re-fetch event detail / crew separately if they need fresh roster state (the schedule detail page does this; event-plan-panel does not).

## Gotchas
- `bf15808 fix(schedule): use stored boat_config_id instead of shape-matching` — clients should send `boat_config_id` explicitly when known; don't rely on the server to infer it.
- The schedule detail page fires a *bare* `{ boat_uuid }` upsert on first load when an owner-viewer's SE has no boat persisted, because the crew-pool endpoint 400s without a persisted `boat_uuid` (see the comment at page.tsx:229-235). Crew-viewers are explicitly excluded — silently creating an SE on their boat would promote them to captain and drop the Crew badge.
- Backend sends `logistics_set` / `logistics_updated` / `event_canceled` calendar emails as a side effect when `dock_time` transitions or any of `(dock_time, arrival_time, departure_time, departure_location, arrival_location, estimated_duration, notes)` changes alongside an existing dock. Emails go ONLY to crew with status in (`invited`, `accepted`, `confirmed`) — pool candidates and declined are skipped. A failing email does not roll back the upsert.
- `b67d359 fix(regattas): drive Accepting-Crew badge from per-race toggle` — `accept_crew_requests` is per-SE state and the regattas page badge depends on it; preserve the field on partial updates.
- `pydantic exclude_unset=True` means omitting a field leaves it untouched; sending `null` for `crew_pool_id` / `boat_config_id` clears it. Form code must distinguish "user didn't touch this" from "user cleared this."

## Cross-cutting concerns
- Auth: `require_auth` + boat-ownership check via `_require_boat_owner`.
- Side effect: calendar email dispatch (.ics) on dock/logistics transitions — touches the email queue and any external calendar that has subscribed via prior invites.
- No websocket broadcast — consumers must re-fetch (schedule detail does, event-plan-panel relies on `onSaved()` parent reload).
- Audit: none beyond standard request logging; logistics changes are inferred from `prev_values` diff at handler time and not persisted as an event log.

## External consumers
None known. Three in-app callers: `event-plan-panel.tsx` (dashboard captain plan editor), `schedule/[id]/page.tsx` (detail-page logistics save and the auto-persist-boat-on-load shim). Regattas page reads `accept_crew_requests` for the badge but does not call this endpoint directly — toggling happens through this same upsert from the schedule detail flow.

## Open questions
- Should the auto-persist-boat shim on schedule detail move server-side (e.g., the crew-pool endpoint accepts an implicit boat from caller's owned-boat-on-event), to avoid the extra round-trip and the "promote crew to captain" footgun?
- `crew_group_priority` is in the update payload but not surfaced in either current consumer — is this still wired through to the priority system, or dead since the consolidated crew card landed (1b5d864 / 03d901b era)?
