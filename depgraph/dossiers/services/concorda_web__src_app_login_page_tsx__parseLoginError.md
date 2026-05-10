---
node_id: concorda-web::src/app/login/page.tsx::parseLoginError
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6c67f6c290ca83507265558cdd19b3f8c4140cebe5b151d9b47e392444ac32fc
status: current
---

# parseLoginError

## Purpose

The `parseLoginError` function transforms raw API error objects into a structured `LoginErrorState` for the login UI. It maps specific backend error codes (`login_rate_limited` and `invalid_credentials`) to human-readable messages and actionable metadata, such as retry timers and password reset availability. This ensures the UI can reactively show specific instructions (e.g., "Too many attempts, try again in X seconds") rather than generic error messages.

## Invariants

- **Input is `unknown`** — The function must safely handle any error type, including standard `Error` objects or unexpected API response shapes.
- **Returns `LoginErrorState`** — The output must strictly follow the union type of `rate_limited`, `invalid_credentials`, or `generic`.
- **`retrySeconds` fallback** — If the API returns a rate limit error without a numeric `retry_after_seconds`, the function defaults to `0`.
- **`canResetPassword` is boolean** — This field is derived from the `password_reset_clears_lockout` property in the API detail to determine if the user should see a reset link.

## Gotchas

- **Strict property checking** — The function relies on `err.detail` being an object with specific keys like `retry_after_seconds` and `remaining_attempts`. If the API changes the naming convention for these fields, the UI will fall back to the `generic` error state and lose the specific context.
- **Type-safety for `message`** — Per the implementation, the function performs `typeof` checks on `d.message` and `d.retry_after_seconds` to prevent runtime crashes if the API returns unexpected types (e.g., a string where a number was expected).

## Cross-cutting concerns

- **Auth**: Directly handles the error state for the `login` action from `useAuth`.
- **Rate limit**: Specifically parses the `login_rate_limited` code to drive the UI's lockout-recovery feedback.
- **Audit**: Per commit `86ff361`, this logic is part of a broader update to support "structured login lockouts" and "error log admin" visibility.

## External consumers

None known.
