---
node_id: concorda-web::src/app/join/page.tsx::formatAge
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4d29378b3114778c806f03f04a4a229a344086b800a8d6e8407b79de1b67abed
status: current
---

# formatAge

## Purpose

A pure utility function for formatting age range strings for membership tiers. It converts numeric `min` and `max` bounds into human-readable strings (e.g., "Ages 18–25", "Ages 12+", or "Ages 10 & under"). It is used exclusively within the `JoinPage` to render membership tier details.

## Invariants

- **Input types**: Accepts optional `number` arguments for `min` and `max`.
- **Return type**: Returns a `string` if bounds are provided, or `null` if no bounds are present.
- **String format**: Uses an en-dash (`–`) for ranges (e.g., `Ages ${min}–${max}`) to maintain professional typography in the UI.

## Gotchas

- **Null/Undefined handling**: The function relies on explicit `null` checks (`min != null`) rather than truthiness to allow `0` as a valid age. If a developer changes this to a simple truthy check (`if (min)`), an age of `0` would incorrectly return `null`.
- **UI/Data mismatch**: Per commit `47dfc24`, this function was added alongside "age fields" in the membership data structure. Ensure that the `min`/`max` values passed from the `temporalProductsApi` are actual numbers and not strings, or the output will be malformed.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
