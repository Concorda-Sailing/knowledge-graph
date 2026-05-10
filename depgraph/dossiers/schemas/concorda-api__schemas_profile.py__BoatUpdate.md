---
node_id: concorda-api::schemas/profile.py::BoatUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c58e1f2aa21b64fb93cd5d3bfa1f44b27122c9b6f11524f2e3da0926c043bf87
status: current
---

# BoatUpdate

## Purpose

The `BoatUpdate` schema defines the payload for partial updates to a boat's profile. It is used by the `PUT /api/profile/boats/{id}` endpoint to allow clients to modify specific attributes like dimensions, location, or registration details without sending a full `BoatRead` object. It is distinct from `BoatResumeUpdate` (see sibling dossier) by focusing on the core physical and administrative attributes of the vessel rather than racing-specific credentials.

## Invariants

- **All fields are optional.** The schema uses `Optional[...] = None` for every field to support partial `PATCH`-style updates via a `PUT` method.
- **Numeric types are strict.** `length` and `draft` must be floats, while `hard_cap` and `soft_cap` must be integers.
- **`positions` is a list of dicts.** This field allows for structured spatial or positional data to be passed as a list of key-value pairs.

## Gotchas

- **Avoid nulling out fields via `None`.** Because every field is `Optional`, there is a risk of accidentally overwriting existing data with `null` if the client doesn't distinguish between "missing" and "explicitly null."
- **Schema mismatch in recent history.** Per commit `7aae433`, the addition of `banner_url` and `picture_url` was a significant change to the boat profile structure; ensure that any logic consuming `BoatRead` (which contains these fields) is aware that `BoatUpdate` does *not* include them for updates.

## Cross-cutting concerns

- **Auth**: Handled by the `PUT /api/profile/boats/{id}` router; requires authenticated user context.
- **Side effects**: Updates to this schema trigger changes in the boat-finder visibility and the boat's profile display in the crew detail pages.

## External consumers

- None known.
