---
node_id: concorda-web::src/lib/api.ts::orgContactsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a78c18feeca4f7482f67e91b9646b3c5e1d1f10b9f275397d86efcc37968046c
status: current
---

# orgContactsApi.update

## Purpose

Provides the interface for updating existing contact information within a specific organization. It targets a specific contact via `contactRoleId` and allows for partial updates to fields like name, email, phone, or role. Use this method when a user is editing their profile or when an admin is updating a contact's details.

## Invariants

- **HTTP Method is `PUT`** — follows standard RESTful patterns for full or partial resource updates.
- **Requires `orgId` and `contactRoleId`** — both are necessary to construct the specific resource path.
- **Payload is a partial object** — the `data` argument accepts optional fields (`first_name?`, `last_name?`, etc.), allowing for field-specific updates without overwriting the entire contact object.
- **Returns the updated `OrgContact`** — the promise resolves to the full, updated contact object.

## Gotchas

- **Role updates are sensitive** — per commit `47688ac`, certain role-based actions (like accepting co-owner invites) are gated by membership status; ensure the `role` field update logic respects the intended business logic of the recipient.
- **Dependency on `fetchApiAuthenticated`** — like all methods in this file, this requires a valid bearer token; if the user's session expires during an update, the call will fail with a 401.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has permission to modify organization members.
- **Side effects**: Updates to contact roles or details may trigger changes in how users appear in the `directoryApi` or how they are identified in `crewfinderApi` flows.

## External consumers

None known.
