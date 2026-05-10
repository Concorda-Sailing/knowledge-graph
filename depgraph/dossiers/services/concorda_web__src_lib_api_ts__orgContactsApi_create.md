---
node_id: concorda-web::src/lib/api.ts::orgContactsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3984bf6c39d84e245ef240e0a29a50df62b29855237d1f55d836542c094c90f6
status: current
---

# orgContactsApi.create

## Purpose

Creates a new contact within a specific organization. This method is used to expand an organization's contact list, typically during administrative workflows like adding crew or staff. It is distinct from the `directoryApi` which handles global person lookups; `orgContactsApi.create` is scoped strictly to the provided `orgId`.

## Invariants

- **Method is `POST`** — performs a creation action on the organization's contact endpoint.
- **Requires `orgId`** — the endpoint is path-dependent on the organization's unique identifier.
- **Payload is non-optional** — requires a specific object containing `first_name`, `last_name`, `email`, `phone`, `role`, and `contact_role_id`.
- **Returns `OrgContact`** — the successful response contains the newly created contact object.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to satisfy the organization's security context.

## Gotchas

- **Role dependency** — the `role` and `contact_role_id` must be valid within the organization's context. Failure to provide a compatible role can lead to API errors.
- **Strict payload shape** — unlike `update`, which allows optional fields, `create` requires all five fields (`first_name`, `last_name`, `email`, `phone`, `role`) to be present in the body.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the organization's contact list.
- **Side effects**: Changes made via this method will update the contact list visible in the `ClubEditPage` (see `page.tsx:146`).

## External consumers

None known.
