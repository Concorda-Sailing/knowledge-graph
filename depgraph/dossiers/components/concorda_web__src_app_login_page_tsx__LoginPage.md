---
node_id: concorda-web::src/app/login/page.tsx::LoginPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a063900bb29120aa7b0d31fd0c705844039a530e439fca33e3f17e08821201a3
status: current
---

# LoginPage

## Purpose

The primary entry point for user authentication in the web application. It provides the UI for email/password entry, handles local form state, and triggers the `login` method from `useAuth`. It is distinct from the `AuthProvider` (which manages the actual session/token) by focusing purely on the presentation of the login attempt and the rendering of specific error states like rate-limiting or credential failure.

## Invariants

- **Redirects are side-effect driven.** The component does not manually call `router.push` on success; it relies on the `AuthProvider` to detect the successful login and redirect the user to the root path.
- **Error parsing is external.** The `error` state is populated via `parseLoginError(err)`, which translates raw API errors into structured UI-friendly objects (e.g., `invalid_credentials` or `rate_limited`).
- **Form state is local.** `formData` is managed via `useState` within the component and is not synced to any global store until `handleSubmit` is invoked.

## Gotchas

- **Password manager compatibility.** Per commit `06075b5`, the form must maintain proper `name` attributes and autocomplete properties to ensure compatibility with browser-based password managers.
- **Structured lockout UI.** Per commit `86ff361`, the error handling must support "structured login lockouts." This means the UI must check for `error.canResetPassword` to render the `resetHref` link, allowing users to bypass a temporary lock via the password reset flow.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to access the `login` function and `useConstants` to retrieve `orgName` for the branding header.
- **Rate limit**: Displays a specific `ShieldAlert` UI when the error kind is `rate_limited`, providing a link to the reset flow if available.

## External consumers

None known.
