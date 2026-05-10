---
node_id: GET::/api/profile
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c8e3efa566b678bef5c99a8951c895dc0f322c815c0047f952bb66d23277907c
status: current
---

# GET /api/profile

## Purpose

Retrieves the profile data for the currently authenticated user. It serves as the primary source of truth for user-specific metadata (like `mailing_address`, `preferences`, and `meta`) and is the standard way for the frontend to fetch the identity of the logged-in person.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a `ProfileRead` object**, which is a serialized version of the `Person` model.
- **Strictly read-only** for this specific GET method; any modifications to the profile must use the `PUT` method on the same route.

## Gotchas

- **Recent IDOR audit (commit `c9a7c41`)** ensures that this endpoint only returns the profile of the `current_user` and does not allow fetching other users' profiles via ID manipulation.
- **The `preferences` and `meta` fields are subject to partial updates** (as seen in the sibling `PUT` method logic), but this GET endpoint returns the fully merged state.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` to establish the `current_user` identity.
- **Websocket**: While this GET endpoint is passive, the sibling `PUT` method triggers `PERSON_UPDATED` and `DIRECTORY_CHANGED` events which may affect UI-side listeners.
- **Side effects**: Changes to the profile (via the sibling `PUT` method) trigger updates to the `PERSON_UPDATED` event stream.

## External consumers

- `concorda-web` (via `profileApi.get`)
- `concorda-test` (via `ApiClient.getProfile`)
