---
node_id: concorda-web::src/components/boat/boat-profile-card.tsx::InfoCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 908fe062d8194f53aa628efbbaa481c260850dcd6eec1402ffd097d423a06b83
status: llm_drafted
---

# InfoCard

## Purpose

A layout utility component used to group related metadata within the boat profile view. It provides a standardized visual container (using `Card`, `CardHeader`, and `CardContent`) to present an icon, a title, and a set of child elements (such as `Row` or `Chips`) in a structured format.

## Invariants

- **`title` is a required string.** It is rendered in the `CardHeader` alongside the `icon`.
- **`icon` is a ReactNode.** It is expected to be a small, visual element (like a Lucide icon) that sits adjacent to the title.
- **`children` are passed through to `CardContent`.** This allows for flexible internal layouts (e.g., lists of `Row` or `Chips`) while maintaining consistent padding and styling.

## Gotchas

- **Visual hierarchy dependency:** The component relies on the `text-sm` and `text-muted-foreground` classes on the `CardTitle` to ensure the header doesn't compete visually with the actual data in the `children`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
