---
node_id: concorda-web::src/contexts/auth-context.tsx::useAuth
node_kind: hook
feature: auth
last_reviewed: 2026-05-09
last_reviewed_against_hash: b3dfb2d0a7ed05282a89922baaefa25e2eba9f6dc5e739f1c2f02ddf2b36e5b5
status: current
---

# useAuth

## Purpose

The hook every authenticated screen calls to know who the current user is. Returns `{ user, isLoading, isAuthenticated, login, logout, refreshUser }`. Backed by `AuthProvider` mounted at the root of the app.

It is also where the **policy-acceptance gate** lives: any authenticated page outside `POLICY_GATE_BYPASS` redirects to `/policies/accept` until `tos_accepted_at` is set on the Person. And it owns the **API-down banner** — a polling loop that detects when the backend is unreachable and shows a "RefreshCw" UI rather than letting individual screens render with stale state.

28 components consume it directly.

## Invariants

- **`refreshUser()` is the only path that fetches `/api/auth/me`.** Don't add a parallel `useState` that calls `authApi.me()` from somewhere else; you'd duplicate fetches and risk inconsistent user state across components.
- **`isLoading` is initially `true`.** It flips to `false` after the first `refreshUser()` resolves. Components that render based on `user` must check `isLoading` first or risk flashing the logged-out state on initial paint.
- **`PUBLIC_ROUTES` and `POLICY_GATE_BYPASS` are explicit allowlists.** Adding a new public page (e.g., a public landing page or a new email-link target) requires updating PUBLIC_ROUTES — otherwise the auth provider redirects unauthenticated visitors to `/login`. Adding a TOS-bypass page requires updating POLICY_GATE_BYPASS — otherwise authenticated users with unaccepted policies can't reach it.
- **`apiAvailable` distinguishes network errors from auth failures.** A `TypeError` (network unreachable) sets `apiAvailable=false`; an HTTP error (401, 500) clears the token and sets user to null. The UI for these is intentionally different.
- **`auth_token` lives in localStorage.** Server-side rendering does not have it. Components rendering on the server must either gate with `"use client"` or check `typeof window !== "undefined"`.
- **OAuth state survives `searchParams`.** When the OAuth callback URL has `?code=...&state=...`, the auth flow consumes those params before redirecting. Do not strip query params on hydration.

## Gotchas

- **`refreshUser()` is wrapped in `useCallback` keyed on nothing.** It's stable across renders. Components calling it from `useEffect` should not include it in deps unless they want infinite loops to be possible.
- **The polling ref (`pollRef`) restarts on `apiAvailable` toggle.** If you add a new condition to the effect that watches it, double-check the cleanup: leaking an interval here pings the API forever in the background.
- **TOS acceptance is per-policy-version.** When a new policy version ships, every user is forced through `/policies/accept` again. Coordinate the deploy so the page is reachable before the version bumps.
- **No memo on the context value.** Every render of AuthProvider produces a new value object, which causes every consumer to rerender. Acceptable today (the provider only rerenders on user/auth changes) but worth knowing if you add high-frequency state inside the provider.

## Cross-cutting concerns

- **Login/logout flow:** `useAuth().login()` calls `authApi.login()` which hits `POST /api/auth/login`, stores the token, then `refreshUser()` populates the user object.
- **Policy gate:** Couples to the `tos_accepted_at` field on Person.
- **Membership tier:** `user.membership_tier` is read by many components to gate paid features. Don't compute this from raw fields; rely on the API to return the resolved value.
- **WebSocket auth:** The websocket connection at `/api/ws` uses the same auth token; logging out invalidates it.

## External consumers

- **AuthProvider** is mounted in `src/app/layout.tsx`. Removing or moving it breaks every authenticated page.
- The hook is exported as `useAuth`; older code may still import `useAuthContext` — those should be migrated.

## Open questions

- Should `apiAvailable: false` block the entire app or just show a banner? Today it's a banner; some destructive UIs probably should be disabled when the API is unreachable.
- Memoize the context value to reduce unnecessary rerenders if a perf issue surfaces.
