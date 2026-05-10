---
node_id: concorda-test::lib/api-client.ts::ApiClient.updateProfile
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 388766abd0344d1c8a531e16e13202a286299bd7c43c93ca5dc567a365c53af3
status: current
---

# ApiClient.updateProfile

## Purpose

Updates the authenticated user's profile information via a `PUT` request to the `/api/profile` endpoint. This is a sibling to `getProfile` and is used in E2E tests to simulate user-driven changes like updating personal details or settings. Use this when a test needs to transition a user from a default state to a customized state before testing downstream features.

## Invariants

- **Uses `PUT` method** to the `/api/profile` endpoint.
- **Accepts `Record<string, unknown>`** as the payload, allowing for flexible data structures.
- **Returns `Promise<unknown>`**, typically resolving to the updated profile object or a success status.
- **Requires an authenticated session** established via `ApiClient.login` or similar.

## Gotchas

- **Policy acceptance requirement:** Per commit `c70d472`, the API/setup may require pending policies to be accepted (e.g., `/auth/accept-tos`) before profile-related updates can be successfully processed or reflected in certain flows.
- **Dependency on `globalSetup`:** If the user profile is being updated as part of a multi-step flow (like the `eaff02b` new-crew-signup), ensure the initial user state is correctly seeded, or the `PUT` may fail due to missing required fields or uninitialized state.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token from an authenticated `ApiClient` instance.
- **Side effects**: Changes to the profile may impact how user-specific data is rendered in the "Boats" tab or "My Schedule" view if those views rely on profile-derived metadata.

## External consumers

None known.
