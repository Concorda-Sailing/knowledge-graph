---
node_id: concorda-test::lib/api-client.ts::ApiClient.getSailingResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9aea86bd21a8946fe906a24d0fca296e2bc290ad43d50dd45f7dd6c029ed35ad
status: current
---

# ApiClient.getSailingResume

## Purpose

Retrieves the sailing resume for the authenticated user. This method provides the current user's profile data (likely including boat associations and credentials) via a `GET` request to `/api/profile/sailing-resume`. It is used to verify that the user's profile is correctly populated after registration or role assignment.

## Invariants

- **HTTP Method**: `GET`
- **Endpoint**: `/api/profile/sailing-resume`
- **Return Shape**: Returns a `Promise<Record<string, unknown>>` containing the user's profile/resume data.
- **Authentication**: Requires a valid bearer token established via `ApiClient.login`.

## Gotchas

- **Role-dependent visibility**: Recent work in `c8b6d75` and `0990b5d` indicates that the visibility of profile-related data (like boat/crew associations) is tightly coupled to the user's current role and the successful completion of the signup/invite flow.
- **Dependency on global setup**: As seen in `c70d472`, if the global setup fails to accept pending policies or handle the `/auth/accept-tos` flow correctly, subsequent calls to profile-related endpoints may fail due to incomplete user state.

## Cross-cutting concerns

- **Auth**: Dependent on the bearer token set on the `ApiClient` instance.
- **Side effects**: Data returned here is a prerequisite for verifying the "Boats" tab and "My Schedule" visibility in E2E flows (see `c8b6d75`).

## External consumers

None known.
