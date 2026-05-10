---
node_id: concorda-test::lib/api-client.ts::ApiClient.createUser
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 513fb794700891e667e51167eb8d95556575a54a9a776cb4f99d2abc9abeec66
status: current
---

# ApiClient.createUser

## Purpose

Provides a high-level administrative method for creating new user accounts via the `/api/admin/users` endpoint. This is a specialized administrative helper used in E2E tests to set up specific user personas (e.g., a new crew member or a co-owner) that cannot be achieved through the standard registration flow. Use this when a test requires a user with specific `roles` or `product_ids` pre-assigned.

## Invariants

- **HTTP Method is `POST`** — targets the `/api/admin/users` endpoint.
- **Requires full identity payload** — must include `email`, `password`, `first_name`, and `last_name`.
- **Returns user identity** — the response shape is `{ id: string; email: string }`.
- **Role/Product assignment** — `roles` and `product_ids` are optional arrays of strings.

## Gotchas

- **Requires Admin Privileges** — because this hits the `/api/admin/` namespace, the `ApiClient` instance must have been authenticated with a token possessing administrative rights (likely via `ApiClient.login` with an admin-seeded user).
- **Dependency on `globalSetup`** — if using this to create users for subsequent tests, ensure the environment is not in a state where the admin user itself is being wiped or reset by a concurrent setup task.

## Cross-cutting concerns

- **Auth**: Requires an administrative bearer token.
- **Audit**: N/A.
- **Side effects**: Creating a user via this method is a prerequisite for testing "invite" flows (e.g., `email-link` flows) where a user must exist before an invitation can be sent to them.

## External consumers

None known.
