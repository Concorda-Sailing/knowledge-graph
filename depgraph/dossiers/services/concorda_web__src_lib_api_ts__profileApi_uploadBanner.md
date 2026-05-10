---
node_id: concorda-web::src/lib/api.ts::profileApi.uploadBanner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 88e3e6925e0de184fc22624735047ed3316f5ad50cb6abfb12839e75589ae332
status: current
---

# profileApi.uploadBanner

## Purpose

Handles the uploading of the user's profile banner image to the server. It wraps `fetchApiUpload` to target the `/api/profile/banner` endpoint. This is distinct from `uploadPicture` (which targets the profile picture) and the boat-specific upload methods, as it specifically updates the top-level user profile aesthetic.

## Invariants

- **Input is a `File` object.** The method expects a browser-native `File` or `Blob` to be passed directly to the underlying upload helper.
- **Returns a `Profile` object.** A successful upload returns the updated profile state, allowing the UI to immediately reflect the new banner URL/image.
- **Uses `fetchApiUpload`.** This ensures the multipart/form-data headers and boundary logic are handled by the standard upload utility.

## Gotchas

- **Profile-level vs. Boat-level.** Ensure you are calling `uploadBanner` and not `uploadBoatBanner`. Using the boat-specific method for a user banner will result in a 404 or incorrect resource association.
- **Dependency on `Profile` shape.** Because the return type is `<Profile>`, any breaking change to the user profile object structure in the API will cause a type mismatch in the component handling the upload response.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiUpload`, which relies on the authenticated session/bearer token established via the `ApiClient`.
- **Side effects**: Successful uploads should trigger a re-fetch or state update in the `ProfileBannerHeader` component to ensure the new image is visible without a hard refresh.

## External consumers

- `ProfileBannerHeader` in `concorda-web::src/components/profile/sections/profile-banner-header.tsx`.
