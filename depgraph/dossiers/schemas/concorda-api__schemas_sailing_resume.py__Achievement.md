---
node_id: concorda-api::schemas/sailing_resume.py::Achievement
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 77f177a7f6cef91ce76fb3e3cb17f222ab392c3580c20f7ee5426c84a7eb0c1b
status: current
---

# Achievement

## Purpose

Defines the structure for a single competitive achievement within a sailing resume. It is a sub-model used primarily within `SailingResumeCreate` and `SailingResumeRead` to capture specific accolades, including the award name, the year achieved, and the competitive placement.

## Invariants

- **`award` is required and non-empty.** The field has a `min_length=1` constraint.
- **`place` is optional.** It is a string field with a `max_length=200`.
- **`year` is an optional integer.**
- **Input coercion is required for legacy support.** The `_achievements_legacy` validator uses `_coerce_achievements` to handle cases where the input might be a list of strings rather than a list of objects.

## Gotchas

- **Legacy string-to-dict coercion.** Per `_coerce_achievements`, if a user provides a list of strings (e.g., `["First Place"]`) instead of objects (e.g., `[{"award": "First Place"}]`), the function strips the string and wraps it in a dictionary `{"award": stripped}` to prevent validation errors.
- **Silent skipping of invalid types.** The `_coerce_achievements` loop silently skips items that are neither strings nor dictionaries, which protects the API from crashing on corrupted rows but may lead to data loss without an explicit error.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Part of the `SailingResume` schema; updates to this model affect the person's profile visibility in the crew finder/roster.

## External consumers

None known.
