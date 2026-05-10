---
node_id: concorda-api::schemas/boat_resume.py::BoatFinderProfile
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 017628cb9ac2b34ccdb7497d1f3ef11cef94db4c87812cb2b019e644efee47f3
status: llm_drafted
---

# BoatFinderProfile

## Purpose

The `BoatFinderProfile` schema defines the public-facing data structure for a boat's profile within the Boat Finder feature. It is a subset of the full boat data, specifically curated for discovery-oriented endpoints. Use this schema when building or extending endpoints that list or search for boats (like `/api/boatfinder`), whereas `BoatFinderProfileDetail` should be used for full-page views where additional context like `drinking` or `typical_crew_complement` is required.

## Invariants

- **`boat_id` is required.** It serves as the primary identifier for linking to the full boat record.
- **`owner_first_name` and `owner_last_name` are mandatory.** Unlike the optional `boat_name`, the owner's identity must be explicitly provided for the profile to be valid.
- **`sail_number` is a required string.** It is a non-optional field used for identification on the water.
- **`availability` is an optional dictionary.** It allows for flexible, unstructured data regarding when the boat is available for use.

## Gotchas

- **Media URLs are relatively new.** Per commit `7aae433`, `banner_url` and `picture_url` were recently added to support visual profiles; ensure any consumer of this schema can handle these new optional string fields without breaking.
- **Schema inheritance is used for detail views.** `BoatFinderProfileDetail` inherits directly from `BoatFinderProfile`. Any change to the base `BoatFinderProfile` (like adding a required field) will automatically propagate to the detail view and potentially break the `GET /api/boatfinder/search` endpoint.

## Cross-cutting concerns

- **Auth**: None (this is a read-only schema for public discovery).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by the boat-finder search and listing endpoints to populate the discovery UI.

## External consumers

- Web frontend (via `/api/boatfinder` and `/api/boatfinder/search`).
