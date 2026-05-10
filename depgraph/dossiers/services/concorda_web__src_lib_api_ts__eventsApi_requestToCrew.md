---
node_id: concorda-web::src/lib/api.ts::eventsApi.requestToCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1bf9e63ca156b05a24fe1b86e00a1ad72a92e1b5d69bab81e86802777bebb95f
status: current
---

# eventsApi.requestToCrew

## Purpose
Client-side mirror for the crew-side action **request to crew on someone else's race**. A logged-in sailor picks a specific boat fielded for an event and asks its owner to take them on; the call POSTs to `/api/events/{event_id}/sailing-event/crew-request` and creates an `EventCrew` row with `status="requested"` and `self_selected=true`. This is the *inbound* counterpart to the captain-driven invite flow (`sendCrewInvites`) — same EventCrew table, opposite initiator. Four UI surfaces consume it: the boat finder's apply dialog, the regatta detail page, the dashboard's "boats looking for crew" card, and the schedule card. Future Claudes editing crew flow should treat this as the canonical entry point for unsolicited crew interest — do not invent a parallel endpoint.

## Invariants
- `boatUuid` is **required**, not optional. Each Event can have multiple SailingEvents (one per fielded boat); the backend disambiguates strictly by `(event_id, boat_uuid)` and refuses to fall back to `.first()` (see `f876f14`).
- The target SailingEvent must have `accept_crew_requests=true` — backend returns 403 otherwise. UI should not surface the action when the toggle is off (regatta detail's "Accepting Crew" badge is the user-facing signal — see `b67d359`, `2d6b8a7`).
- Created row's status is always `"requested"`; transitions are `requested → accepted | declined | pool` and are owner-driven via `respondToCrewRequest` or pool moves. The crew member never self-transitions out of `requested` here.
- One EventCrew row per `(sailing_event, person)` — duplicate request returns 409. Re-asking after a decline requires the prior row be removed.
- Owners cannot request their own boat (400). Enforced server-side via BoatCrew role=owner check.

## Gotchas
- `f876f14` (`fix(events): pass boat_uuid through requestToCrew`) — earlier callers omitted `boat_uuid` and the request silently routed to whichever SailingEvent came back first. If you add a new caller, plumb the boat selection all the way down; do not let a default sneak in.
- `notes` is `notes || null` — empty string becomes null on the wire. If you ever want to distinguish "no note" from "explicit empty," this collapses them.
- Side effect chain: row insert → `broadcast_event(EVENT_CREW_UPDATED)` websocket → owner notification (in-app + email via `render_event_crew_request_to_owner_email`) with `reply_to` set to the requester's email so a captain can just hit Reply. Removing or reordering any of these breaks the Inbox UX.
- The notification's `event_type` is `"event_crew.requested"` — preference filtering keys off this string; renaming requires migrating user prefs.

## Cross-cutting concerns
- **Auth**: requires logged-in member (`fetchApiAuthenticated`); no role gate beyond "not the owner of the targeted boat."
- **Websocket**: emits `EVENT_CREW_UPDATED` to the SailingEvent room — the captain's open detail page and the dashboard card both refresh live.
- **Email**: triggers a templated owner email with Accept/Decline magic links wired through the unified invite-response dispatcher (`88d8f1c`).
- **Inbox**: this row is what `listInboxCrewRequests` surfaces to the captain; the Inbox filters to upcoming events only, so creating a request against a past race technically works but won't appear in the captain's Inbox (only on the event detail page).
- **Audit**: `self_selected=true` is the marker that distinguishes self-requested from invited; downstream analytics and the consolidated crew card branch on it.

## External consumers
None known. Members-only web UI; no integrations, scheduled jobs, or webhooks consume this endpoint directly. The Expo iOS app does not yet wire the crew-request flow.

## Open questions
- Should a 409 on duplicate request expose *which* status the existing row has, so the UI can show "you already declined" vs "you've already asked"? Currently the message is generic.
- No rate limit on requests — a sailor could spam-request every boat in a regatta. Probably fine at current scale; revisit if abuse appears.
- Pool transition (`requested → pool`) is owner-initiated; there's no path for the requester to convert their own request into a pool entry without the owner acting. Intentional, but worth confirming when the pool UX gets revisited.
