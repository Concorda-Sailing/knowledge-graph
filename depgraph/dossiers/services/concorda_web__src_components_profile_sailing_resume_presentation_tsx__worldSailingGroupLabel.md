---
node_id: concorda-web::src/components/profile/sailing-resume-presentation.tsx::worldSailingGroupLabel
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b4c6bba14ef1ddf49190230fa33606aa4427e944f267e75c11f3affe9b6952f
status: current
---

# worldSailingGroupLabel

## Purpose

Maps internal numeric or string-based sailing group identifiers to human-readable, localized labels. It serves as a translation layer between the raw database values (e.g., `"1"`, `"3"`, or `"unclassified"`) and the descriptive prose used in the user's sailing resume. Use this function when you need to display a user's competitive classification level.

## Invariants

- **Input is a string.** The function expects a string representation of a value (e.g., `"1"`, `"3"`, or `"unclassified"`).
- **Returns a string.** It always returns a human-readable label or the original input if no match is found.
- **Default behavior is passthrough.** If the input does not match a known case, the function returns the input string unchanged.

## Gotchas

- **Implicit mapping for non-numeric values.** While the primary cases are `"1"` and `"3"`, the function is designed to handle the `"unclassified"` string explicitly.
- **Manual fallback.** If the value is not `"1"`, `"3"`, or `"unclassified"`, the function returns the raw value. This relies on the caller or the `titleCase` helper to ensure the raw value is formatted correctly for the UI.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Affects the visual presentation of the user's competitive level in the `SailingResumePresentation` component.

## External consumers

None known.
