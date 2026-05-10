---
node_id: concorda-api::schemas/sailing_resume.py::SailingResumeCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f1678833377fd6c62e33d2e1ab8311e23088ac1b7903836838fa39a7978d5c8e
status: current
---

# SailingResumeCreate

## Purpose

The Pydantic model for creating a sailing resume. It defines the input structure for the `POST /api/crewfinder` and `PUT /api/crewfinder/{id}` endpoints. It is distinct from `SailingResumeRead` by omitting system-generated fields like `id`, `type`, and `created`, focusing purely on user-provided data and legacy-compatible achievement coercion.

## Invariants

- **`person_id` is required.** This string links the resume to a specific person in the system.
- **`achievements` uses a custom validator.** The `_achievements_legacy` method calls `_coerce_achievements` to handle mixed input types (dicts vs. strings) to prevent ingestion errors.
- **Optionality of specialized IDs.** Fields like `us_sailing_number`, `world_sailing_id`, and `preferred_oa_ids` are all `Optional` to support varying levels of professional certification.

## Gotchas

- **Legacy achievement coercion.** Per the logic in `_achievements_legacy` (lines 75-78), the schema is designed to be resilient to "corrupted" or inconsistent row data by silently skipping non-dict/non-string items rather than throwing a validation error.
- **Credential field expansion.** Recent changes in `f311f7a` added `us_sailing_number` and `world_sailing_id`. Ensure any new credential types follow this pattern to avoid breaking the strict Pydantic validation on the `POST` endpoint.
- **ID-based filtering.** The inclusion of `excluded_boat_ids` and `no_contact_boat_ids` (per `d5e7a8e`) is used by the matching engine to filter out specific vessels from a user's profile visibility.

## Cross-cutting concerns

- **Auth**: Required for `POST` and `PUT` operations via the `crewfinder` routers.
- **Rate limit**: Subject to the dynamic registration rate limits introduced in `8b9722a`.
- **Side effects**: Updates to this schema directly affect the data surfaced in the "crew finder" matching engine and user profile views.

## External consumers

- Used by `POST /api/crewfinder` and `PUT /api/crewfinder/{id}` in the `crewfinder` router.
