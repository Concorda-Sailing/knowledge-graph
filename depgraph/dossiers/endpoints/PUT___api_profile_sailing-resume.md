---
node_id: PUT::/api/profile/sailing-resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c52fcdee787aa6d9d0d484a1b4fedf3602f6df328bc628f634a6eb09904d32c
status: current
---

# PUT /api/profile/sailing-resume

## Purpose

Handles the upsert (create or update) logic for a user's sailing resume. It allows users to manage their professional credentials, experience, and availability. This endpoint is distinct from a simple "update" because it handles the initial creation of the `SailingResume` record if one does not yet exist for the `current_user`.

## Invariants

- **Method is `PUT`** and the path is `/api/profile/sailing-resume`.
- **Requires authentication** via the `require_auth` dependency.
- **Returns a `SailingResumeRead` model**, ensuring the response shape is consistent for the frontend.
- **Strict field allowlist**: Only fields defined in `SAILING_RESUME_ALLOWED_FIELDS` (e.g., `experience_level`, `us_sailing_number`, `availability`) are persisted to the database.
- **Ownership is enforced**: The `person_id` is always tied to the `current_user.id`.

## Gotchas

- **Credential field expansion**: Per commit `f311f7a`, the schema was recently expanded to include `us_sailing_number`, `world_sailing_id`, and `world_sailing_group`. Ensure any new credential types are added to the `SAILING_RESUME_ALLOWED_FIELDS` set in this file, or they will be silently dropped during the `model_dump` filtering.
- **Nested availability serialization**: The `availability` field requires manual handling of the `model_dump` if it is passed as a Pydantic model, as seen in the logic for `update_data["availability"]`.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Websocket**: Emits `SAILING_RESUME_UPDATED` upon successful upsert.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Triggers updates to any UI components or services listening for the `SAILING_RESUME_UPDATED` event.

## External consumers

- `concorda-web` (via `profileApi.updateSailingResume`)
- `concorda-test` (via `ApiClient.updateSailingResume`)
