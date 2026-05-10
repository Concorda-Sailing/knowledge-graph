---
node_id: concorda-web::src/components/dashboard/crew-card/crew-mini-card.tsx::CrewMiniCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0ad492857db65c044e0adba9a05f366b936b5d1ed669ef3fd761e21c61c1af15
status: current
---

# CrewMiniCard

## Purpose

A specialized, compact UI primitive for displaying a single crew member's identity and status. It is designed to be used within larger layouts like `AvailableSection` to show a summary of a person (avatar, name, and optional badges) without the full footprint of a standard profile card. It supports an optional `onClick` for navigation and an `actions` slot for contextual buttons (like "Invite" or "Resend") that must not trigger the card's primary click event.

## Invariants

- **Event Bubbling Control**: The `actions` slot and the `onRemove` button both explicitly call `e.stopPropagation()` to prevent triggering the card's `onClick` handler.
- **Visual Fallbacks**: If `person_picture_url` is missing, the component renders an `AvatarFallback` using the first letter of the first and last names.
- **Accessibility**: If `onClick` is provided, the container is assigned `role="button"` and `cursor-pointer`.
- **Layout Constraints**: The name and subtitle fields use `truncate` and `max-w-[140px]` to ensure the card maintains a consistent, predictable width in grid layouts.

## Gotchas

- **Aria-label Fallback**: Per commit `6ef00f2`, the `aria-label` for the remove button must provide a fallback if `person_first_name` is undefined to avoid an empty or broken accessibility experience for screen readers.
- **Initials Logic**: The initials generation logic `(member.person_first_name ?? "")[0]` assumes the name strings are accessible; if the name is null/undefined, it defaults to an empty string rather than throwing, but requires the `?? ""` guard to prevent runtime errors.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: Used as a building block for the `AvailableSection` component.

## External consumers

None known.
