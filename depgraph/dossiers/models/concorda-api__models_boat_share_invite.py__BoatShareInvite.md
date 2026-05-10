---
node_id: concorda-api::models/boat_share_invite.py::BoatShareInvite
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 26afbdf981e37ae971d23091e433eac5df593637fa8c772fc5917bb5ffd8f02d
status: llm_drafted
---

# BoatShareInvite

## Purpose

The `BoatShareInvite` model represents a single-use, person-less token used to facilitate the QR/share-link flow. It is distinct from `BoatCrew` (which requires an existing person) and `PendingCrewInvite` (which is tied to a specific email address). A record is created when an owner opens the share dialog and is marked as consumed once a user successfully signs up using the token.

## Invariants

- **`invite_token` is a unique identifier.** It must be a 64-character string and is the primary lookup key for the share flow.
- **`boat_uuid` is required.** Every invite must be explicitly tied to a specific boat.
- **`consumed_at` and `consumed_by_person_uuid` are nullable.** These fields are only populated once the token is actually used to complete a signup.
- **`type` is fixed.** The `__init__` method explicitly sets the type to `"BoatShareInvite"`.

## Gotchas

- **Single-use lifecycle.** Because this is a "person-less" invite, the token is consumed upon the first successful signup. Subsequent attempts to use the same token will fail to find an unconsumed record.

## Cross-cutting concerns

- **Auth**: Access to create and retrieve these tokens is governed by the boat owner's permissions.
- **Side effects**: Successful consumption of a `BoatShareInvite` triggers the creation of a new `BoatCrew` entry and updates the boat's membership state.

## External consumers

- Web/Mobile client (QR/Share-link flow) via `GET /api/boats/{0}/share-invite/{1}` and `POST /api/boats/{0}/share-invite`.
