---
node_id: concorda-web::src/lib/api.ts::organizationsApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dc768661570e3f800019554509c72ca6211568c27c955846d427056cb71dfa56
status: llm_drafted
---

# organizationsApi.delete

## Purpose

The `delete` method removes an organization from the system. It is a destructive operation that targets a specific organization ID via a `DELETE` request. Use this method when an administrator or authorized user needs to decommission an organization entity entirely.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb to target the specific organization resource.
- **Requires `fetchApiAuthenticated`** — The call relies on the authenticated session to provide the necessary bearer token.
- **Returns a message object** — A successful deletion returns a promise resolving to `{ message: string }`.

## Gotchas

- **Destructive action** — This method is a permanent removal of the organization resource.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Side effects**: Deleting an organization will impact any UI components or data views that rely on the existence of this organization, such as the `ClubEditPage`.

## External consumers

- `ClubEditPage` in `src/app/members/admin/clubs/[id]/page.tsx`.
