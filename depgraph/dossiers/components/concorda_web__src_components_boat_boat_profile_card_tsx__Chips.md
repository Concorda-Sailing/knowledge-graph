---
node_id: concorda-web::src/components/boat/boat-profile-card.tsx::Chips
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7f1d8c625e762ec990246c79e7ce864497696cd7a19a1c781b1ce59904766276
status: llm_drafted
---

# Chips

## Purpose

A local helper component used to render a collection of text strings as a group of styled `Badge` elements. It is used within `BoatProfileCard` to display non-hierarchical metadata (like equipment or features) in a compact, wrapped layout. Use this instead of mapping individual `Badge` components manually when you have an array of strings that need consistent spacing and variant styling.

## Invariants

- **`values` must be an array of strings.** If an empty array is passed, it renders an empty `div` with no height/width impact.
- **`variant` is restricted to `"secondary" | "outline"`.**
- **`capitalize` is an optional boolean.** When true, it applies the CSS `capitalize` class to every individual badge in the set.
- **`key` is derived from the value string.** This assumes the input array contains unique strings; duplicate strings will cause React key warnings.

## Gotchas

- **`key={v}` dependency.** Because the key is the value itself, passing a list with duplicate strings (e.g., `['A', 'A']`) will trigger a React key collision warning.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
