---
node_id: concorda-web::src/components/finder/crew-finder-panel.tsx::CrewCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7ee71d12e6acc77aed8cb8b89cac5f19a1b473b0b4a13ccb5d26be3a0417eff9
status: current
---

# CrewCard

## Purpose

The `CrewCard` component renders a visual summary of a user's sailing profile within the Crew Finder interface. It displays key identity markers (name, avatar, banner) alongside sailing-specific metadata like experience level, years sailing, preferred positions, and availability. It serves as the primary navigational entry point to a user's full profile via `router.push`.

## Invariants

- **Input is a `CrewfinderProfile` object.** This object must contain the user's identity and sailing-specific fields (e.g., `experience_level`, `positions_preferred`, `race_areas`).
- **`isSelf` flag controls contact visibility.** When `isSelf` is true, the component logic (via `hasPublishedContact`) determines if contact information should be surfaced or if the user is viewing their own profile.
- **Navigation is driven by `person_id`.** Clicking the card triggers a route change to `/members/crewfinder/crew/${profile.person_id}`.
- **Availability rendering is case-sensitive.** The component maps over a hardcoded array of days to render badges based on the `profile.availability` record.

## Gotchas

- **Footer alignment issues.** Per commit `f36708e`, card footers (like the availability badges) require specific pinning to ensure they don't jump or misalign when the profile data is sparse.
- **Avatar fallback logic.** The `avatarFallback` uses the first character of the first and last name (e.g., `profile.first_name[0] + profile.last_name[0]`). If names are missing or malformed, this may throw or render incorrectly.
- **Hardcoded day mapping.** The availability section relies on a hardcoded array of strings `["monday", "tuesday", ...]` to map the `profile.availability` object. If the API returns different keys or casing, the badges will not render.

## Cross-cutting concerns

- **Auth**: None (the component is a purely presentational/navigational element, though it relies on the user being authenticated to see the full `/members/` route).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Navigation via `router.push` affects the browser history and the active view in the `finder` panel.

## External consumers

None known.

## Open questions

- The `onContact` prop is defined in the signature but not currently utilized in the JSX; should the `HeroCard` or a sub-component be updated to trigger this when a user attempts to interact with the profile?
