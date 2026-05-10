---
node_id: concorda-web::src/app/invite/[token]/page.tsx::InvitePage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c5a6b0f838b804444ab086ddb5a4f9a0e8c5cde9de3035298a0f7de1689dd65b
status: llm_drafted
---

# InvitePage

## Purpose

The entry point for the invitation flow, responsible for handling the initial loading state of the invite process. It wraps `InvitePageContent` in a `Suspense` boundary to manage the asynchronous data fetching required to validate the invitation token. This component ensures the user sees a loading spinner (`Loader2`) rather than a blank screen or a broken UI while the server-side state or token validation is in flight.

## Invariants

- **Must wrap `InvitePageContent` in `Suspense`** to prevent the entire page from failing if the token validation fetch is slow.
- **Uses `Loader2` for the fallback UI** to maintain visual consistency with the rest of the app's loading patterns.
- **The fallback is a centered flex container** with `min-h-screen` to prevent layout shifts during the transition from loading to content.

## Gotchas

- **Avoid dead-end "Log in" links.** Per commit `d5ee240`, if an invitee has no account, the UI must not present a "Log in" link that leads to a dead end; the flow must gracefully handle the transition to account creation or registration.

## Cross-cutting concerns

- **Auth**: Triggers the initial identity/token validation via `InvitePageContent`.
- **Side effects**: The successful resolution of this page is a prerequisite for the user to join the organization and access the dashboard.

## External consumers

None known.
