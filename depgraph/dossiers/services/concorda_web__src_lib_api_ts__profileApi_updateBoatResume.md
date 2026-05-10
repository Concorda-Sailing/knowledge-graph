---
node_id: concorda-web::src/lib/api.ts::profileApi.updateBoatResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85d617e42b91eb4cbe00af291f44814fec3ac728697f97a951cfcbf38ff19b24
status: current
---

# profileApi.updateBoatResume

## Purpose

Updates the metadata and configuration of a specific boat's resume. It is used to modify the public-facing profile of a boat (e.g., name, description, or status) via a `PUT` request. Use this when a user needs to persist changes to their boat's identity or descriptive details, rather than modifying boat configurations or crew pools.

## Invariants

- **HTTP Method is `PUT`** — This is a replacement operation for the boat's resume resource.
- **Requires `boatId`** — The URL path must include the specific boat identifier.
- **Returns `BoatResume`** — A successful call returns the updated boat object.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to authorize the update.

## Gotchas

- **`fetchApiAuthenticated` dependency** — This method relies on the authentication state established by the user's session; if the token is expired or missing, the update will fail with a 401.
- **Relationship to `BoatConfig`** — While this updates the resume (the "what"), it is distinct from `updateBoatConfig` (the "how" or "where"), which handles position sets.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi-authenticated` (requires user session).
- **Side effects**: Updates to the boat resume may affect the visibility of the boat in the directory or on the `BoatPublishBar` component.

## External consumers

- `concorda-web::src/app/members/setup/page.tsx` (SetupPage)
- `concorda-web::src/components/profile/boat-publish-bar.tsx` (BoatPublishBar)
