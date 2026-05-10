---
node_id: concorda-web::src/components/regatta-icons.tsx::QualifierBadge
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6683bbc48bc09fca6352b2a41cc123f37cd515d3024941fae3341511a3ddfcc3
status: llm_drafted
---

# QualifierBadge

## Purpose

Renders a visual badge representing a regatta qualifier code. It wraps `IconSquare` to provide a standardized look for racing credentials. Use this instead of raw `IconSquare` when displaying a code to ensure the specific visual shorthand (like the "Q" stripe) is applied consistently.

## Invariants

- **`code` is the lookup key** for the `QUALIFIER_ICON` mapping.
- **`size` defaults to `"md"`** if not explicitly provided.
- **The `Qs` code is a special case** that renders the label as "Q" and applies a visual stripe via the `stripe` prop.
- **Fallback behavior:** If a code is not found in `QUALIFIER_ICON`, it defaults to a `bg-gray-400` background and uses the raw `code` string as the label.

## Gotchas

- **Visual shorthand for `Qs`** — Per the implementation, `code === "Qs"` triggers a specific visual transformation where the display text is shortened to "Q" and the `stripe` prop is enabled. This ensures users recognize the qualifier even when the text is truncated.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
