---
node_id: concorda-web::src/app/verify-email/page.tsx::VerifyEmailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e57159b5270af027e603107901e4d07b03291c259715202b20af24743978154b
status: current
---

# VerifyEmailPage

## Purpose

The entry point for the email verification flow. It provides a `Suspense` boundary to wrap the `VerifyEmailContent` component, ensuring a loading state (via `Loader2`) is displayed while the verification logic or data fetching is in flight. This prevents layout shifts or broken UI states during the transition from the unauthenticated/unverified state to the verified state.

## Invariants

- **Must use `Suspense`** — The `VerifyEmailContent` is an async component that relies on the boundary to handle the loading state.
- **Fallback is a centered spinner** — The fallback uses `min-h-screen` and `justify-center` to ensure the loader is visually centered during the fetch.

## Gotchas

- **Commit `54d6153`** introduced the crew invite system and security fixes in the same pass; ensure that any changes to the verification flow do not inadvertently bypass the security improvements intended for the new invite system.

## Cross-cutting concerns

- **Auth**: This page is the gateway to a verified session; the verification success typically triggers a state change that allows the user to access protected routes.
- **Side effects**: Successful verification is a prerequisite for the user to access the "crew invite" features and dashboard components.

## External consumers

None known.
