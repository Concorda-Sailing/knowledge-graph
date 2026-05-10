---
node_id: concorda-web::src/components/dashboard/schedule-tab.tsx::CrewRosterRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 048ad81dadfad13d9251964670446ae8ba09802a497970214e1eba36674da3df
status: llm_drafted
---

# CrewRosterRow

## Purpose

A sub-component of the `ScheduleTab` that renders a collapsible row representing the crew members assigned to a specific event. It provides a high-level summary (count of active crew) and, when expanded, displays an avatar-based list of members. It is distinct from `AvailableSection` in that it is strictly for displaying existing event-crew associations rather than managing invitations or requests.

## Invariants

- **`crew` prop can be `undefined`** — if `undefined`, the component must render a "Loading..." state and a `Skeleton` when expanded to prevent layout shift during data fetching.
- **Filtering logic is internal** — the component only displays members where `status` is neither `"declined"` nor `"pool"`.
- **`currentUserId` is optional** — if provided, the component highlights the user's own name with a `(you)` suffix and a specific background color (`bg-primary/10`).
- **Avatar fallback** — if `person_picture_url` is missing, it must render the `AvatarFallback` using the first letter of the first and last names.

## Gotchas

- **Visibility logic** — per commit `6eace6a`, the component is designed to hide peer crew status from non-owner viewers to maintain privacy, though the current implementation relies on the parent's ability to filter the `crew` array before passing it down.
- **Empty state text** — if the filtered `activeCreew` length is 0, the header text defaults to "Who's racing" rather than showing a count, to avoid confusing users with "0 crew".

## Cross-cutting concerns

- **Auth**: Uses `currentUserId` to identify the local user for the "(you)" label.
- **Side effects**: Part of the `ScheduleTab` hierarchy; changes to the `crew` data in the parent will trigger a re-render of this row.

## External consumers

None known.
