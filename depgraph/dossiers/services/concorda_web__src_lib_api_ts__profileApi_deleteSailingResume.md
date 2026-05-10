---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteSailingResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 59d18209e9545c34854585365104980dc245a5db63beb09d5fffeb61125db70a
status: llm_drafted
---

# profileApi.deleteSailingResume

## Purpose

Deletes the user's sailing resume from their profile. This is a destructive action that removes the associated `SailingResume` data via a `DELETE` request to the `/api/profile/sailing-resume` endpoint. It is distinct from `updateSailingResume` (which preserves the record) and should be used when a user intends to completely clear their professional sailing history from their profile.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb to target the `/api/profile/sailing-resume` endpoint.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the request is tied to the current user's session.
- **Returns a success message** — The expected response shape is `{ message: string }`.

## Gotchas

- **Destructive side effect** — Unlike `updateSailingResume`, this call removes the resource entirely. Ensure the UI provides a confirmation step before calling this to prevent accidental data loss.

## Cross-cutting concerns

- **Auth**: Requires a valid user session via `fetchApiAuthenticated`.
- **Side effects**: Deleting the resume may impact any UI components that rely on the presence of a `SailingResume` object for the user's profile view.

## External consumers

None known.
