---
node_id: concorda-web::src/app/members/boatfinder/[id]/page.tsx::BoatDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a35e74901c4986473c04ef51a4d733d84d660dad4159f127eccd13bbf702bdac
status: llm_drafted
---

# BoatDetailPage

## Purpose

Renders the detailed profile view for a specific boat within the Boat Finder module. It fetches and displays boat specifications (class, manufacturer, length), banner imagery, and crew-related metadata. It distinguishes between a generic profile view and a race-specific view by checking for an `event` search parameter, which determines whether to show a "Race Request" CTA or a standard "Apply" flow.

## Invariants

- **Fetches via `boatfinderApi.getDetail(boatId)`** — the primary data source for the profile.
- **Requires a valid `id` from params** — the page relies on the dynamic route segment to identify the boat.
- **Displays `HeroBanner` with fallback logic** — if `boat_name` or `sail_number` is missing, the subtitle falls back to a formatted string of specs.
- **Uses `PermissionGate`** — the entire view is wrapped in a `boatfinder.view` permission check to ensure unauthorized users cannot access profile details.

## Gotchas

- **Race-specific context dependency** — the logic `const isRaceRequest = !!eventId` (line 31) means the UI behavior changes based on whether the user navigated from a calendar/regatta. If `eventId` is missing, the component defaults to the standard "Apply" flow.
- **Hero banner fallback requirements** — per commit `7ca64bf`, the `HeroBanner` expects a `title` and `subtitle`. If the profile lacks a name or sail number, the subtitle must be carefully constructed from `boatSpecs` to avoid an empty-looking header.
- **Loading state requirement** — the component uses a `Skeleton` stack (lines 48-54) during the `loading` phase. Removing this or failing to handle the `loading` state will cause a flash of empty content or errors when `profile` is null.

## Cross-cutting concerns

- **Auth**: Wrapped in `PermissionGate` with `boatfinder.view` permission.
- **Side effects**: The `isRaceRequest` flag (derived from `eventId`) dictates whether the user sees a generic "Apply" button or a race-specific interaction.

## External consumers

None known.
