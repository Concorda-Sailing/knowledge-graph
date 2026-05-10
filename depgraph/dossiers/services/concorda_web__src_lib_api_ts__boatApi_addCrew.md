---
node_id: concorda-web::src/lib/api.ts::boatApi.addCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 00e94dc9ce95fed2319d64aa444856d16b27e37c45cc3ea64a515ea5765db9e4
status: current
---

# boatApi.addCrew

## Purpose

The `addCrew` method is used to add a person to a boat's crew via a POST request. It is distinct from `inviteCrew` in that `addCrew` is intended for administrative or direct additions where a formal invitation process (and the associated email/notification flow) is not the primary driver, whereas `inviteCrew` is used for the formal invitation-to-join workflow. Use this when you need to programmatically or directly associate a `person_uuid` with a boat.

## Invariants

- **HTTP Method is `POST`** — It must be a POST request to the `/api/boats/${boatId}/crew` endpoint.
- **Requires `boatId` and `person_uuid`** — The payload must include a valid `person_uuid`.
- **Returns `BoatCrewMember`** — A successful call returns the full crew member object, including any server-generated fields.
- **Uses `fetchApiAuthenticated`** — The call must include the bearer token from the authenticated session.

## Gotchas

- **Role/Position vs. Config-Awareness** — Per commit `bf15808`, the API is sensitive to the `boat_config_id`. Ensure that any `role` or `position` passed matches the expected schema for the boat's specific configuration to avoid unexpected behavior in the UI.
- **Implicit vs. Explicit Invites** — While `addCrew` adds a member, it does not trigger the same "invitation" state as `inviteCrew`. If the UI relies on the "Accepting Crew" status (see commit `2d6b8a7`), ensure you are using the correct method to trigger the desired state.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires a valid user session with permissions to modify boat membership.
- **Side effects**: Updates the crew list which may affect the "Accepting-Crew" badge visibility on regatta detail pages (per commit `2d6b8a7`).

## External consumers

None known.
