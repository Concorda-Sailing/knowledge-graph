---
node_id: concorda-web::src/app/members/admin/products/[category]/page.tsx::formatAge
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2f7118b4e55bd6ddb6740681c836b15b1ba63c3f658fb9ae61297271e564d847
status: llm_drafted
---

# formatAge

## Purpose

A helper function to format age range constraints for product display. It converts numeric `min` and `max` values into human-readable strings (e.g., "18–21", "18+", or "≤ 12"). It is used within the `CategoryProductsPage` to provide a clean UI representation of age requirements for different product categories.

## Invariants

- **Input types are numeric or null/undefined.** The function expects `min` and `max` to be numbers or omitted.
- **Returns a string.** Always returns a string, even if both inputs are missing (returns `"Any"`).
- **Uses an en-dash for ranges.** When both `min` and `max` are present, it uses the `–` character (Unicode U+2 way) for the range.

## Gotchas

- **Implicitly handles empty values as "Any".** If both `min` and `max` are `null` or `undefined`, the function returns `"Any"`. This is a fallback for when no age restriction is set.
- **Recent UI refactor dependency.** Per commit `47dfc24`, this function is part of the logic that handles "age fields" for memberships; ensure that any changes to the `formData` structure (which uses `min_age` and `max_age` as strings) are compatible with this function's expectation of numbers.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
