---
node_id: concorda-web::src/components/profile/membership-upgrade.tsx::MembershipUpgrade
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b11e2b545bdd46158adec73e40d23c130068dbab07a2a3934388df65e65729d
status: llm_drafted
---

# MembershipUpgrade

## Purpose

Provides the UI for users to upgrade or downgrade their membership tier. It handles the orchestration of fetching available plans via `temporalProductsApi`, initializing Stripe via `paymentsApi.getConfig()`, and executing the upgrade/downgrade via `profileApi.upgradeMembership`. Use this component when a user needs to transition between subscription tiers (e.g., moving from Free to Pro).

## Invariants

- **Requires `profile` object** with a `memberships` array to determine the current tier.
- **Requires `onUpdate` callback** to propagate the updated profile state back to the parent after a successful `upgradeMembership` call.
- **Uses `paymentsApi.createIntent`** to generate a `client_secret` for Stripe-based payments when a paid plan is selected.
- **Filters plans by category** — only products where `p.category === "Membership"` are displayed to the user.

## Gotchas

- **Co-owner requirements:** Per commit `47688ac`, certain membership tiers (specifically Boat Owner) are now required to accept co-owner invites. Changes to the logic here can inadvertently block or allow co-owner onboarding flows.
- **State reset on selection:** Selecting or deselecting a plan resets `clientSecret`, `transactionId`, and `proRatedAmount`. If a user is mid-checkout, changing the selection will clear the payment intent state.
- **Async race conditions:** The component uses multiple `useEffect` hooks to fetch config and create intents. Rapidly switching `selectedSlug` can lead to stale `clientSecret` values if the `paymentsApi.createIntent` call is not properly aborted or guarded.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` and `paymentsApi` which require an authenticated session.
- **Side effects**: Successful upgrades trigger `onUpdate`, which typically triggers a re-fetch of the user profile across the dashboard.

## External consumers

None known.
