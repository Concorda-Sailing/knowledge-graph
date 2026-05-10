---
node_id: concorda-web::src/components/ui/skeleton.tsx::Skeleton
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e5f316484541b75cf0f609e2a5b653df78c89fc3e03b29953fe69f72bf16fdb4
status: llm_drafted
---

# Skeleton

## Purpose

A low-level UI primitive used to display a placeholder-loading state. It renders a div with a pulse animation and a muted background color to indicate that content is loading. Use this instead of a generic spinner when you want to maintain the layout structure of a component (like a card or image) during data fetching.

## Invariants

- **Base classes are fixed.** It always includes `animate-pulse` and `rounded-md bg-muted` via the `cn` utility.
- **Accepts standard HTML attributes.** It spreads `...props` onto the underlying `div`, allowing for `className`, `style`, or `aria-label` to be passed through.
- **Returns a single `div` element.**

## Gotchas

- **Visual consistency.** Because it uses `bg-muted`, the skeleton's visibility depends on the theme's muted color. If the background color is too high-contrast, it may break the "subtle" intent of a loading state.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
