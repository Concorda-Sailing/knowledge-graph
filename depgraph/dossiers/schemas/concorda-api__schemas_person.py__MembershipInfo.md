---
node_id: concorda-api::schemas/person.py::MembershipInfo
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 28113c510ce7d45e4785c56b99cbca02451343de27a8ed81121e125834330a32
status: current
---

# MembershipInfo

## Purpose

A data transfer object (DTO) representing a person's relationship to a specific product (e.g., a membership or subscription). It acts as a summary of the `PersonProduct` junction, providing just enough information (`id`, `product_id`, `name`, and `slug`) to identify the membership without exposing the full product or person details. It is used primarily within the `PersonRead` schema to list a user's active affiliations.

## Invariants

- **Requires `id`, `product_id`, `name`, and `slug`**. All four fields are non-optional strings.
- **Derived from `PersonProduct`**. The data is a flattened representation of a junction entity.
- **`name` and `slug` are required for display**. If the underlying product is missing or null, the schema expects these to be empty strings rather than nulls.

## Gotchas

- **Manual serialization in `convert_memberships`**. The `PersonRead` validator `convert_memberships` handles the transformation from the ORM `PersonProduct` object to this dictionary format. If the ORM object's `product` attribute is `None`, the `name` and `slug` must default to `""` to avoid `KeyError` or `NoneType` errors during serialization (see `item.product.name if item.product else ""`).
- **Implicit dependency on Product structure**. Because `name` and `slug` are pulled from the nested `item.product`, any change to the `Product` model's naming or slugging logic will propagate here via the validator.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used in `PersonRead` which is the primary schema for user profile/identity views across the platform.

## External consumers

None known.
