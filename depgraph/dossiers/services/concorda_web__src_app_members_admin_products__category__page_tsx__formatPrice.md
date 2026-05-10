---
node_id: concorda-web::src/app/members/admin/products/[category]/page.tsx::formatPrice
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d834e6647ccccc752c6dfbc43a64cbcda22d4ca48ec29eb0de14470f1c243c5c
status: llm_drafted
---

# formatPrice

## Purpose

Converts numeric or string-based price values into human-readable currency strings for the admin product management interface. It distinguishes between a zero value (which returns "Free") and a positive numeric value (which returns a formatted USD string). Use this instead of manual template literals when displaying product prices in the admin category tables to ensure consistent "Free" labeling.

## Invariants

- **Input type is permissive**: Accepts `number | string` to handle both raw numeric data and stringified inputs from form state.
- **Zero is "Free"**: A value of `0` (or a string `"0"`) returns the literal string `"Free"`.
- **Fixed precision**: Positive values are always formatted with exactly two decimal places using `.toFixed(2)`.
- **USD Prefix**: All non-zero prices are prefixed with a single `$` symbol.

## Gotchas

- **Type coercion**: Because it uses `Number(price)`, passing non-numeric strings that cannot be coerced (e.g., an empty string or invalid text) will result in `NaN` being passed to `.toFixed`, which will throw a `RangeError`. 

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
