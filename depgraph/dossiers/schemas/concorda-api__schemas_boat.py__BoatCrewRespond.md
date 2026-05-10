---
node_id: concorda-api::schemas/boat.py::BoatCrewRespond
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fad649deeb02542abdb3935509b288bbe4f462bff2e0c2e078ae415506d07e22
status: current
---

# BoatCrewRespond

## Purpose

The schema for a user's response to a crew invitation. It captures the user's decision (accept or decline) to join a boat's crew. It is distinct from the invitation itself, which is a request, whereas this model represents the finalized state of that interaction.

## Invariants

- **`action` is a required string.** It must be exactly `"accept"` or `"decline"`.
- **Used exclusively for the crew-invite-respond flow.** It is the payload for the `PUT` request to `/api/boats/{0}/crew-invite/respond`.

## Gotchas

- **Strict string values for `action`.** The schema does not use a literal `Enum`, but the logic in `routers/boats.py` expects specific strings.

## Cross-cutting concerns

- **Auth**: Requires an authenticated user to submit the response.
- **Side effects**: Triggers updates to the crew roster and potentially notifies the boat owner/organizer of the decision.

## External consumers

- None known.
