---
node_id: concorda-web::src/components/payment-form.tsx::PaymentForm
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 11c3682f524ab45bf73f5f59b01eee9d12209c15ec01f45a7c217a45d6dc4479
status: llm_drafted
---

# PaymentForm

## Purpose

A specialized Stripe-powered form component used to finalize transactions, specifically for registration flows. It wraps the `PaymentElement` and handles the asynchronous transition from a successful Stripe payment to the execution of a parent-provided `onSuccess` callback. Use this when a user needs to pay a specific amount (e.g., for an event or membership) to complete a multi-step registration process.

## Invariants

- **Requires `useStripe` and `useElements` context.** This component must be rendered within a `Elements` provider to function.
- **`amount` must be a positive number.** The UI explicitly formats this as a currency string (e.g., `$10.00`).
- **`onSuccess` is the primary completion trigger.** The component handles the Stripe `confirmPayment` call, but the actual business logic (like database updates) is deferred to the `onSuccess` prop.
- **`billingDetails` is optional.** If provided, it is passed into the `payment_method_data` to ensure the payment is tied to specific user/billing info.

## Gotchas

- **Error handling is dual-layered.** The component catches both Stripe-level errors (via `stripe.confirmPayment`) and errors thrown by the `onSuccess` callback itself. If `onSuccess` fails, the error is caught and passed to `onError` to prevent the registration flow from hanging in a "processing" state.
- **`redirect: "if_required"` behavior.** The component is configured to handle redirects only if the payment method requires them (like 3D Secure). If the payment method is instant, the flow remains on the current page to execute `onSuccess`.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Completion of this form is the final step in the "registration system" mentioned in commit `01bc16e`.

## External consumers

None known.
