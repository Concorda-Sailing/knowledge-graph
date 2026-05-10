---
node_id: concorda-test::lib/api-client.ts::ApiClient.addRegattasToSchedule
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8d0d9a2ea6c1f91e3df0a3d5def86ff3138ee9721ca2d05bc90733929289238d
status: current
---

# ApiClient.addRegattasToSchedule

## Purpose

The `addRegattasToSchedule` method facilitates the transition from a "browsing" state to an "active participant" state. It allows a user to bookmark specific regattas and, if a `boat_uuid` is provided, automatically creates a `SailingEvent` on that boat with pre-populated timing defaults. This is the primary mechanism for testing flows where a user (Captain or Crew) commits to a specific event.

## Invariants

- **Method is a `POST` to `/api/events/my-schedule/add-regattas`**.
- **Optional `boat_uuid` triggers "Captain mode"**. Providing this field ensures the regatta is linked to a specific vessel and populates event defaults.
- **Input `regatta_ids` is a required array of strings**.
- **Returns `Promise<unknown>`**. The response body is typically used for side-effect verification in tests rather than direct data extraction.

## Gotchas

- **Policy bypass requirement**: Tests that simulate a user arriving via an email link (e.g., `email-link-flows.spec.ts`) must call `acceptAllPendingPolicies()` before or during the flow to prevent a fresh Terms of Service (TOS) version from blocking navigation.
- **Role-based visibility**: As seen in commit `c8b6d75`, the effectiveness of this call is tied to the user's role; a "Crew" user must be able to see the resulting regatta in their "My Schedule" view after the call succeeds.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token established via `ApiClient.login`.
- **Side effects**: Triggers the creation of a `SailingEvent` which populates the "My Schedule" view for the associated boat/user.

## External consumers

None known.
