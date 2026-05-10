---
node_id: concorda-api::models/product.py::Product
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e16a3daa1fe914b61f468008d803e069252a9768149c509038eb2fc8710c42f1
status: llm_drafted
---

# Product

## Purpose

`Product` is the **discrete event-ticket SKU** table — a row defines a single buyable thing (regatta entry, dinner-only, late-fee surcharge, racing series ticket) sold at a fixed price with optional inventory (`quantity`). It is the counterpart to `TemporalProduct` (memberships, time-bounded with `grants_*` entitlements): a `Product` does **not** carry any time window, year, or feature-flag bundle — paying for one mints an `EventRegistration`, not an entitlement. When a future Claude is touching event ticketing, registration flow, ticket inventory, or per-event pricing, this is the model. When the question is "does this user have membership X?" or "is this purchase a recurring subscription?", that is `TemporalProduct`.

## Invariants

- **`type="Product"` is hard-coded in `__init__`.** Single-table-style polymorphism via `BaseModel.type`; never override the discriminator.
- **`Transaction.product_type` MUST agree with the model.** Ticket purchases create `Transaction` rows with `product_type="Product"` (six call sites in `routers/payments.py`); membership purchases use `"TemporalProduct"`. The composite index `ix_transactions_product_id_type` (migration 011) is built on this pair — a wrong discriminator silently creates orphan rows that no lookup will find.
- **Slug uniqueness is `(slug, event_id)`, app-enforced only.** `routers/products.py:74-84` and `:117-128` reject duplicates per-event. There is no DB UNIQUE; two products with `event_id=NULL` and the same slug can coexist via raw insert. Same caveat as TemporalProduct.
- **`event_id` may be NULL** — the column is intentionally nullable for future org-wide catalog items, but every read path today filters on `Product.event_id == event.id`. A NULL-event Product is effectively invisible to tickets/registration/payments flows.
- **Quantity gate is enforced via `EventRegistration` count, not on `Product`.** Sold-out check is `count(EventRegistration where status="Confirmed" and product_id=p.id) >= product.quantity` (`events.py:1473-1481, 1530-1545, 1684-1696`). There's no decrement counter; the source of truth is the registration table.
- **Free tickets (`price == 0`) skip Stripe entirely.** `payments.py:112-116, 292-296` reject them at `/create-intent` with "Free tickets do not require payment"; `events.py:1693+` lets `register_for_event` proceed without a `transaction_id` when `product.price == 0`.
- **Tier-C scope**: any create/update/delete that touches a `Product` with an `event_id` must run through `_require_event_org_scope` (`routers/products.py:20-31`). Update re-checks against the *new* `event_id` so a delegate cannot reassign a ticket to another club's event.

## Gotchas

- **`effective_date`, `end_date`, `publish_date` are stored but not enforced anywhere.** The columns exist on the model (and on `ProductCreate/Update/Read` schemas), but no router filters on them. A product with `publish_date` in the future is still listed by `GET /events/slug/{slug}/tickets`; one past `end_date` is still purchasable. If you add date-window logic, you are wiring it from scratch — don't assume parity with TemporalProduct's `start_date/end_date`.
- **`058aa8c` (tier-C scope) is the only post-bootstrap commit that touched this router.** Before that, a delegate of one club had `events.edit` and could mutate any other club's tickets. The `_require_event_org_scope` helper is the chokepoint; the permission decorator alone is insufficient. Don't add a new mutating endpoint here without calling it.
- **Multi-ticket transactions store only the *first* `product_id`.** `payments.py:226, 257, 309` set `Transaction.product_id = request.items[0].product_id` even when the order has many lines; `expected_quantity` carries the total count. Any audit of "what did this transaction buy?" needs to walk `EventRegistration.transaction_id`, not `Transaction.product_id`. This silently couples ticket reporting to the registration table.
- **`74962cb` (`fix(security): bind paid registrations`)** showed that any user could pass another user's completed `transaction_id` to `register_for_event` and consume it. The current binding is `Transaction.person_id == current_user.id` (or NULL for the anonymous-checkout flow). Don't loosen this; the anonymous-NULL branch is intentional for guest checkout, not a fallback.
- **`expected_quantity` gates re-use of one transaction across multiple registrations.** `events.py:1730-1736` blocks a registration when `count(confirmed regs for txn) >= expected_quantity or 1`. A multi-ticket purchase produces one Transaction whose `expected_quantity` must be drained by N separate `register_for_event` calls — not one bulk call. Off-by-one here = double-redemption.
- **Event duplication (`POST /events/{id}/duplicate`) re-creates active products** with the same slug. Because the slug-unique constraint is scoped to `(slug, event_id)` and the new event has a different id, there is no collision. If you ever change uniqueness to global slug, this code (`events.py:1383-1400`) will start failing.
- **No model-level relationship to `EventDiscount`**, despite `event_discount_tickets` being an association table that scopes a discount to specific `Product` rows (`event_discounts.py:71-80, 114-126`). The link exists only in the discount router — `Product.discounts` is not declared. Tooling that walks SQLAlchemy relationships will not find it.
- **No model-level `event` relationship either.** Code joins manually on `event_id` everywhere. Adding a `relationship("Event", back_populates=...)` is a bigger change than it looks because nothing currently expects lazy-loaded events on Product.

## Cross-cutting concerns

- **Stripe integration.** `POST /payments/create-intent` is the only paid-ticket purchase path. Three branches all create `Transaction.product_type="Product"`: (1) multi-ticket via `items[]` with discount calculation, (2) single ticket via `product_id`, (3) fully-discounted-to-$0 which records a Completed transaction without calling Stripe. Stripe metadata for single-ticket carries `product_id`/`product_slug`/`product_name`; multi-ticket carries a comma-joined `products` string only — slug renames after a charge break the audit trail visually but not functionally.
- **Transaction lifecycle.** Stripe webhook (`payments.py:474-503`) flips `Pending → Completed` on `payment_intent.succeeded`, with an `AmountMismatch` guard that compares `payment_intent.amount_received` to `transaction.amount * 100`. `register_for_event` also has a defensive lazy-promote path: if a transaction is still `Pending` when the user lands on the registration page, it calls `retrieve_payment_intent` and self-heals if Stripe says succeeded. Don't remove that — webhooks can be slower than the user.
- **EventDiscount stacking.** `payments.py:146-204` evaluates every active discount on the event and applies the single best one (`best_savings`). Per-discount eligibility scope is `event_discount_tickets` (selected `Product` ids) or whole-order. Discount usage is incremented atomically via a conditional UPDATE that re-checks `max_uses` at the DB level (`payments.py:206-219`); a lost race silently clears the discount. There is no "stack two discounts" path — adding one would require redesigning `best_savings`.
- **Refunds.** None. There is no refund endpoint, no `Transaction.status="Refunded"` writer, and no path from a deleted Product to a refunded Transaction. Deleting a Product (`DELETE /api/products/{id}`) is a hard delete with no FK cascade audit — historical `Transaction.product_id` and `EventRegistration.product_id` rows pointing at it become dangling. The confirmation/my-registration endpoints handle this defensively with `product.name if product else "Unknown"` (`events.py:1597, 1648`).
- **Auth.** All CRUD requires `events.edit` permission plus the tier-C `_require_event_org_scope` check. Public reads are via the event-scoped endpoints (`/events/slug/{slug}/tickets`, `/events/slug/{slug}/check-registration`) — there is no public `/products` listing.
- **No websocket broadcast** on Product mutations. The SPA refetches.
- **No logigraph rules** target this node currently.

## External consumers

- **Stripe** — receives `product_id`, `product_slug`, `product_name` in PaymentIntent metadata (single-ticket path) or a comma-joined product list (multi-ticket path). Historical only — no functional dependency.
- **Concorda iOS app** — reads `/events/slug/{slug}/tickets` for the public ticket list during registration. It does not call admin product CRUD.
- **MBSA legacy CSV importer / fixtures** — no known direct dependency on Product slugs (unlike TemporalProduct's `boat-owner-{year}` shape).
- **No external webhooks or scheduled jobs** consume Product directly.

## Open questions

- **Should `effective_date` / `end_date` / `publish_date` be removed or wired in?** Three columns on every row, indexed nowhere, filtered nowhere. Either cut them in a migration or implement the publish-window semantics they imply.
- **Should `(slug, event_id)` become a real DB UNIQUE constraint?** Currently app-enforced only — same race risk as TemporalProduct's `(slug, year)`.
- **Refund flow.** Stripe refunds, `Transaction.status="Refunded"`, and `EventRegistration.status="Cancelled"` propagation are unimplemented. When the first chargeback or admin refund request lands, this becomes urgent.
- **Multi-ticket transaction modeling.** `Transaction.product_id = items[0]` is a known compromise. A `TransactionLineItem` table would unblock honest reporting and per-line refunds.
- **Org-wide catalog (NULL `event_id`) products** — the column is nullable but no read path supports them. Either delete the nullability or design the catalog UX.
