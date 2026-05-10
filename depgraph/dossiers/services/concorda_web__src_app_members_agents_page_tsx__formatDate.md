---
node_id: concorda-web::src/app/members/agents/page.tsx::formatDate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5340137dea8b819ae0308825b11f3c11122f8bdd65ef9bae24d1c7e3ba01b56f
status: llm_drafted
---

# formatDate

## Purpose

A local helper for rendering agent token expiration/creation dates within the `AgentsPage` component. It wraps the canonical `formatInOrgTz` to ensure that even when a timestamp is null or missing, the UI provides a human-readable fallback. Use this instead of `relativeFromNow` when a fixed date format is required for the UI layout.

## Invariants

- **Input is a string or null.** If the input `iso` is null or an empty string, it returns the literal string `"Never"`.
- **Delegates to `formatInOrgTz`.** It passes a fixed option set (`year: "numeric", month: "short", day: "numeric"`) to the central timezone helper to ensure consistency with the organization's display standards.
- **Requires a timezone string.** The `tz` argument must be provided to satisfy the `formatInOrgTz` signature.

## Gotchas

- **Timezone-local rendering requirement.** Per commit `f444b4c`, this function must ensure backend datetimes are rendered in the organization's timezone rather than the browser's local time to prevent display discrepancies for remote users.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
