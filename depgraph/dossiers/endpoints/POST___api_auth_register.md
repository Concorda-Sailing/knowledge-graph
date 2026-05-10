---
node_id: POST::/api/auth/register
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 807bfadb93bf23eeb57931e8ae5ea2b0c7821441af00668a7f265ef2681f6a3b
status: llm_drafted
---

# POST /api/auth/register

## Purpose

Creates a new user account by initializing a `Person` record and an optional `Boat` instance. This endpoint is the primary entry point for new members to join an organization, handling both free and paid membership tiers. It is distinct from the login flow as it performs heavy-duty creation logic, including password validation, membership type verification, and payment-to-transaction binding.

## Invariants

- **Method/Path**: `POST /api/auth/register`.
- **Input**: Requires a `RegistrationRequest` containing an email, membership type (slug), and optional password/transaction data.
- **Email Uniqueness**: The email check is case-insensitive; the system searches for the existence of the email (lowercased) before proceeding.
- **Membership Validation**: The `membership_type` must match an active `TemporalProduct` slug.
- **Payment Requirement**: If the selected `product.price > 0`, a valid, unused `transaction_id` must be provided.
- **Return Shape**: On success, creates a `Person` and potentially a `Boat`; on failure, returns a 400 or 429 error.

## Gotchas

- **Rate Limiting**: Registration is protected by an IP-based rate limiter (`_register_rate_limit`). This is bypassed in the test environment via `_RATE_LIMITS_DISABLED` to prevent blocking automated test suites.
- **Case-Insensitivity**: Per commit `9a5db8f`, the system now matches emails case-insensitively during registration to prevent duplicate accounts with different casing (e.g., `User@example.com` vs `user@example.com`).
- **Transaction Reuse**: A transaction can only be used once. If `transaction.person_id` is already set, the registration will fail with a 400 error to prevent double-spending.
- **Password Validation**: If a password is provided, it must pass `validate_password`. Failure to meet complexity requirements results in a 400 error.

## Cross-cutting concerns

- **Auth**: Creates the initial `Person` identity; subsequent authentication relies on the credentials established here.
- **Rate limit**: Uses `_register_rate_limit` keyed by `client_ip`.
- **Side effects**: Triggers the creation of a `Person` record and potentially a `Boat` record; may trigger setup emails if no password is provided.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.register`
- `concorda-web::src/lib/api.ts::authApi.register`
