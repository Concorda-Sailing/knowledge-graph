---
node_id: concorda-web::src/app/members/crewfinder/crew/[id]/page.tsx::CrewDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0fc539784a9e442dae07c07742baf5cf86762502a8c4a99d602436ba1b60b20d
status: llm_drafted
---

# CrewDetailPage

## Purpose

Displays the detailed profile of a specific crew member and provides the interface for inviting them to a boat. It orchestrates data fetching from both `crewfinderApi` (for profile details) and `constantsApi` (for application constants), while also checking existing boat memberships to determine the initial invitation state.

## Invariants

- **Requires `personId` from URL params.** The component relies on the `[id]` segment to fetch the correct profile.
- **`isSelf` check.** Uses `user.id` from `useAuth` to determine if the viewing user is the person being viewed, which dictates UI permissions.
- **`backHref` logic.** The navigation path is determined by the `from` search parameter to ensure the user returns to the correct context (`mycrew` vs `crew` vs default).
- **Invitation state.** The `invited` state is set to `true` if the person is already found in the crew list of any of the user's boats.

## Gotchas

- **Implicit "Already on crew" state.** The `handleInvite` function catches errors where the message includes `"already"`. If the API returns a different error string for existing membership, the UI might show a generic "Error" toast instead of the specific "Already on crew" message (see `handleInvite` logic).
- **Race condition in membership check.** The `useEffect` that checks `isOnAny` (lines 81-87) runs after the initial load and relies on `boats.map`. If `boats` is empty or the API call fails, the `invited` state might not reflect the true status of the user immediately.
- **Unpublished/Private profiles.** Per commit `326d716`, the component must handle cases where a crew resume might be unpublished or the profile is not found, which is handled by the `try/catch` in `loadProfile` setting an error state.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to identify the current user and determine `isSelf`.
- **Side effects**: Inviting a crew member triggers `boatApi.inviteCrew`, which updates the membership status for that person on the selected boat.

## External consumers

None known.
