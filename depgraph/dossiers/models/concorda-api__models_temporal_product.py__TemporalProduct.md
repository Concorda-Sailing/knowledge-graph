---
node_id: concorda-api::models/temporal_product.py::TemporalProduct
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a1d57d27639ae4efb0b76aa0e51efe7140d7d6b18c912701c23394c5ef19ffe3
status: llm_drafted
---

# TemporalProduct

## Purpose

`TemporalProduct` is the time-bounded SKU table — primarily memberships scoped to a calendar year, but also event-scoped registration products when `category == "Event"` and `event_id` is set. It is the counterpart to `Product` (which sells discrete event tickets without a date window). A row defines the price, the start/end window, and crucially the `grants_*` feature-flag bundle that turns a paid `PersonProduct` association into runtime entitlements (boat management, crewfinder access, event discount eligibility, prize eligibility). When a future Claude is touching membership pricing, year rollover, eligibility rules, or anything that asks "does this user have membership X?", this is the model.

## Invariants

- **`(slug, year)` is treated as the unique business key.** Both `create_temporal_product` and `update_temporal_product` (`routers/temporal_products.py:255-265, 301-315`) reject duplicates explicitly. There's no DB-level UNIQUE — it's enforced in app code only. Don't bypass via raw inserts.
- **`category` is one of `"Membership"` or `"Event"`** (per `TemporalProductCategory`, stored as `String(20)`). The string values are capitalized — `"Membership"`, not `"membership"` — and many filters (`routers/profile.py:1347`, `routers/payments.py:167, 437`) compare against the capitalized literal directly.
- **`year` and `start_date`/`end_date` must agree.** Auto-population in `create_temporal_product` and `_year_to_dates` defaults to Jan 1 – Dec 31 of `year`. Pro-ration math (`_pro_rated_value` in `payments.py:446`) silently falls back to full price if dates are missing or invalid.
- **`event_id` is only meaningful when `category == "Event"`.** For memberships it's null; the FK exists for event-scoped temporal products (early-bird windows tied to a specific Event).
- **`type="TemporalProduct"` is hard-coded in `__init__`.** The model uses single-table-style polymorphism via `BaseModel.type`; never override the type.
- **`grants_*` flags are the entitlement contract.** A user has a capability iff they have a `PersonProduct` whose `product_id` points at a TemporalProduct with the corresponding flag set. Adding a new capability gate? Add a new `grants_*` column, don't reuse one.
- **Tickets are NOT TemporalProducts.** Event-ticket purchases live in `Product` + `Transaction.product_type="Product"`. Don't conflate the two.

## Gotchas

- **`/temporal-products/available` used to lazy-copy from prior years for unauthenticated callers.** That was an unauthenticated DB write surface, closed in `ec53704` (`fix(security): rate limits on auth endpoints; close unauth DB write`). Auto-copy now only fires from the admin `list_temporal_products` path. Don't re-add lazy-copy to the public endpoint.
- **Pro-ration applies only to authenticated upgrades, never new signups.** `routers/payments.py:355-358` keys off `current_user is None`. `3750138` (`fix(payments): allow unauthenticated new-signup checkout, only require auth for upgrades`) is the relevant fix — checkout-before-account is a real flow.
- **A pro-rated $0 charge still creates a Completed Transaction.** `payments.py:365-383`. The upgrade endpoint (`profile.py:1361-1371`) requires a Completed Transaction for any paid plan, so the $0 receipt is load-bearing — don't optimize it away.
- **`upgrade_membership` deletes ALL existing Membership-category PersonProducts before inserting the new one** (`profile.py:1373-1388`). This is a hard switch, not an additive grant. A user can only carry one Membership PersonProduct at a time.
- **Boat Owner gating is enforced at vote/accept time, not invite-send.** `4c7de14` and `aabe8d0` deliberately moved the `_has_boat_management` check (`services/approvals.py:21-31, 93-103`) to the moment the invitee accepts. An invite can be created and sent to a non-Boat-Owner; the user is nudged to upgrade and the vote re-evaluates. See `rule::coowner::eligibility_at_accept` in logigraph.
- **`grants_*` are checked dynamically on every gated action.** A revoked/expired membership instantly removes capabilities — there is no cached entitlement. If you add caching, you own invalidation.
- **Boat Owner / Co-Owner were merged.** `7e649cf` collapsed the two into a single Boat Owner membership. Code that branches on a "co-owner" tier is stale.

## Cross-cutting concerns

- **Auth.** Public read at `GET /temporal-products/available`. All mutating + admin reads gated by `admin.memberships.view` / `admin.memberships.manage`. `/membership/upgrade` requires login but no role.
- **`grants_boat_management` fan-out.** Used in `services/approvals.py:27` (vote-time gate for `boat_coowner_invite`), `routers/persons.py:64` (eligibility surfacing for invite UI), `routers/profile.py:647` (own-boat owner queries / upgrade nudge), `routers/auth.py:1250` (auth response payload exposing the flag to the SPA). Flipping this flag on a tier silently changes behavior in four places.
- **`grants_event_discount`.** Drives `EventDiscount` redemption logic in `routers/payments.py:151-170` — both "specific membership required" and "any non-guest membership" branches join through TemporalProduct.
- **`grants_crewfinder` / `grants_prize_eligibility`** are declared and migrated but currently have minimal enforcement in routers — they are the reservation for crewfinder visibility and prize ranking. Don't assume they're inert; check call sites before changing semantics.
- **Stripe/Transaction coupling.** Membership purchases create `Transaction` rows with `product_type="TemporalProduct"`. The Stripe webhook (`payments.py:460+`) marks them Completed; `/membership/upgrade` then reads them.
- **No websocket broadcast on TemporalProduct mutations.** `/membership/upgrade` does broadcast `PERSON_UPDATED`, but admin CRUD on the catalog itself is silent — the SPA refetches.
- **Logigraph rules.** None currently target this node directly. Pricing/pro-ration math is pure code, not a rule yet.

## External consumers

- **Concorda iOS app** — reads `/temporal-products/available` for the membership picker during signup/upgrade.
- **Stripe** — receives `product_id` / `product_slug` / `product_name` in PaymentIntent metadata; if you rename slugs after a charge, the metadata trail goes stale (historical only — no functional dependency).
- **MBSA legacy member CSV importer** (`453fd22`) — assumes a `boat-owner-{year}` slug shape exists for the import target year.
- **No external webhooks or scheduled jobs** consume TemporalProduct directly.

## Open questions

- **Should `(slug, year)` become a real DB UNIQUE constraint?** Currently app-enforced only, race-prone under concurrent admin writes.
- **`grants_crewfinder` and `grants_prize_eligibility` — are they wired into actual gates yet, or still placeholders?** Search hits suggest minimal enforcement; needs an audit before tiers are renamed or repriced.
- **Year rollover policy.** Auto-copy fires only when an admin views an empty year for a category. Should there be a scheduled rollover at calendar year-end, or stay lazy?
- **Pro-ration with `requires_boat=True` tiers.** If a user owns no boat at upgrade time, should the Boat Owner upgrade be blocked? Currently no such check on the `/membership/upgrade` path.
