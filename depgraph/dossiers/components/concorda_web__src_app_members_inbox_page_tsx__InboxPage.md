---
node_id: concorda-web::src/app/members/inbox/page.tsx::InboxPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b0a727a991fd6cd2f063535411a9fea0a8fc0f6e7668532d9d9131f8b20336b0
status: current
---

# InboxPage

## Purpose

The main entry point for the member-facing inbox view. It serves as a layout wrapper that provides the page title and descriptive subtitle for the inbox, while delegating the actual data fetching and list rendering to the `InboxList` component.

## Invariants

- **Client-side only** — Uses `"use client"` to manage the lifecycle of the inbox view.
- **Layout structure** — Maintains a `max-w-3xl` constraint to ensure the inbox content remains readable and centered on larger screens.
- **Sub-component dependency** — Relies on `InboxList` to populate the actual content; the page itself is a stateless shell.

## Gotchas

- **Subtitle wording** — Per commit `724bda7`, the subtitle was recently broadened to "Invites and Approval Requests" to better reflect the actual content types being surfaced. Ensure any future changes to the page description align with the types of notifications handled by `InboxList`.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to view the `InboxList` content.
- **Side effects**: Changes to the inbox state (new invites/requests) are surfaced here via the `InboxList` component.

## External consumers

- None known.
