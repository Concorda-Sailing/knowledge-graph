---
node_id: concorda-web::src/lib/api.ts::profileApi.upgradeMembership
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 20c02dce96f002c9a3e8bdc787622d4fe39024bdfce9121ef305ecdf09672088
status: llm_drafted
---

# profileApi.upgradeMembership

## Purpose
Client-side wrapper that POSTs to `/api/profile/membership/upgrade` to bump the current user from one Membership-category `TemporalProduct` to another. Returns the refreshed `Profile` so callers can update local state. Used during the post-payment finalize step (and for $0/free plan swaps that skip Stripe). The handler deletes ALL existing Membership-category `PersonProduct` rows for the user and inserts one new one — this is a swap, not an additive grant. Frame any change here as "what does the membership row look like after this returns" — there is exactly one, and it is `new_product`.

## Invariants
- Exactly one `PersonProduct` of category `Membership` exists per user after a successful call.
- Paid plans (`new_product.price > 0`) require a `transaction_id` whose `Transaction` is `status="Completed"`, owned by the same `person_id`, and tied to the same `product_id`. The frontend MUST create the intent first via `paymentsApi.createIntent` and pass the returned id back.
- Free plans (`price == 0`) accept calls with no `transaction_id` (see `switchToFree` at line 118).
- Pro-rated-to-$0 paid plans still go through the `transaction_id` path — the backend records a $0 completed `Transaction` and this endpoint validates it like any other (line 136).
- Returns the full `ProfileRead` (refreshed `Person`); callers pipe it into `onUpdate` to keep upstream state coherent without a refetch.
- Re-selecting the current plan returns 400 ("already on this plan") — UI must hide/disable the active plan's Select button.

## Gotchas
- Three call sites in `membership-upgrade.tsx`, not three different consumers — `switchToFree` (free), `switchProRatedFree` ($0 paid txn), `onPaidSuccess` (Stripe-confirmed). Different preconditions, same endpoint. Don't collapse them without understanding why each branch exists.
- The handler deletes existing Membership `PersonProduct`s before inserting the new one — if the insert fails the user is left with no membership row. There's no transaction wrapper beyond the implicit session; failure mid-`commit` is the loss case. No recent fixes here, but worth knowing before adding side-effects (e.g. audit rows) inside this handler.
- Broadcasts `PERSON_UPDATED` over websocket; any subscriber that gates on membership tier (e.g. co-owner-invite eligibility per `47688ac`) will refresh on the next event.
- Eligibility checks elsewhere (Boat Owner gate for co-owner accept — `47688ac`, `eb382d2`) read from the resulting `PersonProduct`; if you change what category/slug means "Boat Owner," this endpoint is the write path that has to keep producing the right row.

## Cross-cutting concerns
- Auth: `require_auth` — any logged-in member.
- Payments: tightly coupled to `paymentsApi.createIntent` → Stripe confirm → this endpoint. The `transaction_id` is the join key; reordering or skipping the intent step breaks the paid path.
- Websocket: emits `PERSON_UPDATED` on success.
- No rate limiting on this route specifically; relies on global auth limits. A user could in principle spam free↔free swaps.
- No audit log entry written here. Membership history is not preserved — the old `PersonProduct` is hard-deleted.

## External consumers
- Web only (3 call sites in `membership-upgrade.tsx`).
- Expo app: not currently wired (no membership upgrade flow in the iOS app as of last check).
- No webhooks, scheduled jobs, or external integrations consume this directly.

## Open questions
- Should membership changes be auditable? Today there's no record that a user was ever on a different plan. If/when billing disputes arise, the trail is Stripe-side only.
- Should the delete+insert be idempotent under retry? Network failure after delete but before insert leaves the user membership-less; current UI doesn't surface this clearly.
