---
node_id: concorda-web::src/app/members/regattas/page.tsx::addMinutesHHMM
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f7fea8d80ce2ffb750908078b0490d7f13d05e8f6b5cde380ed0063e341777bd
status: current
---

# addMinutesHHMM

## Purpose

A utility for time arithmetic that adds or subtracts minutes from a time string. It is used to shift the time displayed on regatta cards and schedules, specifically for adjusting start times or offsets. It is distinct from full date manipulation as it only operates on the `HH:MM` component and wraps around the 24-hour clock.

## Invariants

- **Input is a `HH:MM` string.** The function expects a string in the format `"HH:MM"` (e.g., `"14:30"`).
- **Output is a zero-padded `HH:MM` string.** The result is always a 5-character string (e.g., `"09:05"` or `"23:59"`).
- **Handles 24-hour wrap-around.** The modulo operator `% (24 * 60)` ensures that adding minutes that push past midnight results in a valid time on the next day (e.g., adding 60 minutes to `"23:30"` returns `"00:30"`).
- **Returns empty string on invalid input.** If the input is empty or the split results in `NaN`, it returns `""` rather than throwing.

## Gotchas

- **Modulo behavior for negative values.** The function uses `total < 0 ? total + 24 * 60 : total` to handle subtraction. This ensures that subtracting minutes from a time (e.g., for a countdown or offset) doesn't result in a negative time string, which would break the `padStart` logic.
- **Implicitly assumes 24-hour format.** The logic relies on the input being a 24-hour clock format; passing an AM/PM string will result in `NaN` and return an empty string.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Used for time-offset calculations in the regatta calendar/schedule views.

## External consumers

None known.
