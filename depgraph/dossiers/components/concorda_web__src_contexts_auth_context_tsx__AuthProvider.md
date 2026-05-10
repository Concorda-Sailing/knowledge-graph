---
node_id: concorda-web::src/contexts/auth-context.tsx::AuthProvider
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: badb8f3bdee0965975cc75f3218a74178d0641ecc0a4c63d2a6a028e7c3eb072
status: current
---

# AuthProvider

## Purpose

The central authentication provider for the web application. It manages the global `user` state, tracks API availability, and handles the initial authentication handshake via `authApi.me()`. It serves as the root provider for all authenticated routes, ensuring that the application can reactively handle both user identity and backend connectivity status.

## Invariants

- **`user` state is null if no token is present.** If `getAuthToken()` returns nothing, the user is explicitly set to `null` and loading is set to `false`.
- **`apiAvailable` tracks connectivity.** If `authApi.me()` throws a `TypeError`, the provider assumes the network or API is unreachable and enters a polling state.
- **Polling is triggered by API failure.** When `apiAvailable` is false, a `setInterval` calls `checkApiHealth()` every 5000ms to attempt recovery.
- **`localStorage.removeItem("auth_token")` is called on HTTP errors.** If the API is reachable but returns a non-200 status (other than a network TypeError), the local token is purged to force a logout.

## Gotchas

- **Redirect logic for unauthenticated users.** Per commit `a437123`, unauthenticated users must be bounced to `/login` rather than `/join`. Ensure any logic modifying `PUBLIC_ROUTES` or `POLICY_GATE_BYPASS` respects this distinction to avoid incorrect routing loops.
- **The `apiAvailable` state is volatile.** If the API is down, the provider enters a polling loop using `checkApiHealth`. If you modify the health check logic, ensure it doesn't trigger infinite loops or high-frequency requests that bypass the 5s interval.

## Cross-cutting concerns

- **Auth**: Provides the `user` object and `isLoading` state used by `useAuth` and all protected routes.
- **Side effects**: Rebuilding the `user` state or `apiAvailable` status affects all components consuming `useAuth`, including the dashboard and profile views.

## External consumers

None known. (Internal to `concorda-web`).
