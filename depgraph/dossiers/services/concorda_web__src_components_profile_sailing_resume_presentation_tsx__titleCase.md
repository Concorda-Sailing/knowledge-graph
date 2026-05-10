---
node_id: concorda-web::src/components/profile/sailing-resume-presentation.tsx::titleCase
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9f330db006e8468a893095b2c6290a7b4a66c65bfe51dbfea5fa69d88fa34aee
status: current
---

# titleCase

## Purpose

The `titleCase` helper converts strings containing underscores or hyphens into a human-readable format. It is specifically used to format roles (e.g., "skipper_of_boat" becomes "Skipper of boat") within the `EntryList` component to ensure consistent presentation in the sailing resume. Use this when you need to transform machine-readable slugs into display-ready text for the profile view.

## Invariants

- **Input is a string.** It expects a single string argument.
- **Handles delimiters via regex.** It replaces `_` and `-` with spaces before splitting into words.
- **Preserves short words.** Words with a length of 2 or fewer characters are converted to uppercase (e.g., "of" becomes "OF"), while longer words use standard sentence casing.
- **Trims whitespace.** Leading and trailing whitespace is removed before processing.

## Gotchas

- **Case sensitivity for short words.** Because the function forces words $\le 2$ characters to uppercase, a role like "of" becomes "OF". This may look visually jarring in certain sentence-heavy contexts.
- **Implicit behavior for single-character words.** A single-letter word (like "a") will be converted to uppercase ("A").

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Affects the visual presentation of the `SailingResumePresentation` component.

## External consumers

None known.
