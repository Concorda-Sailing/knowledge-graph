---
node_id: concorda-web::src/components/profile/crewfinder-publish-bar.tsx::CrewfinderPublishBar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4a2136dd42919cc74386646ce66461a3cc618c9f6902c6ef5360d3878684e7a2
status: llm_drafted
---

# CrewfinderPublishBar

## Purpose

Provides a toggle switch for users to opt-in or opt-out of the "Crew Finder" visibility. It acts as a validation gate: if a user attempts to enable the toggle while their `SailingResume` is incomplete (missing `about_me`, `experience_level`, `race_areas`, or `availability`), it intercepts the action and displays a prompt rather than calling the API.

## Invariants

- **Validation is mandatory for opt-in.** The `missingItems` array must be non-empty to trigger the `setShowPrompt(true)` state.
- **API payload structure.** The `doPublish` function must wrap the `opt_in` boolean inside `preferences.crewfinder` to match the `profileApi.update` contract.
- **State synchronization.** The `onProfileUpdate` callback is called with the full updated `Profile` object to ensure the parent component's state remains in sync with the server.

## Gotchas

- **Validation logic is hardcoded to `SailingResume` fields.** If the definition of a "complete profile" changes in the backend, this component's `missingItems` logic must be manually updated to prevent users from being stuck in a "prompt loop" where they cannot publish despite having a valid profile.
- **The `handleToggle` function is asymmetrical.** It only blocks the `checked: true` state. A user can still toggle the switch to `false` (opt-out) even if their profile is incomplete, as `doPublish` is called directly when `checked` is false.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi.update` which requires an authenticated session.
- **Side effects**: Updating this toggle affects the visibility of the user's profile on the "Hero banner cards" (per commit `7ca64bf`) in the boat finder and crew finder sections.

## External consumers

None known.
