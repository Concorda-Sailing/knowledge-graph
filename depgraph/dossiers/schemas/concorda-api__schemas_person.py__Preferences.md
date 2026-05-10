---
node_id: concorda-api::schemas/person.py::Preferences
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2580bb8644a79d51e98cb800c5993eeda61c6dd518c0451e689894770d5ad8c4
status: llm_drafted
---

# Preferences

## Purpose

The `Preferences` model defines the user-specific configuration and UI state for a person. It aggregates specialized preference types—`DirectoryPrefs`, `CrewfinderPrefs`, and `MailingListPrefs`—to manage how a user interacts with different modules of the platform. It is distinct from `PersonRead` in that it focuses on the *settings* rather than the identity or membership data.

## Invariants

- **`DEFAULT_PREFERENCES` is the source of truth** for initial state, using `.model_dump()` from the specific preference sub-classes to ensure consistency between the class definitions and the default dictionary.
- **`mailing_list` defaults to `opt_in: False`** but `event_notices: True` and `general_news: True` to ensure users receive critical system updates by default.
- **`calendar_filters` and `my_schedule_filters` are `dict` types**, allowing for flexible, unstructured filtering logic that can be expanded without schema migrations.
- **`setup_wizard_completed` is a boolean flag** used to track onboarding progress; it is part of the core `Preferences` object.

## Gotchas

- **Manual dictionary construction risk:** Because `DEFAULT_PREFERENCES` relies on calling `.model_dump()` on instances like `DirectoryPrefs()`, any change to the constructor of those sub-classes must be reflected in how the default dictionary is generated to avoid `TypeError` during instantiation.
- **Schema complexity in `PersonRead`:** While `Preferences` is a standalone model, it is embedded directly into `PersonRead`. Changes to the structure of `Preferences` (like adding a new sub-preference type) will immediately impact the serialization of the entire `Person` object.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to these preferences (specifically `mailing_list` or `directory` settings) may impact how the user appears in search results or how they receive automated communications via SendGrid (per commit `a7a8a37`).

## External consumers

None known.
