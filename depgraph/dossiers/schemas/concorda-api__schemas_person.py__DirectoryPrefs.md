---
node_id: concorda-api::schemas/person.py::DirectoryPrefs
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 32353720da54e7e0db2546f9330b235719ab7c41d9acf99e58e0b9300f4853de
status: llm_drafted
---

# DirectoryPrefs

## Purpose

Defines the visibility and communication preferences for a user within the directory and crew-finding subsystems. It is a sub-model of `Preferences` used to control how much personal information (name, phone, email) is exposed to other members. Use this instead of `CrewfinderPrefs` when you need to specifically manage directory-wide visibility vs. crew-specific visibility.

## Invariants

- **`opt_in` is the master toggle** — All visibility fields (`show_name`, `show_phone`, etc.) are effectively ignored if `opt_in` is `False`.
- **Default state is private** — `opt_in`, `show_name`, and `show_email` default to `False` to ensure privacy-by-default for new users.
- **`show_phone` defaults to `False`** — Unlike `CrewfinderPrefs`, which defaults to `True` for phone visibility, `DirectoryPrefs` is more restrictive.

## Gotchas

- **Inconsistent defaults across preference types** — `CrewfinderPrefs` defaults `show_phone` to `True` (commit `1118209`), but `DirectoryPrefs` defaults it to `False`. Developers must be careful when switching between these models in the UI to avoid accidentally exposing phone numbers in the directory.

## Cross-cutting concerns

- **Auth**: Managed via the `Person` model; visibility is subject to the user's organization-level permissions.
- **Side effects**: Controls the visibility of user details on the "crew detail" pages and the general member directory.

## External consumers

None known.
