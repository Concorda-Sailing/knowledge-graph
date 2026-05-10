---
node_id: concorda-web::src/lib/api.ts::orgContactsApi.remove
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 81f7d5007c5a62d90d77e30a4d328edee92e6ab84da88a09502fb4e1c210c89d
status: current
---

# orgContactsApi.remove

## Purpose

Deletes a specific contact from an organization. It targets a unique contact via the `orgId` and `contactRoleId` to ensure the correct identity is removed. This is the destructive counterpart to the `update` method in the same object.

## Invariants

- **HTTP Method is `DELETE`** — Uses the standard RESTful pattern for resource removal.
- **Requires two identifiers** — Both `orgId` and `contactRoleId` must be provided to locate the specific resource.
- **Returns `void`** — The API returns an empty body on success; the client expects no data in the response.
- **Uses `fetchApiAuthenticated`** — Requires a valid session token to authorize the deletion.

## Gotchas

- **Role-based access control** — Per commit `47688ac`, certain administrative actions (like managing co-owners) are gated by membership requirements. Ensure the user calling this has the appropriate permissions to modify the organization's contact list.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is tied to an authenticated session.
- **Side effects**: Deleting a contact may affect the visibility of members in the directory or administrative views.

## External consumers

- `ClubEditPage` in `src/app/members/admin/clubs/[id]/page.tsx`.

## Open questions
