---
node_id: concorda-web::src/components/profile/boat-publish-bar.tsx::BoatPublishBar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6bf5e5c794295ed7d35138681adb437b07ffd22af13a33ff27272b83214b68af
status: current
---

# BoatPublishBar

## Purpose

The `BoatPublishBar` provides a visual status indicator and a toggle for a user's "published" status. It evaluates the completeness of a `BoatResume` (checking for presence of 'About', 'Ethos', 'Positions', 'Race Areas', and 'Policies') and prevents the user from publishing if required fields are missing. Use this component when a user needs to toggle their visibility/discoverability in the Boat Finder.

## Invariants

- **Requires a valid `Boat` and `BoatResume`** — the component relies on `boat.id` for the API call and `resume` properties for validation.
- **Validation is strictly client-side** — it checks for the existence of `about`, `ethos`, `positions` (length > 0), `race_areas` (length > 0), and both `accepting_crew` and `drinking` policies.
- **`onUpdate` is the source of truth** — after a successful `profileApi.updateBoatResume` call, the component calls `onUpdate(updated)` to ensure the parent state reflects the new published status.
- **`doPublish` is an async operation** — it manages a local `saving` state to prevent multiple concurrent requests during the API round-trip.

## Gotchas

- **Validation-induced blocking** — if a user attempts to toggle the "published" state while `missingItems` is not empty, the `handleToggle` function intercepts the call and sets `showPrompt` to true, preventing the API call.
- **Silent failure on API error** — the `doPublish` function contains a `try/catch` block that catches errors but currently contains only a comment `// revert on failure`. This means if the API call fails, the UI state might become desynchronized from the server without a clear error message to the user.

## Cross-cutting concerns

- **Auth**: Uses `profileApi.updateBoatResume`, which requires an authenticated session.
- **Side effects**: Successful updates trigger `onUpdate`, which is used to refresh the boat's visibility status in the `BoatsList` and potentially the `Dashboard` overview.

## External consumers

None known.
