---
node_id: concorda-web::src/lib/api.ts::authApi.checkEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a96d64c5fd5ce0a7a375b94cdda31638fef52e87036199bd1205d740fec68c59
status: llm_drafted
---

# authApi.checkEmail

## Purpose

Checks if a specific email address is already registered in the system. This is a read-only GET request used primarily during the registration flow to provide immediate feedback to users before they submit a full registration payload.

## Invariants

- **HTTP Method is GET** — The email is passed as a URL-encoded query parameter (`?email=...`).
- **Returns a boolean object** — The response shape is strictly `{ available: boolean }`.
- **Input must be URI encoded** — The email string must be passed through `encodeURIComponent` to prevent malformed requests if the email contains special characters.

## Gotchas

- **Registration flow dependency** — This is used by `RegisterPageContent` in `src/app/join/register/page.tsx` to gate the registration submission.
- **Case sensitivity/Normalization** — While the API handles the check, ensure the UI doesn't inadvertently mask issues by normalizing input in a way that differs from the backend's lookup logic.

## Cross-cutting concerns

- **Auth**: This is a public-facing check; it does not require a bearer token or `fetchApiAuthenticated`.
- **Side effects**: None.

## External consumers

None known.
