---
node_id: concorda-web::src/components/boat/boat-inline.tsx::BoatInline
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b04be53e8f8e64da7458ff29b92dbeb1fe6a4cc5bfd617a16d41cfa2ad58a325
status: llm_drafted
---

# BoatInline

## Purpose

The central orchestrator for the boat profile view. It manages the complex state of a boat's various sub-sections (details, resume, crew, punchlist, and banner) and handles the URL-based subtab navigation. Unlike the specialized sibling components (e.g., `BoatProfileTab` or `BoatPunchlist`), this component acts as the stateful container that coordinates data fetching and provides the `onDelete` and `onTabsWidthChange` callbacks to its children.

## Invariants

- **Subtab navigation is URL-driven.** The `subtab` query parameter (e.g., `?subtab=crew`) is the source of truth for which view is active, ensuring browser history and deep-linking work.
- **Ownership check is mandatory.** The component calculates `isOwner` via `ownedBoats.some((b) => b.id === boatId)` to determine if administrative actions (like deletion or transfer) should be visible.
- **State is local to the instance.** While it fetches data via `useBoats`, the individual form states (like `detailsForm` or `bannerCrop`) are managed locally within this component to allow for unsaved/dirty states before committing to the API.

## Gotchas

- **URL replacement vs push.** The `setActiveTab` function uses `router.replace` with `{ scroll: false }`. This prevents the page from jumping to the top when a user switches between tabs (e.g., from "overview" to "crew"), which is critical for a smooth UX in the dashboard.
- **Manual profile completion tracking.** The component calculates `profileMissing` by checking specific fields like `sail_number`, `manufacturer`, and `resume.about`. If a new required field is added to the API, it must be manually added to the `detailsMissing` or `finderMissing` arrays here to ensure the "profile completion" logic remains accurate.

## Cross-cutting concerns

- **Auth**: Uses `useAuth()` to determine user identity and permissions for the `isOwner` check.
- **Side effects**: Triggers re-renders in the parent dashboard/profile layout when `onTabsWidthChange` is called, ensuring the layout adjusts to the width of the active tab content.

## External consumers

None known.
