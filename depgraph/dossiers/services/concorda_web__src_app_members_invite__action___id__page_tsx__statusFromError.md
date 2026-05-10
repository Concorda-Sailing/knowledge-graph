---
node_id: concorda-web::src/app/members/invite/[action]/[id]/page.tsx::statusFromError
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cb6af6b87da6c91cebaca4c03565ad4055c72dff1d9054e84b3c5293c6bb577d
status: current
---

# statusFromError

## Purpose

Maps raw error objects or strings from the `inviteResponseApi` into a structured `Status` type. It translates specific error messages (e.g., "expired", "already", "forbidden") into semantic UI states so the `InviteResponsePage` can display a meaningful outcome to the user rather than a generic error.

## Invariants

- **Input is a `unknown` error type.** It must handle both `Error` instances and primitive strings to avoid runtime crashes during parsing.
- **Returns a `Status` type.** The output is strictly one of the predefined status strings (e.g., `"expired"`, `"already"`, `"not-eligible"`, or `"error"`).
- **Case-insensitive matching.** The function converts the error message to lowercase before performing `.includes()` checks to ensure robust matching against varying backend error formats.

## Gotchas

- **React StrictMode double-fire.** Per commit `ef5f386`, the page uses a `submittedRef` to prevent the effect from firing twice in development. Without this guard, the first execution records the vote, and the second execution hits a 409 "already voted" error, causing the UI to incorrectly show an "already" status instead of a successful one.
- **String-based pattern matching.** The function relies on specific substrings like `"not a voter"` or `"403"` to identify eligibility errors. If the backend error message wording changes, this function will fail to categorize the error, defaulting to a generic `"error"` status.

## Cross-cutting concerns

- **Auth**: Relies on `useAuth` to ensure the user is authenticated before the effect triggers the API call.
- **Side effects**: Triggers the `inviteResponseApi.respond` call, which updates the state of the invitation in the database.

## External consumers

None known.

## Open questions

- Should the error mapping logic be moved to a centralized error-handling utility if other invite-related pages begin requiring similar semantic mapping?
