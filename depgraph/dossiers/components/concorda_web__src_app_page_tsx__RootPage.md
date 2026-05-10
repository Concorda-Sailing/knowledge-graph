---
node_id: concorda-web::src/app/page.tsx::RootPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: da96fcd63d31d6a70038da529ca3e3bfb6a248ea71117e5bf81a99b3f8f3f57d
status: current
---

# RootPage

## Purpose

The entry point for the web application that manages the initial routing-to-auth transition. It acts as a traffic controller: if a user is authenticated, it redirects them to the `/members` dashboard; if no user is present, it renders the `JoinPage`. This prevents unauthenticated users from seeing the dashboard and ensures the `JoinPage` is the default landing state for new or unauthenticated visitors.

## Invariants

- **Redirects on successful auth** — Uses `router.replace("/members")` to move authenticated users away from the root.
- **Requires `useAuth` context** — Relies on the `user` and `isLoading` states from the auth provider to determine routing logic.
- **Displays a loading state** — Shows a `Loader2` spinner while `isLoading` is true or a `user` is present to prevent "flashes" of the `JoinPage` during the auth check.

## Gotchas

- **Redirect loop risk** — Because this component uses `router.replace`, ensure that the destination (`/members`) does not inadvertently redirect back to `/` in a way that creates a loop if the auth state is unstable.
- **The "Flash of JoinPage"** — If `isLoading` is not strictly checked, the `JoinPage` may briefly render before the redirect occurs. The current implementation guards this with `if (isLoading || user)`.

## Cross-cutting concerns

- **Auth**: Directly depends on `useAuth` to drive the routing decision.
- **Side effects**: Triggers the transition to the `/members` dashboard, which is the primary entry point for the authenticated application state.

## External consumers

None known.
