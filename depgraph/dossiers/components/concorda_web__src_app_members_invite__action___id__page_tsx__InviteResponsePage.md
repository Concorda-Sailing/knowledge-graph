---
node_id: concorda-web::src/app/members/invite/[action]/[id]/page.tsx::InviteResponsePage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 00d5e760d8e759162166bfc7158c181935417678a15190b99aa9b482030305cc
status: current
---

# InviteResponsePage

## Purpose

The landing page for users clicking an "Accept" or "Decline" link in an invitation email. It automatically executes the response via `inviteResponseApi.respond` once the user is authenticated. It is distinct from a manual settings page because it is a single-use, automated transition state that resolves the invitation status immediately upon page load.

## Invariants

- **Action must be valid.** The `action` param must be exactly `"accept"` or `"decline"`; otherwise, the page renders an "Unknown action" error state.
- **Requires authentication.** The page waits for `useAuth()` to resolve; if the user is unauthenticated, the `auth-context` redirects them to `/login` with the current URL as a redirect target.
- **Single execution.** The response is triggered exactly once per page load to prevent duplicate submissions.
- **Status mapping.** The UI transitions through `working` -> `ok` or `already` (if the invitation is no longer pending) or `error` (if the API returns a 403/forbidden/not-a-voter error).

## Gotchas

- **React StrictMode double-fire.** Per commit `ef5f386`, the page uses `submittedRef` to guard against `useEffect` firing twice in development. Without this, the first call succeeds and the second call hits a 409/already-voted error, causing the UI to show an error state instead of a success state.
- **Error parsing.** The `statusFromError` helper (used in the `catch` block) is responsible for mapping specific error strings (like "already", "not a voter", or "403") to the correct UI state.

## Cross-cutting concerns

- **Auth**: Depends on `useAuth()` to resolve the user and handle the redirect-to-login flow.
- **Side effects**: Successful completion of this page updates the member's status and the invitation's state in the database.

## External consumers

None known.
