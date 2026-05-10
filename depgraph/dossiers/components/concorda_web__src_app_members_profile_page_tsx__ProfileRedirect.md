---
node_id: concorda-web::src/app/members/profile/page.tsx::ProfileRedirect
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f0e44fd3fb499c6a7e11f4a71593c5dda47a1aedc33003b56bf4ef8b70b010eb
status: current
---

# ProfileRedirect

## Purpose

A transient UI component that handles the client-side redirect from the `/members/profile` route to the actual profile view located at `/members?tab=profile`. It serves as a loading state to prevent broken-link errors when users or automated systems attempt to access the direct path, ensuring they land on the correct tabbed interface.

## Invariants

- **Uses `router.replace`** — This prevents the redirecting page from cluttering the browser history, ensuring the "Back" button doesn't trap the user in a loop.
- **Returns a loading state** — Displays a centered `Loader2` spinner while the transition occurs.
- **Client-side only** — Uses `"use client"` and `useEffect` to ensure the redirect only triggers in the browser environment.

## Gotchas

- **Path mismatch** — If the tabbed interface in `/members` is renamed or the query parameter `tab` changes, this component will redirect users to a state that may not display the profile content.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Redirects users to the `members` page, which is the primary view for the "Sailing Resume & Racing Preferences" cards (per commit `64e481d`).

## External consumers

None known.
