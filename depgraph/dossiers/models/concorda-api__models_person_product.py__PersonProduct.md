---
node_id: concorda-api::models/person_product.py::PersonProduct
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 58f5a5aa153b0333d24628081dc2ff257e556b663afb3fead0f893a64203e21d
status: current
---

# PersonProduct

## Purpose

`PersonProduct` is the join row that materializes "this person owns this SKU" — the bridge between a `Person` and a `TemporalProduct`. It carries no data of its own beyond the two FKs; all entitlement semantics live on the linked `TemporalProduct` via its `grants_*` flags. A future Claude reasoning about "does this user have membership X / boat management / event discount?" should picture the canonical query: join `PersonProduct` to `TemporalProduct`, filter on the relevant `grants_*` flag (see `services/approvals.py:21-31` for the textbook shape). It is also the only writeable artifact of a successful membership purchase — the row is created at the end of `/api/profile/membership/upgrade` after a Completed Transaction is verified.

## Invariants

- **At most one Membership-category `PersonProduct` per person at any time.** Enforced procedurally by `routers/profile.py:1373-1388`: the upgrade flow loads every existing Membership-category row for the user and deletes them before inserting the new one. There is no DB-level constraint encoding this — only app code.
- **`(person_id, product_id)` is unique** (DB-level `ix_person_products_person_product`). The same SKU cannot be re-granted to the same person; `/membership/upgrade` rejects it with 400 "already on this plan" before reaching the unique violation.
- **Both FKs are NOT NULL.** A row without a person or product is meaningless.
- **`type="PersonProduct"` is hard-coded in `__init__`.** Single-table polymorphism inherited from `BaseModel`; never override.
- **A Membership-category row implies a paid (or $0-pro-rated) Completed Transaction exists** for any plan with `price > 0`. The transaction is the receipt; the PersonProduct is the entitlement. The two are coupled but not FK-linked — don't assume you can recover the Transaction from the PersonProduct.

## Gotchas

- **The "hard switch" on upgrade is destructive and non-transactional in spirit.** `upgrade_membership` deletes all Membership-category PersonProducts, then inserts the new one, then commits. If anything between the delete and the commit raises, the user can be left with no membership at all. The whole block runs in one SQLAlchemy session so a single `commit()` covers both, but be wary of inserting any I/O (Stripe call, broadcast) between the delete and insert.
- **No expiry mechanism on the PersonProduct itself.** Expiration is implicit via the linked `TemporalProduct.end_date` / `year` — but nothing actively prunes stale rows when a year rolls over. Today the entitlement check is "row exists AND product flag is set"; it does not consult `end_date`. A user with a 2025 Boat Owner PersonProduct still passes `_has_boat_management` in 2026 unless someone manually deletes the row.
- **Tier confusion if upgrade fails mid-flight.** If the delete commits but the insert fails, the user loses their old tier without gaining the new. The current code does both inside one transaction, so this is mostly theoretical — but code that adds steps between them needs to preserve atomicity.
- **Already-on-this-plan check happens before the wipe.** The 400 fires when the new product matches an existing row, so callers can't use `/membership/upgrade` as an idempotent renewal. Year-rollover flows need a different path.
- **Co-Owner tier collapse.** PersonProduct rows from before the Boat Owner / Co-Owner merge may still reference legacy SKUs; treat any per-row tier inference as suspect on pre-2026 data.

## Cross-cutting concerns

- **Boat management entitlement** — `services/approvals.py:21-31` `_has_boat_management()` is the canonical check, gating `boat_coowner_invite` accept (`approvals.py:93-103`) per `rule::coowner::eligibility_at_accept`. The check fires at vote/accept time, not invite-send.
- **Membership upgrade flow** — `routers/profile.py:1333-1393` is the only writer in normal user flow. Admin flows in `routers/admin.py` (lines 268, 342, 430, 520) and registration (`routers/auth.py:681`) also create rows.
- **Stripe transaction coupling** — the `transaction_id` from the Stripe-completed PaymentIntent is the gating credential for paid plans. The Transaction's `product_id` must match the new TemporalProduct, status must be "Completed", and `person_id` must match the upgrader.
- **`grants_event_discount` redemption** — `routers/payments.py:151-170` joins through PersonProduct to determine whether a user holds a discount-bearing membership.
- **Websocket** — `/membership/upgrade` broadcasts `PERSON_UPDATED` after the swap; admin-side mutations to PersonProduct are silent and rely on SPA refetch.
- **Audit / soft-delete** — none. PersonProduct uses hard deletes; there is no history of past memberships once the row is wiped.

## External consumers

- **Concorda iOS app** — indirectly, via `/api/auth/me` and profile reads that surface `grants_*` derived from PersonProduct joins.
- **Stripe** — no direct consumer, but the upgrade contract assumes Stripe webhook has flipped the matching Transaction to Completed before the client calls `/membership/upgrade`.
- **MBSA legacy member CSV importer** — bulk-creates PersonProduct rows during onboarding (`routers/admin.py:520`).
- **No external webhooks or scheduled jobs** read or mutate this table.

## Open questions

- **Should there be an explicit expiry / end-of-membership sweep?** Today a 2025 PersonProduct silently keeps granting in 2026 because the entitlement check ignores `TemporalProduct.end_date`. Either the check needs a date filter, or a year-rollover job needs to prune.
- **Should the Membership-category uniqueness constraint be DB-level?** A partial UNIQUE on `(person_id)` filtered by `TemporalProduct.category="Membership"` isn't natively expressible without denormalization — but the procedural enforcement is racy under concurrent upgrades.
- **Upgrade idempotency / renewal semantics.** The 400 on already-on-this-plan blocks a no-op renewal. When year-rollover happens, what's the canonical re-purchase path?
- **Soft-delete for membership history?** Knowing "Logan was a Boat Owner in 2024" requires the Transaction trail today; PersonProduct itself carries no history.
