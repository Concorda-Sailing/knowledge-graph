---
node_id: concorda-web::src/app/verify-email/page.tsx::VerifyEmailContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 337df289acf45e762e87d2641276d8293a354f190e3842cbd27ca177b1f92a7a
status: current
---

# VerifyEmailContent

## Purpose

The core UI component for the email verification landing page. It extracts the `token` from the URL search parameters and triggers an asynchronous verification request to the backend. It manages the visual state transitions between `loading`, `success`, `already` (already verified), and `error` to provide user feedback during the onboarding flow.

## Invariants

- **Token extraction is mandatory.** The component relies on `useSearchParams` to retrieve the `token` string; if the token is missing, it immediately transitions to an error state.
- **Uses `fetchApi` for the request.** The verification call must go through the standard API wrapper to ensure consistent handling of base URLs and potential interceptors.
- **Endpoint contract.** Expects a JSON response with a `{ message: string }` shape.
- **Status-driven UI.** The component uses a strict union type for status (`"loading" | "success" | "already" | "error"`) to drive the rendering of specific Lucide icons and text.

## Gotchas

- **URL encoding requirement.** The token is passed via a query parameter; the implementation uses `encodeURIComponent(token)` to prevent malformed requests if the token contains special characters.
- **Single-use nature.** Per the logic in the `success` and `already` states, the user is directed to `/login` after verification. This is a one-way flow and does not support re-verifying a failed attempt without a new token generation.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi` to hit the `/api/auth/verify-email` endpoint.
- **Audit**: N/A.
- **Side effects**: Successful verification is a prerequisite for the user to access authenticated routes (e.g., the dashboard or boatfinder).

## External consumers

None known.
