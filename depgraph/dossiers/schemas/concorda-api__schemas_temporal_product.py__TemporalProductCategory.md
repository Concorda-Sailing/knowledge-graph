---
node_id: concorda-api::schemas/temporal_product.py::TemporalProductCategory
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 357f0e633f24f699a16762f1fb29ce713795dc0ce88760ac52fe58a28612e34f
status: current
---

# TemporalProductCategory

## Purpose

Defines the enumeration for product types within the temporal product system. It distinguishes between `Membership` (recurring/long-term) and `Event` (single-instance/short-term) categories. This classification drives how the product is treated by the registration and payment systems.

## Invariants

- **Inherits from `str, Enum`** — Ensures compatibility with JSON serialization and Pydantic's string-based validation.
- **Values are case-sensitive** — Must be exactly `"Membership"` or `"Event"`.
- **Used as a type discriminator** — The `category` field in `TemporalProductCreate` and `TemporalProductUpdate` relies on these specific string values to determine product behavior.

## Gotchas

- **Restructuring-induced dependency** — Per commit `bb2da2b`, the system underwent a restructure of memberships and roles. Any logic relying on the distinction between a "Membership" and an "Event" must account for the new `event_manager` role and the updated permission model.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The `category` value influences whether a product is treated as a recurring membership or a one-off event registration, affecting downstream payment and registration logic.

## External consumers

None known.
