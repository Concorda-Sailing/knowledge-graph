---
node_id: GET::/api/auth/me
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85fd3a990ec8ebe8f4b573b27e207810bea363ee439f377dd61286fb590c023b
status: current
---

# GET /api/auth/me

## Purpose

Retrieves the authenticated user's profile, including their identity, roles, and active product memberships. It is the primary endpoint for bootstrapping the client-side session state, providing the necessary data to render the user's permissions and any pending policy-acceptance requirements.

## Invariants

- **Requires `Authorization` header** in the format `Bearer <token>`.
- **Returns a `UserResponse` object** containing `id`, `email`, `first_name`, `last_name`, `picture_url`, `memberships`, `permissions`, and `pending_policy_acceptances`.
- **Throws `401 Unauthorized`** if the header is missing, the token is malformed, or the token is expired.
- **Throws `404 Not Found`** if the token is valid but the associated user record no longer exists in the database.
- **Permissions are sorted alphabetically** via `sorted(auth_user.permissions)` before being returned to ensure deterministic UI behavior.

## Gotchas

- **Membership visibility is conditional** on the `grants_boat_management` attribute. If a product lacks this attribute, the field defaults to `False` (see logic for `pp.product.grants_boat_management`).
- **Case-insensitivity in identity** was a recent point of failure; ensure that any logic relying on email lookups elsewhere respects the case-insensitive matching-fix introduced in commit `9a5db8f`.
- **Policy acceptance is decoupled from roles.** The `pending_policy_acceptances` list is populated via `pending_policies_for(db, user.id)`, meaning a user can be authenticated but still have unaccepted legal/operational policies to address.

## Cross-cutting concerns

- **Auth**: Requires a valid Bearer token; uses `get_current_user_id` to resolve identity.
- **Rate limit**: Subject to standard auth endpoint limits (see `ec53704` regarding rate limits on auth endpoints).
- **Side effects**: Used by `concorda-web::src/lib/api.ts::authApi.me` to initialize the global user state upon app load.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.me` (used for test-side session verification).
- `concorda-web` (primary consumer for user profile and permission bootstrapping).
