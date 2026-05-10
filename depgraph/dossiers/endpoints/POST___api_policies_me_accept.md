---
node_id: POST::/api/policies/me/accept
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a6a31ea5ddd53c2adfb2197353b52fc3ae9e753a4076ac52b20ee460ab819d64
status: llm_drafted
---

# POST /api/policies/me/accept

## Purpose

Records the formal acceptance of one or more contract versions for the authenticated user. This endpoint is used to transition a user from a "pending" state to an "accepted" state for specific policies, ensuring that legal requirements (like ToS acceptance) are timestamped and logged. It is distinct from administrative policy management; it is a user-facing action that mutates the `Person` and `PersonContractAcceptance` tables.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Input must contain non-empty `contract_uuids`**; otherwise, returns a 400 error.
- **Returns a JSON object** with `accepted` (count of new records) and `already_accepted` (count of existing records).
- **Validates existence of all UUIDs**; if any provided UUID is not found in the `Contract` table, the entire request fails with a 404.
- **Mutates `Person.tos_accepted_at`** if one of the accepted contracts has the slug `"tos"`.

## Gotchas

- **The "tos" slug side-effect:** If a contract with the slug `"tos"` is included in the request, the `Person.tos_accepted_at` field is updated to the current UTC time. This is a legacy synchronization step to ensure older code paths reading the `Person` table see the most recent acceptance.
- **Idempotency via `accepted_ids`:** The endpoint checks existing `PersonContractAcceptance` records before inserting to prevent duplicate entries for the same user/contract pair.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the `current_user`.
- **Audit**: Records the `ip_address` (via `_client_ip`) and `accepted_at` timestamp in the `PersonContractAcceptance` table.
- **Side effects**: Updating the `"tos"` slug triggers a side-effect on the `Person` record's `tos_accepted_at` field.

## External consumers

- `concorda-web` (via `policiesApi.accept`)
- `concorda-test` (via `ApiClient.acceptAllPendingPolicies`)
