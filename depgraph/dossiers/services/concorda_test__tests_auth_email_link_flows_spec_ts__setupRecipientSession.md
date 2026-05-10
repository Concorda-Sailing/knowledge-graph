---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::setupRecipientSession
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8f3c424c683347fd156d255e70ad58d4589c56b9e46f586d41d5721c925aaeb5
status: current
---

# setupRecipientSession

## Purpose

Establishes a logged-in browser session for a recipient (e.g., a co-owner or crew member) by synchronizing the `ApiClient` state with the Playwright `Page`. It performs two critical steps: first, it calls `api.acceptAllPendingPolicies()` to clear the TOS-update gate, and second, it injects the bearer token into the browser's `localStorage` under the key `auth_token`. This ensures that when the test navigates to an invite URL, the user is already authenticated and not redirected to a policy acceptance screen.

## Invariants

- **Requires `BASE_URL` load first** — The function must navigate to `BASE_URL` before attempting the `localStorage` write to ensure the write lands on the correct origin.
- **Injects `auth_token`** — The token is stored in `localStorage` via `page.evaluate` to bypass the need for a manual login UI flow.
- **Clears policy gates** — It must call `api.acceptAllPendingPolicies()` to prevent the `/policies/accept` redirect from breaking the invite flow.
- **Uses the provided `token`** — The `token` passed to the function is the one used for both the `api.setToken` call and the `localStorage` injection.

## Gotchas

- **TOS-update gate redirect** — If `api.acceptAllPendingPolicies()` is not called or fails, the authenticated request to an invite link will be intercepted by the policy acceptance gate, preventing the invite page from rendering.
- **Order of operations** — The `api.setToken(token)` call must happen before the `page.goto(BASE_URL)` to ensure the `ApiClient` instance is in sync with the browser state during the setup.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken(token)` and injects `auth_token` into `localStorage`.
- **Side effects**: Essential for testing the "Emailed invite links" flow; without this, the user cannot reach the "Invite accepted" state or the dashboard.

## External consumers

None known.
