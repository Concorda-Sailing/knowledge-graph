---
node_id: concorda-web::src/components/profile/sections/racing-preferences-section.tsx::RacingPreferencesSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c22a75f33c5e151e975d8a5e7a777df14bd437721b2845e889f9c5d8c446cbb7
status: current
---

# RacingPreferencesSection

## Purpose

Displays and manages the user's racing-specific profile data, including availability (days of the week) and preferred organizations. It provides an inline editing interface via `useInlineEdit` to allow users to update their sailing resume without a full page reload. Use this component when you need to render the racing-specific portion of the user's profile in the user settings or profile view.

## Invariants

- **Requires `resume` object.** The component expects a `SailingResume` object (or `null`) containing `availability` and `race_areas`.
- **Uses `useInlineEdit("racing")` for state management.** This ensures the editing state is scoped to the "racing" key, preventing collisions with other profile sections.
- **Fetches organizations on mount.** It calls `organizationsApi.list()` to resolve `preferred_oa_ids` into human-readable names.
- **Displays a "missing" badge.** A red badge appears if either the availability or the race areas list is incomplete, signaling to the user that their profile is not fully optimized.

## Gotchas

- **Organization lookup is asynchronous.** Because `organizationsApi.list()` is called in a `useEffect`, there is a brief moment where `preferredOrgsText` might be empty or "—" while the list is loading.
- **Type casting for availability.** The component uses `(avail as unknown as Record<string, boolean>)` to access day properties (e.g., `monday`, `tuesday`). This assumes the API response matches the `DAYS` constant casing.

## Cross-cutting concerns

- **Auth**: None (relies on `organizationsApi` which handles its own auth context).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Updates the user's `SailingResume` object via `onResumeUpdate`, which may trigger updates to the broader profile state in the parent view.

## External consumers

None known.
