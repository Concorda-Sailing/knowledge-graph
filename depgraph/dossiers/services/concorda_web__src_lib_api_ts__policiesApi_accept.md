---
node_id: concorda-web::src/lib/api.ts::policiesApi.accept
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d10993d6247d87f9859785ae9328b3dccb988feb9ae165c996504277cfe03114
status: llm_drafted
---

# policiesApi.accept

## Purpose

The `policiesApi.accept` method handles the formal acceptance of policy-related contracts. It is used when a user (typically a boat owner or crew member) needs to commit to a specific set of `contract_uuids`. This is a distinct action from viewing or drafting; it is a state-changing operation that finalizes a user's agreement to terms.

## Invariants

- **Method is POST** — This is a state-changing operation.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the user has a valid session.
- **Input is an array of strings** — Accepts `contract_uuids: string[]`.
- **Returns a summary object** — The response shape is `{ accepted: number; already_accepted: number }`.

## Gotchas

- **Role-based access requirements** — Per commit `47688ac`, accepting certain invites (specifically co-owner invites) now requires a `Boat Owner` membership. If a user attempts to call this without the correct role/membership, the backend will reject the request.
- **State-change side effects** — The response provides both `accepted` and `already_accepted` counts. This is critical for UI logic to distinguish between a new acceptance and a redundant one, as seen in the logic patterns from commit `b4d60c6`.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires a valid user session and appropriate role/membership (e.g., Boat Owner).
- **Side effects**: Successful calls update the state of the user's policy commitments, which may affect the visibility of status badges in the directory or schedule views.

## External consumers

- `AcceptPoliciesPage` in `concorda-web/src/app/policies/accept/page.tsx`.
