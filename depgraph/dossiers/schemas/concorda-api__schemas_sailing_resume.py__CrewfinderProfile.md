---
node_id: concorda-api::schemas/sailing_resume.py::CrewfinderProfile
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0354eca66423743a682854d4dbec822d9514cdd3d5d3fbe66afddaab628a6534
status: llm_drafted
---

# CrewfinderProfile

## Purpose

The base schema for public-facing crew profiles. It provides a high-level summary of a person's sailing identity (experience, preferred positions, and basic contact info) for use in search results and directory listings. It is the parent class for `CrewfinderProfileDetail`, which adds specialized fields like certifications and club affiliations. Use this when you need a lightweight view of a user that doesn't expose sensitive or heavy-weight resume data.

## Invariants

- **`id` and `person_id` are required strings.** Both must be present to link the profile to the underlying identity.
- **`from_attributes = True`** — The model is designed to be instantiated directly from SQLAlchemy/ORM objects.
- **`achievements` uses legacy coercion.** The `_achievements_legacy` validator ensures compatibility with older data shapes via `_coerce_achievements`.
- **Optionality is heavy.** Most fields (picture, experience, availability, etc.) are `Optional` to prevent validation errors when a user has not completed their full profile.

## Gotchas

- **Schema expansion is frequent.** Recent commits `f311f7a` and `7aae433` added US/World Sailing credentials and banner/picture URLs respectively; ensure new fields added to the `Detail` version are also considered for the base `CrewfinderProfile` if they should appear in search results.
- **Field shadowing.** `race_areas` exists in both the base `CrewfinderProfile` and the `CrewfinderProfileDetail`. If you update the type or logic for one, verify the other to avoid inconsistent rendering in the UI.

## Cross-cutting concerns

- **Auth**: Primarily used in public-facing GET requests (`/api/crewfinder`); visibility of certain fields (like `email` or `phone_number`) is controlled by the router's permission logic, not the schema itself.
- **Rate limit**: Subject to the "dynamic registration rate limit" introduced in commit `8b9722a`.
- **Side effects**: Changes to this schema structure will impact the JSON response shape for both the general crew finder list and the specific search endpoint.

## External consumers

- `GET /api/crewfinder` and `GET /api/crewfinder/search` in the web API.
