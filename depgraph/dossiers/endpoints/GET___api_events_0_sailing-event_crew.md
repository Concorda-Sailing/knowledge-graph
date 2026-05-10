---
node_id: GET::/api/events/{0}/sailing-event/crew
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6201cef804dabb90a09149186e7d12ac874ff47a4542a91e6aa07eea2109e68a
status: llm_drafted
---

# GET /api/events/{event_id}/sailing-event/crew

## Purpose

Returns the list of crew members associated with a specific sailing event. It is distinct from the `crew-pool` endpoint, which is used for writing/syncing the pool; this is a read-only view for displaying current membership. The endpoint implements strict privacy logic: while the boat owner and the viewer (if they are part of the crew) see full PII, other peer crew members see redacted information if the target's sailing resume is not public.

## Invariants

- **Method is `GET`** and requires a valid `event_id`.
- **Auth is mandatory** via `require_auth`.
- **Returns a list of `EventCrewRead` objects.**
- **Privacy-aware rendering:** The visibility of PII (name/email) is dynamically determined by `peer_can_see_pii` based on the viewer's relationship to the event and the target's resume status.
- **Ownership priority:** If the viewer is the boat owner (`viewer_is_owner`), they receive full PII for all members.

## Gotchas

- **Crew badge suppression:** Per commit `8842b8d`, the UI/API logic must ensure the "Crew" badge is suppressed when a user is captaining their own boat to avoid redundant status signaling.
- **PII Leakage Risk:** The function `peer_can_see_pii` is the critical guard. If modified, it directly impacts whether peer crew members can see each other's private contact details.
- **Visibility logic dependency:** The endpoint relies on `_get_user_sailing_event_or_404` with `relation="any"` to establish the base event context before applying the more restrictive `_require_can_view_sailing_event` check.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Side effects**: Affects the rendering of the "Crew" list in the schedule detail page and any component displaying event membership.

## External consumers

- `concorda-web` (via `eventsApi.getEventCrew`)
- `concorda-test` (via `ApiClient.getEventCrew`)
