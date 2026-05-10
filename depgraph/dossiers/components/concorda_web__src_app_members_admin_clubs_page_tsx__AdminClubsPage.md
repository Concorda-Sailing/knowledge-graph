---
node_id: concorda-web::src/app/members/admin/clubs/page.tsx::AdminClubsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 817e642ec9d6132c98c5a0019243a02debd784eea0d36f5090abd02e9fd643c9
status: llm_drafted
---

# AdminClubsPage

## Purpose

The central administrative dashboard for managing organizations (Clubs) and their members. It provides a unified view of all organization types, allowing admins to search, view, and manage club-level data. It is the primary interface for high-level organizational oversight, distinct from the member-specific management pages.

## Invariants

- **Requires `admin.clubs.export` or `admin.clubs.import` permissions** for specific action buttons to be visible and functional.
- **Uses `organizationsApi.list()` to fetch the club list** and `adminApi.members()` to fetch the member list for steward lookups.
- **The `rootOrgId` is derived from the "Organizing Authority" type**; this is used to identify the top-level entity in the hierarchy.
- **`getDelegateName` performs a client-side lookup** against the `members` state to resolve `stewardId` to a human-readable name.

## Gotchas

- **Generalization of organization types** (per commit `31d8b03`) means this page no longer just shows "Clubs" but any organization type. Ensure any logic added here respects the broader organizational hierarchy.
- **Mobile-specific layout requirements** (per commit `55a8876`) suggest that while this is a web-based admin page, the data/structure may be mirrored or consumed by mobile views in a "paired table + card list" format.

## Cross-cutting concerns

- **Auth**: Depends on `useAuth` for permission checks (`admin.clubs.export`, `admin.clubs.import`).
- **Side effects**: Changes to organization data or member lists via the `ClubDialog` or export/import actions will affect the global organization state.

## External consumers

None known.
