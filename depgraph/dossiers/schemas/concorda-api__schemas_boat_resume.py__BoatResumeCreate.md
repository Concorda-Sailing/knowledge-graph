---
node_id: concorda-api::schemas/boat_resume.py::BoatResumeCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6471427a5d8b240496440e7d0d82751f647529cfa5392956ef59b89b419a402b
status: llm_drafted
---

# BoatResumeCreate

## Purpose

The schema for creating a new boat resume. It defines the required and optional fields for a boat's public-facing profile, such as ethos, crew requirements, and availability. Use this instead of `BoatResumeUpdate` when initializing a new boat profile to ensure `boat_id` is provided as a mandatory field.

## Invariants

- **`boat_id` is required.** It is the primary identifier linking the resume to a specific boat entity.
- **`published` defaults to `False`.** New resumes are created in a draft state unless explicitly set to `True`.
- **`looking_for_junior_crew` defaults to `False`.**
- **`availability` is a dictionary.** It expects a structured object (likely containing time/day keys) rather than a simple string.

## Gotchas

- **`ethos` and `drinking` use string literals.** While the type hint is `Optional[str]`, the docstrings indicate specific expected values (e.g., `"Competitive, Casual, Beginner"` or `"Yes, Only after Racing, No"`). Passing arbitrary strings may cause UI inconsistencies in the Boat Finder.
- **`race_areas` and `positions` are lists.** Ensure input is a list of strings to avoid validation errors during creation.

## Cross-cutting concerns

- **Auth**: Requires a valid session to POST to the endpoint that consumes this schema.
- **Side effects**: Creation of a resume via this schema populates data for the "Boat Finder" feature (see commit `7aae433`).

## External consumers

- None known.
