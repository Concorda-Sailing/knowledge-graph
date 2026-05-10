---
node_id: concorda-web::src/components/profile/crewfinder-visibility.tsx::CrewfinderVisibility
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea06dd0619714b546708e12f426ec6778ba95ab62204e2a0795f1c4374dcbbe1
status: current
---

# CrewfinderVisibility

## Purpose

Provides a UI for users to toggle the visibility of their name, phone, and email within the Crewfinder feature. It manages local loading states and success feedback during asynchronous updates to the user's profile preferences. This component is used to allow granular control over what personal data is exposed to other sailors in the community.

## Invariants

- **Updates via `profileApi.update`** — The component sends a nested object to the API to ensure only the specific `crewfinder` preference field is targeted.
- **Requires `profile` and `onUpdate` props** — The component relies on the parent to provide the current state and a callback to sync the updated profile after a successful API call.
- **Input/Output is a `Profile` object** — The `onUpdate` callback must receive the full updated profile object returned by the API to maintain state consistency in the parent.

## Gotchas

- **Silent failure on error** — Per the implementation in `save`, if the API call fails, the error is caught and ignored. This results in the checkbox appearing to "revert" on the next render because the local state is not updated, but the user receives no explicit error message.
- **Race condition on rapid clicks** — The `disabled={saving}` attribute on the `Checkbox` prevents multiple simultaneous requests, but the `setTimeout` for `setSuccess(false)` is hardcoded to 2000ms, which may overlap with subsequent user interactions if the API is slow.

## Cross-cutting concerns

- **Auth**: Uses `profileApi.update`, which requires an authenticated session.
- **Side effects**: Updates to these fields directly affect the visibility of user data in the Crewfinder search results and profile views.

## External consumers

None known.
