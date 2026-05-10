---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteBanner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 339049beaab846c261c6131efc4beff3854e3b9ba81ce46fc190f3a2d70e6ff6
status: current
---

# profileApi.deleteBanner

## Purpose

Removes the user's profile banner image via a `DELETE` request. This is a specialized sibling to `uploadBanner`, which handles the multipart/form-data upload. Use this method when a user chooses to clear their banner or when implementing a "remove image" UI state.

## Invariants

- **HTTP Method is `DELETE`** — The underlying call to `fetchApiAuthenticated` must use the `DELETE` method.
- **Endpoint is `/api/profile/banner`** — The path is static and does not accept a user ID, as it is scoped to the authenticated session.
- **Returns a `Profile` object** — On success, the API returns the updated `Profile` type, which includes the new (null/empty) banner state.

## Gotchas

- **Requires authenticated session** — Uses `fetchApiAuthenticated`, so it will fail with a 401 if the user's session has expired or if the token is missing.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is tied to the current user's profile.
- **Side effects**: Deleting the banner will trigger a re-render in the `ProfileBannerHeader` component (see `profile-banner-header.tsx:107`).

## External consumers

None known.
