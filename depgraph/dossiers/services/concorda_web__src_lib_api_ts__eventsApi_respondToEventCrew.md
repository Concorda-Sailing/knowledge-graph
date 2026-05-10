---
node_id: concorda-web::src/lib/api.ts::eventsApi.respondToEventCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d38e0363cc9f4f39a12d5972d9ccb7c2356bbce92caf4af6b25c8aaf126795e3
status: current
---

# eventsApi.respondToEventCrew

## Purpose

Client-side mirror for the crew member's accept/decline action on an invite — `PUT /api/events/{event_id}/sailing-event/crew-respond`. This is the partner of `sendCrewInvites`: where the owner pushes invites out, this is how the *recipient* answers. The state transition is `invited → accepted | declined`; on accept the crew member can claim a `position_name` (validated server-side as still-open and listed in `positions_needed`); on decline the row goes terminal. Returns the single updated `EventCrewMember`. UIs MUST refetch the full roster via `getEventCrew` after — accepting one slot doesn't mutate other rows in the response, but an alternate may have been auto-promoted (`services/crew_roster.py::evaluate_roster`) and the boat owner gets a notification email; both are invisible to this call's return shape. 4 components consume: `schedule/[id]/page.tsx` (twice — accept vs decline paths), `my-crew-tab.tsx`, `schedule-tab.tsx`.

## Invariants

- **`action` is exactly `"accept" | "decline"`** — anything else is rejected server-side with 400. The TS union enforces this at compile time; don't widen it.
- **Only `invited` rows respond.** The handler filters to `EventCrew.status == "invited"` and 404s if the caller has no pending invite (already-accepted, never-invited, declined-then-trying-again all 404). UI should hide the accept/decline buttons unless the row's status is `"invited"` — calling on any other status is always an error.
- **`positionName` is optional and only meaningful on accept.** On decline it's silently ignored. On accept, server validates: position is in `sailing_event.positions_needed` AND has open slots (counted against currently-`accepted` rows). Out-of-range or full → 400.
- **Returns `EventCrewMember`, not the list.** Callers refetch via `getEventCrew` to pick up alternate-promotion side effects and pool reordering.
- **Self-action only**: the route is scoped by `relation="crew"` — caller must be the same person whose invite is pending. Owners marking on someone else's behalf use `markCrewResponse` instead.

## Gotchas

- **Acceptance silently mutates the user's `SailingResume`** — server appends the chosen `position_name` to `resume.positions_preferred` if not already there. UI rendering the resume should refetch after a position-selecting accept; no websocket event covers this resume-side change.
- **Alternate auto-promotion fires only on decline.** `evaluate_roster` runs in the decline branch and can flip another person's `role` from `alternate` to `main` and their `status` from `pool` to `invited`. The promoted person gets an email; the responding caller gets nothing back about it. Roster UIs that show "X declined, Y bumped up" need to refetch, not diff the response.
- **`88d8f1c` wired the unified-dispatcher response page through this endpoint.** Email Accept/Decline links now route here; if you add params (`action`, `position_name`) you must keep them URL-safe — the response page passes them through.
- **`b4d60c6` decoupled accept-counting from position-name presence.** Don't reintroduce `position_name`-required gating in the UI; positions are optional on accept and counts must work without one.
- **No idempotency.** A second accept on an already-accepted row 404s (filter requires `status == "invited"`); UI double-click protection should disable the button on first click, not rely on the server's tolerance.

## Cross-cutting concerns

- **Email**: on every response, the boat owner gets `event_crew.{accepted|declined}` notification via `render_event_crew_response_to_owner_email`. Failure to render/send is not currently caught (unlike `confirm_event_crew`'s 2026-05-10 hardening) — a notification failure here would 500 the response. Candidate for the same try/except treatment.
- **Websocket**: handler emits `event_crew.updated` after commit. Subscribed components in other tabs/sessions should refetch via `getEventCrew`.
- **Status enum**: writes use `EventCrewStatus.ACCEPTED` / `.DECLINED` per `rule::event_crew::status_enum`. Both are valid transitions out of `invited`.
- **`responded_by_uuid` = `current_user.id`** here (the genuine self-response case — the cleanest semantics of that conflated field).
- **Auth**: `fetchApiAuthenticated` cookie session; `require_auth` on the handler.

## External consumers

- **Concorda iOS app** mirrors this endpoint for the in-app invite response. Email Accept/Decline deep links land on the unified response page (`88d8f1c`) which calls this same service.

## Open questions

- **Should declined be reversible?** Currently `declined` is terminal per the rule's decision table; a re-invite is the only path back. UX hasn't been pushed on this yet.
- **Should the response include the promoted alternate's identity** so the UI can show "Y was bumped up" without a refetch round-trip? Currently no; roster recomputation is opaque to the caller.
