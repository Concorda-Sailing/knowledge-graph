---
node_id: concorda-web::src/components/boat/boat-profile-card.tsx::BoatProfileCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 23f8696d22dd9d3749408fc34bb7d5842f31454114acb62adb5d2e7d03c96889
status: current
---

# BoatProfileCard

## Purpose

Displays a structured summary of a boat's physical specifications and the owner's operational preferences. It acts as the visual bridge between the raw `BoatLike` (physical data) and `BoatResume` (operational/social data) types. Use this component when you need to present a high-density "at-a-glance" profile rather than a full-page detailed view.

## Invariants

- **Input structure** — Requires both a `boat` object (for physical specs like `length` and `manufacturer`) and a `resume` object (for social/operational data like `availability` and `drinking`).
- **Whitespace preservation** — The `resume.about` section uses `whitespace-pre-line` to ensure owner-written descriptions maintain intended formatting.
- **Conditional rendering** — Sections like "Roles Needed" or "Race Areas" only render if the underlying arrays are non-empty to prevent empty `InfoCard` containers from cluttering the UI.
- **Type coercion** — The `typical_crew_complement` is explicitly cast to a `String` to ensure the `Row` component handles numeric inputs without crashing.

## Gotchas

- **Recent introduction** — This component was added in commit `b92cb2a` to provide rich profile content; ensure any new fields added to the `BoatLike` or `BoatResume` types are checked for compatibility with this layout.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: N/A

## External consumers

None known.
