---
node_id: concorda-web::src/components/finder/hero-card.tsx::HeroCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3a9385498dfaafeafc6e85e99c2289833fbdc5858e0b250761a273875af758e3
status: current
---

# HeroCard

## Purpose

The `HeroCard` is a high-visibility UI component used to showcase primary entities (like a featured boat or a prominent crew member) in the "Finder" views. It differs from standard `Card` or `CrewCard` components by including a large banner area and an overlapping avatar to create a "hero" visual effect. It is intended for top-level display rather than dense list views.

## Invariants

- **`onClick` behavior** — If provided, the card becomes a clickable surface with a `cursor-pointer` and a hover shadow.
- **Event Bubbling Guard** — The `onClick` handler explicitly checks `(e.target as HTMLElement).closest("a, button")` to prevent the card's click event from firing when a user interacts with nested interactive elements like buttons or links.
- **Avatar Fallback** — Supports two modes: `avatarAsImg` (renders a raw `<img>` with a fallback `div`) or a standard `Avatar` component (using Radix-style primitives).
- **Banner Aspect Ratio** — The banner area uses a fixed height (`h-32`) and `object-cover` to ensure visual consistency regardless of the source image dimensions.

## Gotchas

- **Footer Alignment** — Per commit `f36708e`, the card structure requires explicit management of the bottom section to ensure footers (like "Apply" buttons) remain pinned to the bottom and do not shift layout when content varies.
- **Click Interference** — Because the card wraps the entire content area, any interactive element placed inside `children` must be a non-button/non-anchor element, or the `onClick` guard must be strictly respected to prevent accidental triggers.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Used in high-level "Finder" views (e.g., `BoatFinderPanel`, `CrewFinderPanel`) to highlight featured results.

## External consumers

None known.
