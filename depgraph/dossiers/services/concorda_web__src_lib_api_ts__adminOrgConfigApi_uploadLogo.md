---
node_id: concorda-web::src/lib/api.ts::adminOrgConfigApi.uploadLogo
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a57f18a103531a9861da33ba4cc5416abca6741c5b699e1cc4068772cb9f8af
status: current
---

# adminOrgConfigApi.uploadLogo

## Purpose

Handles the multipart/form-data upload of the organization's logo to the backend. It is a specialized method within `adminOrgConfigApi` that uses `fetchApiUpload` to wrap the `File` object into a `FormData` instance. Use this instead of `update` when the user is providing a binary file rather than a JSON-serializable configuration object.

## Invariants

- **Requires a `File` object.** The input must be a browser-native `File` or `Blob` instance.
- **Uses `POST` method.** Unlike `update` (which uses `PUT`), this method performs a `POST` to the `/api/admin/org-config/logo` endpoint.
- **Returns `OrgConfigData`.** The successful response shape matches the organization's configuration-wide data structure.
- **Requires authentication.** The underlying `fetchApiUpload` calls `getAuthToken()`; if the token is missing or the session is expired, it throws an error.

## Gotchas

- **Strictly requires `FormData`.** If you attempt to pass a raw string or JSON object to this method, it will fail because `fetchApiUpload` explicitly appends the file to a `FormData` instance with the key `"file"`.
- **Auth dependency.** Because it relies on `getAuthToken()`, this will throw an error if called in a context where the user is not authenticated, which can happen if the admin session has expired during a long-lived dashboard session.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiUpload` which requires a valid bearer token via `getAuthToken()`.
- **Side effects**: Updating the logo via this method will affect any component rendering the organization's branding (e.g., the header or the Admin System page).

## External consumers

- `AdminSystemPage` in `src/app/members/admin/system/page.tsx`.
