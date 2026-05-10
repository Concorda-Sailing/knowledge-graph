---
node_id: concorda-api::schemas/sailing_resume.py::CrewfinderProfileDetail
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4d3ac54ad3c350f0cd9845d36aaf98c4226c315818c22f4cffb5d11337a01322
status: llm_drafted
---

# CrewfinderProfileDetail

## Purpose

Provides the high-fidelity view of a user's sailing profile, extending the base `CrewfinderProfile` with granular professional and recreational data. While `CrewfinderProfile` provides basic contact and availability, this class is used when the client requires deep context like race history, certifications, and club affiliations. It is the primary schema for the detailed profile view in the crewfinder module.

## Invariants

- **Inherits from `CrewfinderProfile`** — must include all base fields (email, phone, etc.) plus the extended sailing-specific fields.
- **`race_areas` is duplicated** — exists in both the base class and this detail class; ensure the detail-specific list is the one used for the expanded view.
- **Optionality** — all fields in this class are `Optional` to allow for partial profile completion or legacy data ingestion.

## Gotchas

- **Schema expansion history** — recent commits show a rapid evolution of this schema. It has recently absorbed `US/World Sailing credential fields` (commit `f311f7a`) and `preferred_oa_ids` (commit `d7c718e`). When adding new professional attributes, check if they belong in the base profile or this detail class.
- **Field shadowing** — `race_areas` is present in both the base and the detail class. If updating the logic for how race areas are stored, ensure changes are reflected in both to avoid type mismatches during serialization.

## Cross-cutting concerns

- **Auth**: Used by `GET::/api/crewfinder/detail/{0}`; access is governed by the router's permission checks.
- **Side effects**: Changes to these fields (via update endpoints) impact the visibility of the user in the crewfinder search results.

## External consumers

- Web frontend (Crewfinder detail pages).
