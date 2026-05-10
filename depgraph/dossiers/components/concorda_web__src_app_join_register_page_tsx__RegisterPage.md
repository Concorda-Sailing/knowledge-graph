---
node_id: concorda-web::src/app/join/register/page.tsx::RegisterPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b3676845a9ab3da13bd6bf837c0d41a1f06cd70a80327e9f2dfca190e3e5b0c6
status: current
---

# RegisterPage

## Purpose

The multi-step registration entry point for new users. It manages a complex local state machine that transitions through membership type selection, personal information, boat registration, and payment. It is distinct from the standard login flow as it handles the creation of new identities and the integration of Stripe-based payment processing.

## Invariants

- **State-driven UI** — The `currentStep` state controls the visibility of different form sections; changing this state does not persist data to the backend until the final submission.
- **Search-param driven configuration** — The component relies on `useSearchParams` to determine if the user is registering as an `organization` or via a specific `invite` token.
- **Stripe integration** — The `stripePromise` and `paymentClientSecret` are managed locally to handle the transition from form completion to successful transaction.
- **Form data structure** — The `formData` object is a flat structure containing both user identity (email, password) and boat-specific metadata (manufacturer, draft, sail number).

## Gotchas

- **Password visibility toggle** — Per commit `bc156d7`, the form includes a `showPassword` state to toggle visibility of the password and confirm-password fields; ensure any new sensitive field additions follow this pattern for accessibility.
- **Form field attributes** — Per commit `06075b4`, the form uses specific `name` and `autocomplete` attributes to support password managers; do not strip these when adding or refactoring input fields.
- **Boat registration complexity** — Per commit `bb9b274`, the boat registration step includes a "skip-later" capability and a `sail-number` lookup; changes to the `formData` schema must account for these optional/lookup-based fields.

## Cross-cutting concerns

- **Auth**: Creates a new user identity; success triggers the creation of a session/token.
- **Audit**: N/A.
- **Side effects**: Successful registration/payment triggers the creation of a user profile and potentially updates the `boatfinder` registry if boat data is provided.

## External consumers

None known.
