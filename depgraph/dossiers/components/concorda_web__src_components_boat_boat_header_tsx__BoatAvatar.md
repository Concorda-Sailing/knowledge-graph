---
node_id: concorda-web::src/components/boat/boat-header.tsx::BoatAvatar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f351cd7ce3eace8d7cb0724c68b578a06471c69ccaed82f47e15548b423d17d5
status: current
---

# BoatAvatar

## Purpose

Renders a circular profile image for a boat, using the `boat.picture_url` property. If no image is provided, it falls back to a centered `Anchor` icon. This is a sub-component of `BoatHeader` and is intended to provide a consistent visual identity for a boat across the platform.

## Invariants

- **Input is a `Boat` object.** The component expects a `boat` prop containing at least `picture_url`, `name`, and `sail_number`.
- **Fallback UI is a centered `Anchor` icon.** If `picture_url` is falsy, it renders a `div` with `bg-muted` and the `Anchor` component.
- **Dimensions are fixed.** The avatar is strictly `w-20 h-20` with `rounded-full` and `object-cover` to ensure consistency in the header layout.
- **Alt text fallback.** The `alt` attribute uses `boat.name` or `boat.sail_number` to ensure accessibility even when the image is missing.

## Gotchas

- **Recent refactor to `BoatHeader` (commit `ad5e998`)** moved the avatar logic into this standalone component to support the new shared header pattern. Ensure any changes to the avatar's visual style (like size or rounding) are coordinated with the `BoatHeader` layout to prevent layout shifts in the banner area.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
