---
node_id: concorda-web::src/app/members/schedule/page.tsx::ScheduleRedirect
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cba2a30998223b8999855a28af261881e1ebad4201fe00784423345bf46f24cd
status: llm_drafted
---

# ScheduleRedirect

## Purpose

Acts as a client-side redirector to move users from the base `/members/schedule` path to the specific tabbed view at `/members?tab=schedule`. It serves as a loading state (displaying a spinner) while the Next.js router performs the transition, ensuring users land on the correct functional view without manual URL manipulation.

## Invariants

- **Uses `router.replace`** — This prevents the redirect from adding an extra entry to the browser history stack, ensuring the "back" button doesn't trap the user in a redirect loop.
- **Client-side only** — The component uses `"use client"` and `useEffect` to ensure the redirect happens after the initial mount in the browser.
- **Visual feedback** — Displays a `Loader2` spinner during the transition to prevent the user from seeing a blank screen during the route change.

## Gotchas

- **Commit `4cd1587`** (Crew pools, race setup, calendar filters, directory redesign, and UX improvements) indicates this component is part of a broader redesign of the directory and calendar UX; ensure that any changes to the `members` tab structure do not break the target path `/members?tab=schedule`.

## Cross-cutting concerns

- **Auth**: None (the redirect occurs after the component mounts, but the target route `/members` is protected by the higher-level layout/middleware).
- **Side effects**: Triggers the mounting of the `members` dashboard view and its associated tab state.

## External consumers

None known.
