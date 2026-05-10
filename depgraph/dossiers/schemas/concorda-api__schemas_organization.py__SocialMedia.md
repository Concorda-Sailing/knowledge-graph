---
node_id: concorda-api::schemas/organization.py::SocialMedia
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5cebfc6e5beccdda0effdb5a3188ddf5056be4081d6d119221986572c5cb6f04
status: current
---

# SocialMedia

## Purpose

The `SocialMedia` model provides a structured container for an organization's social media presence, specifically grouping Facebook, Instagram, and Twitter handles. It is used as a nested component within the `OrganizationCreate` schema to ensure type-safe ingestion of social links during organization creation or updates.

## Invariants

- **All fields are optional.** `facebook`, `instagram`, and `twitter` are all defined as `Optional[str] = None`, allowing for partial profiles.
- **Input is a flat object.** When used in `OrganizationCreate`, the client must provide a single object containing these keys.
- **No validation logic.** This is a pure data-carrying Pydantic model with no custom validators or regex constraints on the string formats.

## Gotchas

- **Schema mismatch in `OrganizationRead`.** While `SocialMedia` is a nested model in `OrganizationCreate`, the `OrganizationRead` schema (and the broader `Organization` structure) treats the `social_media` field as a `dict` rather than the `SocialMedia` type. This means any code relying on strict type-checking for the *output* of an organization fetch must handle a raw dictionary rather than the `SocialMedia` class.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
