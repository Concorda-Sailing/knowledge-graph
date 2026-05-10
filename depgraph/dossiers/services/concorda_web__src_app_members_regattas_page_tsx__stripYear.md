---
node_id: concorda-web::src/app/members/regattas/page.tsx::stripYear
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 30515b02d95de97788c13023d8adb826c6f19c841a6efb158b69496446895687
status: current
---

# stripYear

## Purpose

The `stripYear` function cleans up regatta names by removing trailing or leading year identifiers (e.g., "Regatta 2024" becomes "Regatta"). It is a formatting utility used to ensure that the UI remains clean and consistent when displaying regatta titles in lists or headers. It also performs automatic title-casing if the input string is provided in all-caps.

## Invariants

- **Input is a string.** The function expects a `name` string.
- **Regex targets 4-digit years.** It specifically looks for the patterns `19xx` or `20xx` surrounded by whitespace to avoid stripping numbers that are part of the actual name.
- **Returns a trimmed string.** The result is always `.trim()`ed to remove any whitespace left behind by the regex replacement.
- **Title-casing is conditional.** The function only applies title-case logic if the `noYear` result is entirely uppercase and longer than 3 characters.

## Gotchas

- **Regex is narrow.** The regex `/\s*\b(19|20)\d{2}\b\s*/g` only targets years starting with 19 or 20. If a regatta name includes a different century or a non-year number that matches this pattern, it will be stripped.
- **Title-casing side effect.** Because the function forces title-case on all-caps strings, it may inadvertently change the casing of names that were intentionally uppercase for reasons other than being a "year-suffixed" name.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Used in the rendering of regatta lists and headers within the `RegattasPage` component.

## External consumers

None known.
