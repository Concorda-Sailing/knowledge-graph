---
node_id: concorda-web::src/components/org-brand.tsx::OrgBrand
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e4c9ec204f8367c755b49056d09e190d35571697ad3ea62bb80c5433b705895c
status: current
---

# OrgBrand

## Purpose

Renders the organization's branding (logo and name) in a consistent format across the application. It uses the `useConstants` hook to fetch the current organization's identity. Use this component instead of manual `img` or `span` tags when you need to ensure the brand identity remains consistent with the global organization state.

## Invariants

- **Relies on `useConstants()`** — the component expects `orgName` and `logoUrl` to be available in the global constants context.
- **`size` prop is mandatory** — must be one of `"sm"`, `"md"`, or `"lg"`.
- **`collapsible` behavior** — when `true`, the text is hidden via the `group-data-[collapsible=icon]` selector, leaving only the icon visible.
- **Fallback UI** — if `logoUrl` is null or undefined, it renders a `div` with a `bg-muted` background as a placeholder.

## Gotchas

- **Layout shifts during "Dashboard overhaul"** — per commit `76ad44e`, the dashboard layout was updated to include inline boat config and sailing calendars; ensure that using `collapsible` in these new dashboard sections does not cause unexpected layout jumps in the sidebar or header.

## Cross-cutting concerns

- **Auth**: Uses `useConstants` which is populated after the authentication flow is established.
- **Side effects**: Primarily used in navigation elements (sidebars/headers) to represent the current organization context.

## External consumers

None known.
