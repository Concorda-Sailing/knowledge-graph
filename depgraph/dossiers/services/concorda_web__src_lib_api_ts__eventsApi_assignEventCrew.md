---
node_id: concorda-web::src/lib/api.ts::eventsApi.assignEventCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f52862224e1904889576eab7f121d2b73aa4ef6d9c0b9052bad532d900cdcc5b
status: current
---

# eventsApi.assignEventCrew

## Purpose

Owner-side endpoint for placing or repositioning a person on a sailing event's crew list without going through the invite/respond email roundtrip. Used when the skipper has already squared the assignment verbally and just needs the system to reflect reality — pre-assigning known confirmed crew, slotting someone into a position, or clearing a position_name when a boat config change orphans them. The PUT goes to `/api/events/{eventId}/sailing-event/crew-assign`, requires the caller to be the event owner, and returns the updated `EventCrewMember` row. Three components consume it: the schedule detail page (orphan-cleanup on config swap, plus a generic position-assign), and the dashboard event-plan panel (single assign).

## Invariants

- Caller must be the event's boat owner — backend uses `_get_user_sailing_event_or_404(..., relation="owner")`.
- If the person isn't already on the event, the handler auto-adds them with `status="pool"` (NOT accepted/confirmed). Existing rows keep whatever status they had.
- `position_name` is whatever the caller passes — `undefined` clears it. There's no slot-name validation against the boat config; orphan cleanup at `page.tsx:356` relies on this.
- `self_selected` is forced to `False` on every call — this row is now owner-driven, even if the crew picked their own position earlier.
- Broadcasts `EVENT_CREW_UPDATED` over the websocket on success.

## Gotchas

- The framing "bypasses invite/accept flow, jumps straight to accepted" is a half-truth: the handler does not touch `status`. New auto-adds land in `pool`, not `accepted`. If you actually want owner-marks-as-accepted behavior, that's `crew-mark-response` (`markCrewResponse` / `mark_event_crew_response`), which is a different endpoint with its own constraints (must already be `invited`).
- `event-plan-panel.tsx:214` updates state with `.map` only — it assumes the person is already in `eventCrew`. If you ever call this for someone not yet on the event, the optimistic update silently drops the new row even though the server created it. The schedule page version (`page.tsx:389`) handles both cases correctly with an `exists` check.
- The orphan-cleanup at `page.tsx:356` passes `undefined` for `positionName` to clear it — relies on the JSON serializer sending `position_name: null`. Don't change the client to omit the field.
- Recent crew-status work (`dd72f2f`, `bf44b09`) introduced the `EventCrewStatus` enum and tightened status semantics elsewhere; this handler still writes `"pool"` as a literal string when auto-adding. Worth aligning if you touch it.

## Cross-cutting concerns

- Auth: owner-only via `relation="owner"` check; non-owners get 404.
- Websocket: emits `EVENT_CREW_UPDATED` to the sailing-event channel; any open detail/plan view refreshes.
- No email is sent — that's the whole point versus `crew-invite` and `crew-mark-response`. The crew member gets no notification that they were just added or repositioned.
- Roster evaluation (`evaluate_roster`) is NOT called here, unlike `mark_event_crew_response`'s decline path. If a position change should retrigger fill-from-pool logic, it currently won't.
- No audit trail beyond the row mutation itself — `responded_by_uuid` is not set (that field is only used by the mark-response path).

## External consumers

None known. Web-only endpoint; no scheduled jobs, webhooks, or Expo app calls touch it (Expo currently has no event-management UI).

## Open questions

- Should auto-added rows land in `accepted` instead of `pool` when an owner explicitly assigns a position? Today the position is set but the status stays `pool`, which means the slot may not count as filled by `accepting_crew` math (`2d6b8a7`, `b4d60c6`). Worth tracing through `_event_crew_to_read` and the slot-count callers before changing.
- Should the crew member be notified silently-added? The mark-response path notifies for exactly this "correct the record if it's wrong" reason; this path doesn't.
- Should this share a code path with `crew-mark-response`? The two are converging in intent (owner-driven crew state changes); keeping them split has cost the codebase one inconsistency already (status handling).
