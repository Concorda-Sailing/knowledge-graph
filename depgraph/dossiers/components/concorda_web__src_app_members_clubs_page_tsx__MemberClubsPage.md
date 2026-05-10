---
node_id: concorda-web::src/app/members/clubs/page.tsx::MemberClubsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c173da87a6718320c1ae31e0be9c40981e12e77487a79167a7280192f43da830
status: llm_drafted
---

# MemberClubsPage

## Purpose

Displays a searchable, filterable directory of member yacht clubs, sailing centers, and racing associations. It fetches delegate information and organization-wide regions to provide a high-level overview of affiliated entities. Use this component when you need to present a list of organizations that includes both the club's identity and its primary contact (delegate) information.

## Invariants

- **Data fetching is dual-source.** It concurrently calls `organizationsApi.delegates()` for entity data and `constantsApi.getAll()` for the region list.
- **Search is case-insensitive.** The filter applies to `club.name`, `club.abbreviation`, `delegate.first_name`, `delegate.last_name`, and `club.address.city`.
- **Region filtering is strict.** If `regionFilter` is set to "none", the component explicitly hides clubs where `club.region` is truthy.
- **Loading state is mandatory.** The component renders a skeleton-based grid while the two API calls are in flight to prevent layout shift.

## Gotchas

- **Search is broad and potentially noisy.** Because the search string `q` is checked against the delegate's name and the club's address/city, a search for a common name might return unexpected results across different clubs.
- **Region-less clubs are hidden by "none" filter.** Per commit `11a19fa`, the logic `if (regionFilter === "none") { if (club.region) return false; }` means that if a user selects "none", they are explicitly looking for clubs that have no region assigned.
- **The component is "general" but not "universal".** Per commit `31d8b03`, while the admin view was generalized for all organization types, this specific page is still heavily reliant on the `DelegateInfo` shape which assumes a `delegate` object exists.

## Cross-cutting concerns

- **Auth**: Relies on `organizationsApi` and `constantsApi`, which require valid authentication headers established by the session.
- **Side effects**: The search and filter state are local to this component; changing them does not trigger a re-fetch of the underlying data, only a re-render of the `filtered` list.

## External consumers

None known.
