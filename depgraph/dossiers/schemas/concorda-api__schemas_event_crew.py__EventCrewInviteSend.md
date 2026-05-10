---
node_id: concorda-api::schemas/event_crew.py::EventCrewInviteSend
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 02274354bc05db35edfb42f9393d32ff2e0104f15b79faeb1df4dee27b3f6119
status: current
---

# EventCrewInviteSend

## Purpose

The schema for initiating a crew invitation for a specific event. It allows a user to either invite a specific list of people via `person_uuids` or, by passing `None`, trigger a broadcast invitation to all members within the existing `EventCrewPoolSet`. Use this when implementing the "Invite All" or "Select Specific Members" logic in the crew management UI.

## Invariants

- **`person_uuids` is optional.** If `None` is passed, the system defaults to inviting the entire current pool.
- **Input is a list of strings.** `person_uuids` must contain valid UUID strings for the target persons.
- **Directly consumed by `POST /api/events/{0}/sailing-event/crew-invite`.**

## Gotchas

- **Broadcast logic dependency.** Per commit `7e78c9d`, the behavior of `person_uuids = None` is critical for the "Invite All" feature; ensure the backend handles the `None` case to target the full `EventCrewPoolSet` rather than failing validation.
- **Role/Priority distinction.** While this schema only carries the UUIDs, the underlying `EventCrewPoolMember` (used in the pool set) tracks `role` and `priority`. This schema is the "shallow" version used for the initial dispatch.

## Cross-cutting concerns

- **Auth**: Requires a user with sufficient permissions (likely Skipper or Admin) to call the dependent route.
- **Side effects**: Triggers the crew invitation workflow, which may impact the "unread/pending invite" status for the targeted users.

## External consumers

None known.
