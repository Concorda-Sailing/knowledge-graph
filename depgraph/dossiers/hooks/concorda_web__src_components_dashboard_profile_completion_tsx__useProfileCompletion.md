---
node_id: concorda-web::src/components/dashboard/profile-completion.tsx::useProfileCompletion
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17495ddec568fd2ea2368fd7ee1e157e3531aaad4227aa2fe8f6c09bd512f1b2
status: current
---

# useProfileCompletion

## Purpose

Provides a data-fetching hook to determine a user's onboarding progress. It aggregates data from three distinct API endpoints—profile, sailing resume, and boats—to calculate a completion state. Use this hook when a parent component needs to know if a user has finished their setup (e.g., to show a "Get Started" widget) without the overhead of the full `ProfileCompletion` UI component.

## Invariants

- **Returns `null` on failure.** If any of the three primary API calls fail or if the `buildTasks` logic throws, the hook returns `null` to signal an error state.
- **Aggregates three specific endpoints.** It relies on `profileApi.get()`, `profileApi.getSailingResume()`, and `profileApi.getBoats()`.
- **Graceful degradation for optional data.** The `getSailingResume` and `getBoats` calls are wrapped in `.catch()` blocks to return `null` or an empty array respectively, ensuring a missing resume doesn't break the entire completion check.
- **Output shape is fixed.** Returns an object containing `allDone` (boolean), `tasks` (array of `Task`), and `completed` (number).

## Gotchas

- **Race conditions in `Promise.all`.** Because the hook uses `Promise.all`, if the `profileApi.get()` call is slow, the entire completion state is delayed even if the other two sources are instant.
- **Implicit dependency on `buildTasks`.** The logic for what constitutes a "task" is abstracted into `buildTasks`; changing the definition of a task in that function will silently change the `allDone` status and the `completed` count here.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` which requires an authenticated session.
- **Side effects**: The completion state is used to drive the "Get Started" widget in the dashboard, which is a key part of the onboarding flow introduced in commit `23fb96c`.

## External consumers

None known.
