---
node_id: concorda-web::src/app/join/register/page.tsx::RegisterPageContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ca582108b699cb66eb95728f2ee24aa56ea073190345ea3fd3e38642588fab6
status: llm_drafted
---

# RegisterPageContent

## Purpose

The core registration engine for new users, handling multi-step form state, identity creation, and payment integration. It manages the transition between basic user info, boat registration (including optional "skip-later" logic), and Stripe-based membership payments. It is distinct from the login flow as it is a public-facing entry point that must handle both organization-specific and individual registration paths via URL parameters.

## Invariants

- **State-driven multi-step flow**: The `currentStep` state controls the visibility of form sections; UI components must react to this state to ensure a linear user experience.
- **Stripe integration fallback**: The `stripePromise` is initialized via `paymentsApi.getConfig()`. If the API call fails or the key is missing, it must fall back to `process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.
- **URL-driven configuration**: The registration type (organization vs. individual) and membership type are driven by `searchParams` (`type` and `membership`), making the component's behavior dependent on the entry URL.
- **Form data structure**: The `formData` object is a monolithic state object containing everything from identity (email, name) to boat details (length, draft) and privacy preferences (directory opt-ins).

## Gotchas

- **Password visibility/security**: Per commit `bc156d7`, the form includes explicit `showPassword` and `showConfirmPassword` states to manage the visibility of sensitive input fields for better UX/accessibility.
- **Boat registration optionality**: Per commit `bb9b274`, the form supports a "3-col boat row" and "skip-later" logic, meaning the `formData` must be able to handle incomplete or deferred boat metadata without breaking the registration submission.
- **Autocomplete/Accessibility**: Per commit `06075b5`, ensure that any new fields added to the `formData` include proper `name` attributes and autocomplete support to satisfy requirements for modern password managers.

## Cross-cutting concerns

- **Auth**: None (this is a pre-auth registration flow).
- **Websocket**: none
- **Audit**: N/A (registration is a creation event, not a log-entry update).
- **Rate limit**: none
- **Side effects**: Successful registration triggers the creation of a new user identity, which is a prerequisite for all authenticated features (Dashboard, Profile, etc.).

## External consumers

None known.
