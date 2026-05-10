---
node_id: concorda-web::src/components/boat/boat-crew-invite.tsx::parseEmails
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 67c6d986d2a8d41d62db93ecd8b21f630ad8da5ca2f9ccee704959d10d3f6dde
status: current
---

# parseEmails

## Purpose

The `parseEmails` helper converts freeform user input (from a textarea) into a sanitized, unique array of lowercase email addresses. It is used to process bulk invite lists where users might separate addresses using various delimiters like commas, semicolons, or newlines. This is a local utility for the `BoatCrewInvite` component and is distinct from any server-side validation.

## Invariants

- **Input is a raw string.** The function accepts any string, including empty or whitespace-only strings.
- **Returns a unique set.** The output is a `string[]` where every element is unique and lowercase.
- **Regex-based validation.** Only strings matching the pattern `^[^\s@]+@[^\s@]+\.[^\s@]+$` are retained; malformed strings are silently dropped.
- **Delimiter support.** The function splits on whitespace, commas, semicolons, and newlines.

## Gotchas

- **Regex is permissive.** The regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` is a basic sanity check and does not strictly validate the full RFC 5322 standard; it primarily ensures the presence of an `@` and a dot.
- **No error on invalid input.** If a user enters a list of non-email strings, the function returns an empty array `[]` rather than throwing, which may lead to silent failures in the UI if the caller doesn't handle empty lists.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
