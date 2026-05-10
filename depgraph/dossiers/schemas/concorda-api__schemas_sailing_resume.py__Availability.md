---
node_id: concorda-api::schemas/sailing_resume.py::Availability
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 03eeba055b4694e43a81f309c95dbee3f97634baddcf703ff1f6968d108f0e89
status: llm_drafted
---

# Availability

## Purpose

Defines the weekly availability pattern for a sailor, specifying which days of the week they are available and any specific dates to exclude. It is a component of the `SailingResume` schema, used to filter or match crew members to specific regattas or events based on their temporal availability.

## Invariants

- **Days are boolean flags.** Each day of the week (`monday` through `sunday`) is a `bool` that defaults to `False`.
- **`excluded_dates` is a list of ISO strings.** This field accepts an `Optional[list[str]]` to represent specific dates where the user is unavailable.
- **Legacy fields are preserved for backward compatibility.** `weekends`, `evening_races`, and `specific_dates` are kept as `Optional` fields to ensure existing data remains readable during transitions.

## Gotchas

- **Implicit fallback for corrupted data.** The `_coerce_achievements` function (which handles related list-based data in this module) uses a pattern of silently skipping non-dict/non-string items to protect reads against corrupted rows.
- **Schema evolution complexity.** Recent commits like `f311f7a` (adding US/World Sailing fields) and `d7c718e` (adding `preferred_oa_ids`) show that this schema is frequently updated to accommodate new credential and identity types.

## Cross-cutting concerns

- **Auth**: None (this is a data schema).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Changes to this schema impact the `SailingResumeCreate` flow, which is a prerequisite for building out the user's professional sailing profile.

## External consumers

None known.
