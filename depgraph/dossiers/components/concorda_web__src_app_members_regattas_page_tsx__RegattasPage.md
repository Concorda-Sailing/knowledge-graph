---
node_id: concorda-web::src/app/members/regattas/page.tsx::RegattasPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 624b2f9d992a1ffea8b5da58e7d5652f7f08b488a7a227a3a98380dbf64e1f0a
status: llm_drafted
---

# RegattasPage

## Purpose

The central orchestration page for the Regattas module. It manages the state for searching, filtering, and adding regattas to a user's schedule, including complex multi-step flows for "Captain" vs "Crew" roles. It serves as the primary interface for users to discover upcoming races and manage their racing calendar.

## Invariants

- **Calendar anchoring is TZ-aware.** The `calendarMonth` state is initialized using `ymdInOrgTz` to ensure the view is anchored to the organization's timezone rather than the browser's local time.
- **Stateful multi-step flows.** The page manages several distinct modal/dialog states: `captainCrewPrompt` (role gate), `seriesPrompt` (series vs single race), and `captainSetup` (detailed boat/crew configuration).
- **Data fetching is split.** `constantsApi` and `profileApi` are called on mount to populate `userBoats`, `userCrewPools`, and global constants required for the UI.
- **Filter state is local-first.** Filters (regions, clubs, types, etc.) are managed via `useState` and drive the visibility of regatta cards.

## Gotchas

- **Timezone-driven calendar title.** Per commit `1347555`, the desktop calendar title must explicitly show the current year to avoid ambiguity in the UI.
- **Role-based gates.** A user must pass the "Captain-or-crew gate" before accessing the `captainSetup` flow. This is a critical UX step to ensure users have the correct permissions/context for the regatta they are adding.
- **Dependency on `ymdInOrgTz`.** If the calendar month calculation fails to use the organization's timezone, the `calendarMonth` state will be offset, causing the user to see the wrong month's races.
- **Race detail integration.** Per commit `df6cdbd`, the regatta add dialogs are designed to be mounted within the detail view, meaning this page's state-driven logic must remain compatible with being triggered from a sub-component.

## Cross-cutting concerns

- **Auth**: Uses `profileApi` to fetch user-specific boat and crew pool data.
- **Side effects**: Updates the user's schedule via `captainSetup` and `seriesPrompt` flows.
- **UI/UX**: Drives the visibility of the "Accepting-Crew" badge and "Upcoming" repositioning logic.

## External consumers

None known.
