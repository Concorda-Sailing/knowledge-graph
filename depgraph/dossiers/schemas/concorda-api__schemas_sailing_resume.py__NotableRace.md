---
node_id: concorda-api::schemas/sailing_resume.py::NotableRace
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 531d9f6025728e9f787534459cb9c2dfb8f204382fa4c813a5de57c067972ce7
status: llm_drafted
---

# NotableRace

## Purpose

Defines the structure for a specific, high-level racing achievement within a user's sailing resume. It is used both for `notable_races` and `cruises` in the `SailingResumeCreate` model to provide structured context about a sailor's significant past experiences.

## Invariants

- **`name` is required.** Every `NotableRace` instance must have a non-null string name.
- **`year` is optional.** If provided, it must be an integer.
- **`boat` and `role` are optional.** These fields capture the vessel and the user's specific position (e.g., "Skipper" or "Trim") during the race.

## Gotchas

- **`notable_races` and `cruises` share the same schema.** While they represent different types of experiences, they both utilize the `NotableRace` model, meaning any change to this class affects both lists in the `SailingResume` object.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: This schema is a component of `SailingResumeCreate`; updates to these fields are reflected in the user's profile data.

## External consumers

None known.
