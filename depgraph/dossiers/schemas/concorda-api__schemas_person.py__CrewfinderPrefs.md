---
node_id: concorda-api::schemas/person.py::CrewfinderPrefs
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3570996b57a083557b29d61548d7ce377d2502a6aa557d59c0ac4fc77229ec59
status: current
---

# CrewfinderPrefs

## Purpose

Defines the user preference configuration specifically for the "Crewfinder" feature. It is a sub-model of `Preferences` and is distinct from `DirectoryPrefs` (which governs general directory visibility) and `MailingListPrefs` (which governs communication frequency). Use this when adding or modifying fields related to how a person's identity is surfaced during crew matching and recruitment workflows.

## Invariants

- **`show_phone` and `show_email` default to `True`**. Unlike the more restrictive `DirectoryPrefs`, these are enabled by default to facilitate active crew matching.
- **`opt_in` is the master toggle**. If `opt_in` is `False`, the system should treat the user as invisible to the Crewfinder service regardless of the sub-field values.
- **`allow_matching` is a boolean flag**. It controls whether the user's profile can be surfaced in automated matching-based recruitment.

## Gotchas

- **Default state mismatch**: While `DirectoryPrefs` defaults `show_phone` and `show_email` to `False`, `CrewfinderPrefs` defaults them to `True`. This distinction is critical for the "crew workflow polish" mentioned in commit `fdc87b4`.
- **Implicit dependency on `PersonCreate`**: Because `Preferences` (and thus `CrewfinderPrefs`) is an optional field in `PersonCreate`, new users may lack these keys entirely until an explicit update is performed.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to these preferences impact the visibility of users in the "crew detail pages" and "crew pools" (per commit `1118209`).

## External consumers

None known.
