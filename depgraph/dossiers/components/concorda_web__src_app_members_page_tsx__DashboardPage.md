---
node_id: concorda-web::src/app/members/page.tsx::DashboardPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 62a73d0585cac6accf1976d0a2c87cebc0f28349488d561572c1e4730d264e01
status: current
---

# DashboardPage

## Purpose

The central landing page for authenticated members, serving as a high-level dashboard for profile management, boat details, and onboarding status. It orchestrates several specialized views (Boats, Schedule, etc.) via a tabbed interface and manages the transition from the "Get Started" wizard to the full dashboard.

## Invariants

- **Tab Navigation**: The active tab is driven by the `?tab=` search parameter.
- **Default State**: If no tab is specified, the page defaults to `"schedule"`, unless the `showGetStarted` state (derived from `setup_wizard_completed`) forces the `"get-started"` tab.
- **Boat Detail Pattern**: Detailed boat views must use the pattern `?tab=boats&boat=<id>` rather than the legacy `?tab=boat-<id>` format.
- **Data Fetching**: The component performs multiple asynchronous side-effects on mount to calculate "missing field" counts for boats and check the setup wizard status.

## Gotchas

- **Legacy URL Redirects**: Per commit `679fe81`, any URL containing `?tab=boat-` must be redirected to the new pattern `?tab=boats&boat=<id>`. This ensures users with old bookmarks are moved into the correct dashboard context.
- **Async Race Conditions**: The `boatMissing` state calculation relies on a nested loop of `profileApi.getBoats()` and `profileApi.getBoatResume(boat.id)`. If the resume fetch fails, the code catches the error and increments the missing count by 5 (representing a missing resume) rather than crashing.
- **Tab Initialization**: The `tabInitRef` and `showGetStarted` logic is sensitive to the order of execution. The component must wait for the `profileApi.get()` call to resolve before deciding whether to force the `"get-started"` tab, otherwise, the user may see a flicker of the wrong view.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to check `user.memberships` for `grants_boat_management` to determine if the user can see management controls.
- **Side effects**: Triggers the visibility of the `UrgentBanner` and updates the `pending_request_count` via `useDashboardBadges`.

## External consumers

None known.
