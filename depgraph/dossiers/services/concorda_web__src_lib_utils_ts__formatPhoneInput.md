---
node_id: concorda-web::src/lib/utils.ts::formatPhoneInput
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2616ece354f9c9e1e7a0f4269307c815ab6eac9e16f03a65223a9f7a449d5981
status: current
---

# formatPhoneInput

## Purpose

The `formatPhoneInput` function provides progressive formatting for phone numbers as a user types. It strips all non-digit characters and applies a `(XXX) XXX-XXXX` pattern. It is intended for use in text inputs to provide visual feedback during registration or profile updates, ensuring the user sees a standard North American format.

## Invariants

- **Input is a raw string.** The function accepts any string and immediately strips non-digits via `\D`.
- **Output is a formatted string.** The return value follows the pattern `(XXX) XXX-XXXX` once the digit count is sufficient.
- **Progressive formatting.** The function returns partial strings (e.g., `(123`) for short inputs to allow for seamless typing.

## Gotchas

- **US/Canada prefix handling.** The function logic for 11 digits (starting with "1") is present in the source but the `formatPhoneInput` implementation itself does not use the `digits.length === 11` logic found in the surrounding code block (lines 17-18). This suggests a discrepancy between the intended logic for handling country codes and the actual progressive formatting applied to the `value` argument.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: Used in `RegisterPageContent` (registration flow) and `UserDialog` (admin user management).

## External consumers

None known.
