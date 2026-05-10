---
node_id: concorda-web::src/lib/api.ts::eventsApi.getEventCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c26bf965e2527886d18e87817a4367b8e8b460b4bd5f5ca5c70a270e047b332d
status: llm_drafted
---

# eventsApi.getEventCrew

## Purpose

Client-side mirror for the per-event crew roster: `GET /api/events/{event_id}/sailing-event/crew` returns the full `EventCrew[]` for the caller's *own* SailingEvent — the boat the viewer captains, or the boat they're crewing on. There is no global view; the route is scoped by relation. The response is PII-gated server-side via `rule::crew_visibility::peer_pii_resume_gated`: peer crew see other peers' `person_first_name`/`_last_name`/`_picture_url`/`_email` as `null` unless the target has a published sailing resume. Boat owners and the viewer's own row always get full PII. This service is the read-side partner for every crew-mutation call (`setCrewPool`, `notifyCrew`, `sendCrewInvites`, `respondToEventCrew`, `assignEventCrew`, `markCrewResponse`, `confirmEventCrew`, `removeEventCrew`, `requestToCrew`, `respondToCrewRequest`, `updateMyPosition`) — all 9 callers fetch via this endpoint after a mutation rather than trusting the mutation's return shape for list state.

## Invariants

- **Returns `EventCrewMember[]`** matching the Python `EventCrewRead` schema field-for-field (`~/concorda-web/src/lib/api.ts:1695`). The TS `EventCrewStatus` literal union (`pool | invited | accepted | declined | confirmed | requested`) and `EventCrewRole` (`main | alternate`) are hand-mirrored from `concorda-api/models/event_crew.py`; the comment at line 1683 names that file as source of truth.
- **PII fields are `Optional`** (`person_first_name?`, `person_last_name?`, `person_picture_url?`, `person_email?`). Any UI rendering them must handle `undefined`/`null` and fall back to a non-identifying placeholder. Treating them as required strings will render `"undefined"` for peer rows.
- **`resume_published?: boolean`** signals *why* PII is present: when `false` and PII is null, the row is intentionally masked; when `true`, the peer opted in. UIs that want to show a "hidden" affordance should branch on `resume_published === false && person_first_name == null`.
- **Auth-scoped**: 404 if the caller has neither captain nor crew stake on a SailingEvent for `event_id`. No "see other boats' crews" mode.

## Gotchas

- **`EventCrewStatus` union is freshly tightened (`bf44b09`).** Before this commit the field was bare `string`, and a few call sites in `schedule-tab.tsx` / `page.tsx` compared against legacy values. The TypeScript narrowing now catches typos at compile time but a stale literal like `"pending"` will fail to build — that's correct behavior, not a regression.
- **The mutation endpoints return `EventCrewMember` (single) or `EventCrewMember[]`, but the canonical pattern is to refetch via `getEventCrew` after mutating.** All 7 call sites in `schedule/[id]/page.tsx` re-invoke `getEventCrew` post-mutation; don't optimize that out — pool reordering and alternate auto-promotion happen server-side and won't appear in the mutation response shape.
- **Don't assume `person_email` is present for any peer row.** It is the most-leaked field historically — peer-enumeration of crew emails was the motivating bug for the resume gate. Mailto links / share-by-email UIs must check before rendering.
- **`role: "alternate"` rows can auto-promote to `main`** between fetches when a main declines (`services/crew_roster.py::evaluate_roster`). UI sort order keyed on `role` should not be cached across mutations.
- **`responded_by_uuid` is conflated** — it's whoever recorded the response (self, owner-marking-verbal, owner-accepting-request), not necessarily the crew member. Don't use it as "who said yes."

## Cross-cutting concerns

- **Visibility rule**: server enforces `rule::crew_visibility::peer_pii_resume_gated` via `services/visibility.py::peer_can_see_pii` + `routers/events.py::_event_crew_to_read(include_pii=...)`. This client has no visibility logic of its own — it must trust the null-mask.
- **Status enum rule**: `rule::event_crew::status_enum` covers the 6 canonical values + transitions. The TS Literal union mirrors it.
- **Websocket**: server emits `event_crew.updated` after pool/invite/respond/confirm mutations; subscribed components should refetch via this service rather than mutating local state.
- **Auth**: all calls go through `fetchApiAuthenticated`; cookie session required.

## External consumers

- **Concorda iOS app** consumes the same endpoint and shares the PII-null contract; any new field added to `EventCrewRead` server-side must land here AND the mobile model in lockstep.

## Open questions

- **Should the response grow a `visibility_hidden: boolean` flag** so the frontend can render an explicit "Hidden crew member" placeholder rather than inferring from null PII + `resume_published === false`? Deferred per the rule's open questions; same call as on the schema side.
