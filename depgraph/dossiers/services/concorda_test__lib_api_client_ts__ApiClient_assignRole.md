---
node_id: concorda-test::lib/api-client.ts::ApiClient.assignRole
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 97a46cfb0e8e894a27d0753e2ef843ab1e1b9d17f7767ce6fb85649390f70b8d
status: llm_drafted
---

# ApiClient.assignRole

## Purpose

The `assignRole` method is a specialized helper for updating user permissions within the test environment. It allows a test to programmatically elevate or change a user's role (e.g., from a standard user to an organizer or crew member) via a POST request to `/api/roles/assign`. This is used to set up specific permission-based scenarios, such as testing how a user interacts with restricted features after a role change.

## Invariants

- **Method is `POST`** — It hits the `/api/roles/assign` endpoint.
- **Payload structure is strict** — Requires exactly `person_id` (string) and `role_name` (string).
- **Returns `Promise<unknown>`** — The return value is typically ignored in tests as the primary goal is the side effect of the role change.

## Gotchas

- **TOS Gating** — Per commit `c70d472`, ensure that any role assignment that requires a user to have accepted the latest Terms of Service is preceded by a call to `acceptAllPendingPolicies()`. Assigning roles to a user who hasn't acknowledged a new TOS version can lead to unexpected failures in subsequent UI-driven steps where the TOS modal blocks navigation.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token established via `ApiClient.login`.
- **Side effects**: Changing a role can trigger permission-based UI changes in the "Boats" tab and "My Schedule" view.

## External consumers

None known.
