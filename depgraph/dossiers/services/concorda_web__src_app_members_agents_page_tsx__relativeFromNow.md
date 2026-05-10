---
node_id: concorda-web::src/app/members/agents/page.tsx::relativeFromNow
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7038bb7bfa3c619a1c6883fe25a1e53a42260e8a03af5d8891b1dc7b95b76f97
status: llm_drafted
---

# relativeFromNow

## Purpose

Calculates a human-readable relative time string (e.g., "2d ago" or "in 5 days") from an ISO timestamp. It is a pure utility used within the `AgentsPage` to provide temporal context for agent token expiration/creation without requiring a full date-time library.

## Invariants

- **Input is an ISO string.** The function expects a valid date-time string that can be parsed by `new Date()`.
- **Returns a string.** The output is always a string, never `null` or `undefined`.
- **Uses a 30-day month approximation.** For durations longer than 60 days, it calculates months using `Math.round(days / 30)`.
- **Calculates relative to `Date.now()`.** The "now" reference point is established at the moment of execution.

## Gotchas

- **Timezone-agnostic calculation.** Unlike `formatDate` in the same file, this function does not use `formatInOrgTz`. It calculates the delta based on the raw UTC timestamp and the local machine's `Date.now()`, which is sufficient for relative "days ago" logic but may cause slight discrepancies in "today" vs "yesterday" transitions depending on the viewer's local time.
- **Rounding behavior.** The use of `Math.round` for months can cause the label to jump to "in 1 month" or "in 2 months" earlier/later than a calendar-aware library would, due to the fixed 30-day divisor.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
