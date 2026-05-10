---
node_id: concorda-web::src/lib/api.ts::adminProductsApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 23ffaa0380d33d0b1477178582b655fef172218d9b2cd6d3d7338ce16981dbe0
status: llm_drafted
---

# adminProductsApi.delete

## Purpose

The `delete` method for `adminProductsApi` performs a destructive operation on a specific product resource. It is used by administrative interfaces to remove products (Memberships or Events) from the system. Use this method when a product is no longer valid or needs to be purged, rather than just being deactivated via the `update` method.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb to target the specific product resource.
- **Requires a valid `id`** — The function takes a single string argument representing the product's unique identifier.
- **Returns `void`** — The method returns a promise that resolves to nothing upon successful deletion.
- **Uses `fetchApiAuthenticated`** — This operation is protected by the standard authentication layer; it will fail if the user is not authenticated or lacks administrative permissions.

## Gotchas

- **Destructive operation** — Unlike the `update` method which can toggle `is_active`, this method removes the record entirely.
- **Dependency on `EventDetailContent`** — Per `page.tsx:704`, this method is used within the admin event detail view. Deleting a product that is tied to an active event may have downstream effects on event visibility or registration-related logic.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has the necessary permissions to modify product resources.
- **Audit**: N/A
- **Side effects**: Deleting a product may affect the visibility of the "Event" or "Membership" in the public-facing product lists and any associated registration flows.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx::EventDetailContent`
