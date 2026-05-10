---
node_id: concorda-api::models/payment_config.py::PaymentConfig
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 979ce7d72c9930ee29ad5dae50aec282aa9d122e99ffdc6d877c184e0901d04b
status: llm_drafted
---

# PaymentConfig

## Purpose

The `PaymentConfig` model acts as a singleton configuration store for Stripe integration credentials. It holds the publishable key, secret key, and webhook secret required for processing payments. Because it is a singleton, it is intended to have exactly one row in the `payment_config` table, which is queried via `.first()` to provide context to the payment engine.

## Invariants

- **Singleton pattern** — Only one row is expected to exist in the `payment_config` table.
- **`id` is a UUID string** — The primary key is a 36-character string generated via `uuid.uuid4()`.
- **`mode` is a required field** — It defaults to `"disabled"` and dictates the operational state of the payment system.
- **`updated_at` is auto-managed** — The timestamp updates automatically on every row mutation via `datetime.utcnow`.

## Gotchas

- **Singleton assumption** — The docstring explicitly states: `"Singleton — query with .first(), only one row expected."` If multiple rows are inserted, the behavior of the payment engine becomes non-deterministic as it relies on the first result returned by the DB.
- **Recent feature expansion** — Per commit `6405007`, this model is part of a larger push adding "payments, crew finder, [and] temporal products." Changes to the `mode` or keys here will directly impact the stability of the newly added payment and registration systems.

## Cross-cutting concerns

- **Auth**: Protected by admin-level authorization via `routers/admin.py`.
- **Side effects**: Updates to this model (specifically `stripe_secret_key` or `mode`) directly affect the ability of the system to process payments and validate Stripe webhooks.

## External consumers

- Stripe Webhook listener (via `stripe_webhook_secret`).
