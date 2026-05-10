---
node_id: concorda-web::src/components/profile/sections/crewfinder-optin-section.tsx::CrewfinderOptinSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c7532a6b4238650176afcfd57943593b5e6768c5824af45060d7370a9676bc46
status: current
---

# CrewfinderOptinSection

## Purpose

The `CrewfinderOptinSection` is a UI component that displays the user's readiness to be discovered by others via the Crew Finder feature. It provides visual feedback on whether the user has completed the necessary profile requirements (Sailing Experience and Racing Preferences) and hosts the controls for visibility and publishing. It is distinct from `SailingExperienceSection` because it focuses on the *status* of the data rather than the editing of the data itself.

## Invariants

- **Requires a `Profile` and `SailingResume`** — The component relies on `profile` for identity and `resume` to determine the `experienceReady` and `preferencesReady` states.
- **Status is derived from `resume` fields** — `experienceReady` is true only if `about_me` and `experience_level` are present; `preferencesReady` requires both `race_areas` and at least one day of `availability`.
- **Uses `onProfileUpdate` for state synchronization** — Any changes made via `CrewfinderPublishBar` or `CrewfinderVisibility` must be passed back through this callback to ensure the parent state remains the source of truth.

## Gotchas

- **Extraction Refactor** — Per commit `9f71a80`, this component was recently extracted from a larger profile section. Ensure that any new logic regarding profile completeness is updated here if it was previously handled in the parent component.

## Cross-cutting concerns

- **Auth**: None (relies on the parent component to provide the authenticated `profile` object).
- **Side effects**: Updates to visibility or publishing status via this section will trigger `onProfileUpdate`, which may affect how the user appears in global search results or the directory.

## External consumers

None known.
