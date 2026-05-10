---
node_id: concorda-web::src/lib/api.ts::profileApi.uploadPicture
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e14f0d66b0addad5e5c3ce9db3a41e92f2e1d5371910c6d9a4fdb6ea6b9e5e7d
status: llm_drafted
---

# profileApi.uploadPicture

## Purpose

Handles multipart/form-data uploads for user profile assets (picture, banner) and boat-specific assets (picture, banner). It uses the `fetchApiUpload` helper to ensure the correct content-type and file-handling logic are applied. Use this instead of `fetchApiAuthenticated` when the payload is a `File` object to ensure the binary data is correctly transmitted to the `/api/profile` endpoints.

## Invariants

- **Uses `fetchApiUpload`** — standard `fetchApiAuthenticated` will fail when passing a `File` object as the body.
- **Returns a `Profile` or `Boat` object** — the response shape matches the type of the asset being uploaded.
- **Path-based routing** — profile assets use `/api/profile/...` while boat assets require a `boatId` in the URL path.

## Gotchas

- **Requires `File` object** — the input must be a browser `File` or `Blob`. Passing a raw string or JSON object will cause the upload to fail or be misinterpreted by the server.
- **Endpoint-specific paths** — when uploading boat-related assets, the `boatId` is a required part of the URL path, not a query parameter.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiUpload` which relies on the authenticated session/token established by the `ApiClient`.
- **Side effects**: Updating these assets typically triggers a re-render of the user's profile header and the boat detail views.

## External consumers

None known.
