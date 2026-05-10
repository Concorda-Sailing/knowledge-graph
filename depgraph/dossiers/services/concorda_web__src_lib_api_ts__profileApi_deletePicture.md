---
node_id: concorda-web::src/lib/api.ts::profileApi.deletePicture
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e0440ec9fdce903747976cddafaf5c78bfa00cb578a379873f99a4b00b324ff
status: current
---

# profileApi.deletePicture

## Purpose

Removes the user's profile picture from the server. It is a specialized destructive action within the `profileApi` service, distinct from `uploadPicture` which handles the multipart/form-data upload. An agent should use this when a user interface provides a "Remove Photo" or "Delete" option for the profile avatar.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb to the `/api/profile/picture` endpoint.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the request is tied to the current session.
- **Returns a `Profile` object** — On success, the API returns the updated `Profile` resource, allowing the UI to refresh the user's state immediately.

## Gotchas

- **Dependency on `fetchApiAuthenticated`** — Because this relies on the authenticated fetch wrapper, any changes to how the session or bearer tokens are handled in `api.ts` will directly impact the reliability of this call.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to verify the user's identity and permissions.
- **Side effects**: Triggers a state update in `ProfileBannerHeader` (the primary consumer) to reflect the absence of a profile image.

## External consumers

- `ProfileBannerHeader` in `concorda-web/src/components/profile/sections/profile-banner-header.tsx`.
