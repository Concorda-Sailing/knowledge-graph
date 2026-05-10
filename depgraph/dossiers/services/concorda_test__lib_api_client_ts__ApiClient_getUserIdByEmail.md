---
node_id: concorda-test::lib/api-client.ts::ApiClient.getUserIdByEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: db034a6e0bdcae7e36cd6ed76fe60a9bd2327daf0f76bb7ee75bd923c9d9166e
status: llm_drafted
---

# ApiClient.getUserIdByEmail

## Purpose

A best-effort lookup helper that retrieves a user's ID via their email address. It exists because the public API does not provide a direct way to filter persons by email (the `/api/persons` endpoint is admin-only and the `/api/persons/directory` is privacy-gated). It works by temporarily logging in with the provided credentials and then calling `/api/auth/me`.

## Invariants

- **Requires a password.** If the `password` argument is omitted, the method returns `null` immediately.
- **Mutates and restores auth state.** The method calls `this.login(email, password)`, which updates `this.token`, but it restores the `prevToken` immediately after the lookup to prevent side effects in the calling test.
- **Returns `string | null`.** Returns the user's ID on success, or `null` if the login attempt fails or an error is caught.

## Gotchas

- **Temporary identity switch.** Because it calls `this.login`, it changes the `ApiClient` instance's state. While it attempts to restore the `prevToken`, any failure during the `await this.me()` call could leave the client in an unexpected authenticated state.
- **Dependency on `this.login` and `this.me`.** This is a high-level orchestration of two other methods; if the signature of `login` changes (e.g., to support different auth types), this helper will break.

## Cross-cutting concerns

- **Auth**: Relies on `this.login` and `this.me` to establish and verify identity.
- **Side effects**: Used to set up state for tests involving user-specific actions (e.g., verifying a user can see certain data after an invite).

## External consumers

None known.
