---
node_id: concorda-web::src/components/dashboard/event-plan-panel.tsx::StatusBadge
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e61682003c6a6f16d4c880acfb81b285b868b4dc5b8a225c0284888072b4a289
status: llm_drafted
---

# StatusBadge

## Purpose

A purely presentational component that renders a visual status indicator for a crew member's participation state. It maps specific string-based statuses to themed `Badge` components with appropriate icons and colors. Use this to ensure consistent visual language for "invited", "accepted", "confirmed", and "declined" states within the event plan interface.

## Invariants

- **Input is a string.** The `status` prop must be one of the four hardcoded cases: `"invited"`, `"accepted"`, `"confirmed"`, or `"declined"`.
- **Returns `null` for unknown status.** If the input does not match a case, the component renders nothing rather than a fallback badge.
- **Uses specific icon/color pairings.** `"invited"` uses a `Clock` icon with an `outline` variant, while `"accepted"` uses a `Check` icon with an `emerald-600` background.

## Gotchas

- **Strict string matching.** If the backend changes the status casing or naming (e.g., "accepted" to "accepted_invite"), this component will silently render `null` due to the `default: return null` guard.
- **Visual density.** The component uses highly specific utility classes (`text-[9px] h-4 px-1 gap-0.5`) to maintain a compact footprint within the event plan panel; changing these may cause layout shifts in the parent container.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
