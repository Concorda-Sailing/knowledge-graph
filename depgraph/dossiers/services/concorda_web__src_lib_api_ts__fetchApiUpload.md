---
node_id: concorda-web::src/lib/api.ts::fetchApiUpload
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 355da980d584e7352d4e11e95206f7eb415c77164e6317ab9cd1f3bd5ce38602
status: llm_drafted
---

# fetchApiUpload

## Purpose

A specialized helper for performing authenticated multipart/form-data uploads. It is distinct from `fetchApiAuthenticated` because it explicitly constructs a `FormData` object and appends a single `file` field. Use this specifically when the endpoint expects a file upload (e.g., profile pictures, boat banners, or sailing resumes) rather than a JSON body.

## Invariants

- **Requires an active session.** Throws a hard `Error("Not authenticated")` if `getAuthToken()` returns a falsy value.
- **Uses `multipart/form-data`.** The body is a `FormData` instance with the key `"file"`.
- **Returns a JSON response.** The method awaits the response and then calls `response.json()` to return the parsed result of type `T`.
- **Error handling is descriptive.** If the response is not `ok`, it attempts to parse the `detail` field from the JSON body to provide a human-readable error message.

## Gotchas

- **Strict dependency on `getAuthToken`.** If the authentication state is lost or the token is not refreshed, this will throw before the network request is even attempted.
- **Single-file constraint.** The current implementation only supports appending a single file under the key `"file"`. If an endpoint requires multiple files or different field names, this helper will fail to satisfy the contract.

## Cross-cutting concerns

- **Auth**: Uses `getAuthToken()` to inject the `Authorization: Bearer <token>` header.
- **Side effects**: Triggers updates to the user's profile view and boat detail views (e.g., `uploadPicture`, `uploadBoatPicture`, `uploadBoatBanner`).

## External consumers

None known.
