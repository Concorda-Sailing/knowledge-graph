---
node_id: concorda-web::src/components/profile/profile-inline.tsx::ProfileInline
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ff40c2b167641f0d9ae7a91efa3edf676e9d218462b8a8da2b936f5adadef87e
status: llm_drafted
---

# ProfileInline

## Purpose

The central orchestrator for the user profile view. It manages the lifecycle of profile-related data, including personal information, communications, and sailing experience, by coordinating multiple specialized section components. It acts as the single source of truth for the current `editing` state and handles the complex logic of aggregating and saving disparate form data across different sections.

## Invariants

- **Data fetching is dual-track.** It concurrently fetches the base `profileData` and the `sailingResume` via `profileApi`.
- **`formRefs` management.** The `formRefs` Map is cleared every time the `editing` state changes to ensure stale form handles from one section do not persist into another.
- **`section` based saving.** The `saveEdit` function accepts a specific `EditingSection` to determine which subset of data is being committed.
- **Error handling.** If `profileApi.get()` fails, the component sets a string error message and stops the loading sequence.

## Gotchas

- **Mobile overflow.** Per commit `3dc161f`, the profile layout is sensitive to container widths; ensure any new sub-sections respect the `TabsList` and `SidebarInset` constraints to prevent 4px overflows on mobile.
- **Racing section validation.** The `saveEdit` function contains a specific guard for the `"racing"` section that checks for `missingFields` in the form status. If you add a new required field to a racing-related section, you must ensure it is registered in the `h.getStatus().missingFields` array, or the `toast` will not trigger.
- **State-driven data loading.** The `loadData` function accepts a `showSkeleton` boolean; if `false` is passed (as seen in the `useWsFreshness` hook), the component will not trigger the loading skeleton, allowing for a smoother background refresh.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to access `refreshUser` for state synchronization.
- **Websocket**: Listens to the `person.updated` event via `useWsFreshness` to trigger a background `loadData(false)` refresh.
- **Side effects**: Rebuilds the profile view when the user's identity or profile data is updated via the websocket.

## External consumers

None known.
