---
node_id: concorda-test::tests/auth/boat-owner-registration.spec.ts::test@19
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fc216691216c580a3183c7980fa9c5c43fd0534f0134c07c183eaf94302ac24c
status: llm_drafted
---

# user can pay $30 with Stripe test card and complete signup

## Purpose

Verifies the end-to-end registration flow for a "Boat Owner" tier, specifically ensuring that a user can successfully complete the Stripe payment process. This test validates the transition from personal info entry to boat detail entry, and finally the interaction with the Stripe Elements payment iframe. It is distinct from standard registration tests because it requires a functional Stripe integration and a specific membership selection to trigger the payment gate.

## Invariants

- **Requires `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`** — The test stack must pass this via Dockerfile/Compose, otherwise the test skips via the `isStripeAbsent` check.
- **Membership selection is mandatory** — The test must explicitly call `register.selectMembershipByName(/boat owner/i)` to reach the payment step.
- **Boat details requirement** — Only the `sailNumber` is required to advance past the boat details stage.
- **Timeout is 90s** — Due to the complexity of iframe-based Stripe interactions and potential network latency, the test uses a high `setTimeout(90_000)`.

## Gotchas

- **Stripe iframe instability** — The structure of Stripe iframes changes between releases (e.g., switching between `accessory-target` and `easel` frames). Recent commits like `a9082c5` and `d68b62e` show a pattern of needing to probe all `iframe[src*="stripe.com"]` frames to find the one containing the card form.
- **Input interaction failures** — Standard `.fill()` often fails or drops keys in Stripe fields. Per commit `4cd81bc`, the strategy was to revert to `.fill()` for certain fields, but generally, the test relies on a combination of `focus()` and `keyboard.type` or specific per-key settling to ensure the UI registers the input.
- **UI/Selector drift** — The test is sensitive to the order of operations (e.g., clicking the "Card" tab to expand the form). Commit `fe19eb9` highlights the need to click the Terms of Service (TOS) or other UI elements to ensure the Stripe elements are actually enabled and visible before attempting to type.

## Cross-cutting concerns

- **Auth**: Completes the registration flow to establish a new user identity.
- **Side effects**: Successfully completing this test creates a new user in the database with a `boat-owner` membership and a corresponding `Boat` record.

## External consumers

None known.
