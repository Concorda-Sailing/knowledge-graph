---
node_id: concorda-web::src/app/invite/[token]/page.tsx::InvitePageContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 414c85de1b06d1f45faef381de66c5fa968871fba9dd82c13310ab3150ec416a
status: current
---

# InvitePageContent

## Purpose

The core UI component for the invitation acceptance flow. It handles the lifecycle of an unauthenticated or partially authenticated user attempting to redeem an invite token. It manages three distinct states: loading the invite details, displaying an error (invalid/expired token), and the successful "accepted" state which redirects the user to the `/members` dashboard.

## Invariants

- **Token-driven lifecycle**: The component relies on the `token` parameter from the URL to fetch data via `inviteApi.getInvite(token)`.
- **State-based rendering**: The UI must strictly transition from `loading` -> `error/invite` -> `accepted`.
- **Redirect behavior**: Upon successful `inviteApi.acceptInvite(token)`, the component waits 1.5s before routing to `/members`.
- **Error handling**: If the API call fails, the error is caught and displayed as a localized string to prevent a full-page crash.

## Gotchas

- **Auth-
