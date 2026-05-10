---
node_id: concorda-web::src/lib/api.ts::crewfinderApi.contact
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0a39c39b6b749872fa0a7f3f900e884723d1fac535d3d31e90da1bdd455f90d2
status: current
---

# crewfinderApi.contact

## Purpose

The `contact` method facilitates sending messages to either a crew member or a boat via the Crewfinder service. It acts as a bridge between the directory browsing experience and the messaging system, allowing users to initiate contact without needing to navigate to a separate profile or inbox view. Use this when a user clicks "Contact" on a `ContactDialog` or similar UI component.

## Invariants

- **Method is `POST`** — The request must use the POST method to the `/api/crewfinder/contact` endpoint.
- **Payload structure** — The `data` object must contain `contact_type` (either `"crew"` or `"boat"`), a `target_id` (string), and a `message` (string).
- **Returns a success message** — The expected response shape is `{ message: string }`.
- **Uses `fetchApiAuthenticated`** — The call must be wrapped in the authenticated fetch helper to ensure the bearer token is attached.

## Gotchas

- **`target_id` ambiguity** — While the type is a string, the backend expects the specific ID of the person or boat being contacted. Ensure the ID passed matches the `contact_type` provided to avoid silent failures or incorrect routing.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user is logged in before attempting to send a message.
- **Side effects**: Successful contact triggers the logic used by the `ContactDialog` in the members/crewfinder view.

## External consumers

- `concorda-web::src/app/members/crewfinder/contact-dialog.tsx::ContactDialog`
