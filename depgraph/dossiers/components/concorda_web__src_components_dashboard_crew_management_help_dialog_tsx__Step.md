---
node_id: concorda-web::src/components/dashboard/crew-management-help-dialog.tsx::Step
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 37c226e7dfc47d309c0080d68c9ef34d0c32d7b18c14030bc65402520ac4f824
status: llm_drafted
---

# Step

## Purpose

The `Step` component is a local helper used to render instructional steps within the `CrewManagementHelpDialog`. It provides a consistent visual pattern for an icon, a title, and a description to guide users through the crew management workflow. It is distinct from the main `CrewManagementHelpDialog` as it is a stateless, purely presentational sub-component.

## Invariants

- **Input structure** — Accepts `icon` (ReactNode), `title` (string), and `description` (ReactNode).
- **Layout** — Uses a flex-start alignment with a fixed-width icon container (`w-8 h-8`) to ensure vertical alignment of text across multiple steps.
- **Visual hierarchy** — The `title` uses `text-sm font-medium` while the `description` uses `text-xs text-muted-foreground` to maintain a clear distinction between header and body text.

## Gotchas

- **Icon sizing** — The icon container is hardcoded to `w-8 h-8`. If a larger icon is passed, it may break the alignment or overflow the container's intended visual weight.
- **Text wrapping** — The `description` is a `ReactNode` and can contain complex JSX (as seen in the `Mail` step). Ensure that any complex content passed to `description` does not break the `leading-snug` vertical spacing.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
