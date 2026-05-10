---
node_id: concorda-web::src/hooks/use-dashboard-badges.ts::useDashboardBadges
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c976e8f7033af9415cc266ec9a4713d4b3442d394acfbc98f679ee4e13726d9c
status: llm_drafted
---

# useDashboardBadges

## Purpose

Provides the badge counts for the dashboard tab strip, specifically tracking pending invitations and incomplete profile fields. It is used to ensure consistency between the `/members` and `/members/setup` views so that the navigation tabs display the same notification counts.

## Invariants

- **Returns a `DashboardBadges` object** containing `pendingInviteCount` and `profileMissing`.
- **`profileMissing` is a derived count** based on the presence of specific fields: `phone_number`, `about_me`, `experience_level`, `positions_preferred`, `race_areas`, and at least one day of `availability`.
- **Fetches are non-blocking.** Errors in `profileApi` or `getMyCrew` are caught internally to prevent the entire dashboard from failing to render.
- **`pendingInviteCount` is a sum** of `event_invitations` and `invitations` from the crew object.

## Gotchas

- **Commit `a3b5d5a`** added the logic to include boat-crew invitations in the count; previously, the badge only reflected certain invitation types.
- **`profileMissing` relies on a specific field-check logic** that includes a check for `availability`. If a user has a `SailingResume` but no days of the week defined in `availability`, it is counted as a missing field.
- **`profileApi.getSailingResume()` is treated as optional.** The code uses a `.catch(() => null as SailingResume | null)` pattern to ensure that a missing resume doesn't crash the `profileMissing` calculation.

## Cross-cutting concerns

- **Auth**: Implicitly depends on the authenticated user session via `profileApi` and `getMyCrew`.
- **Side effects**: Updates the badge counts on the `/members` and `/members/setup` tab strips.

## External consumers

None known.
