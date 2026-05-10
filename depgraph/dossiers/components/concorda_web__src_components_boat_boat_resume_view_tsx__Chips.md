---
node_id: concorda-web::src/components/boat/boat-resume-view.tsx::Chips
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8b6fa62fdff1f30f4230596353da304365db914f94d61f7e0f1e443204a7299d
status: llm_drafted
---

# Chips

## Purpose

A specialized UI helper for rendering arrays of strings as a collection of `Badge` components. It is used within `BoatResumeView` to display categorical data like `positions`, `race_areas`, and `availability`. Use this instead of manual mapping when you need consistent spacing, the `capitalize` utility, or the automatic `<Empty />` state handling.

## Invariants

- **Input is an array of strings.** If `values` is null, undefined, or an empty array, it renders the `<Empty />` component.
- **`capitalize` prop controls CSS.** When `capitalize={true}`, it applies the `"capitalize"` class to the `Badge` to ensure proper casing for raw API strings.
- **Uses `v` as the key.** The component maps over `values` and uses the string value itself as the React `key`.

## Gotchas

- **Key collision risk.** Because the component uses the value `v` as the `key` (line 26), duplicate strings in the input array will cause React reconciliation errors. Ensure input arrays are unique before passing them to `Chips`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
