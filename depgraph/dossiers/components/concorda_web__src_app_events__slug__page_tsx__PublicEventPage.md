---
node_id: concorda-web::src/app/events/[slug]/page.tsx::PublicEventPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 94e2bb07bfe8d899deafa0e09e094995eef4861cd1633f9396d72d82d3ba9048
status: current
---

# PublicEventPage

## Purpose

The `PublicEventPage` is the primary landing page for unauthenticated or authenticated users to view event details and complete registrations. It manages the complex state of a multi-step registration flow, including ticket selection, discount application (both membership-based and code-based), and Stripe payment integration. It is distinct from internal admin views by focusing on the public-facing "registration" lifecycle rather than "event management."

## Invariants

- **Registration state is driven by URL parameters.** The presence of the `reg` search parameter sets the initial `step` to `"confirmation"`.
- **Discount logic is dual-mode.** Membership discounts are auto-applied if `user` is present; code-based discounts require explicit user input and `discountCodeApplied` state.
- **Registration deadline is a hard boundary.** The `isPastDeadline` memo uses the `event.registration_deadline` to prevent registration attempts once the window has closed.
- **Subtotal calculation is reactive.** The `subtotal` and `discountPreview` depend on the current `selectedTickets` and `discounts` state.

## Gotchas

- **Timezone-aware rendering is mandatory.** Per commit `f444b4c`, all backend datetimes (like `registration_deadline`) must be rendered using the organization's timezone via `useConstants().timezone` rather than the browser's local time to avoid confusing users about when registration actually closes.
- **Stripe integration requires a client secret.** The component manages `clientSecret` and `paymentAmount` state; failure to correctly set these during the transition from `select` to `confirmation` will break the payment flow.

## Cross-cutting concerns

- **Auth**: Uses `useAuth()` to determine if a user is eligible for `membership` type discounts.
- **Side effects**: Successful registration via this page triggers the creation of a `Registration` record in the backend, which is the primary driver for event attendance lists.

## External consumers

None known.
