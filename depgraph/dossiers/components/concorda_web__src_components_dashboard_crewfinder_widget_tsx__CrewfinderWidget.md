---
node_id: concorda-web::src/components/dashboard/crewfinder-widget.tsx::CrewfinderWidget
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 95123e019c3c3a6b5861653953e1746522b42279ba9016a84739b6a4a3cb4d33
status: llm_drafted
---

# CrewfinderWidget

## Purpose

A dashboard widget that provides a contextual call-to-action based on the user's role. It determines if the user is a boat owner by checking their boat count via `profileApi.getBoats()`, then dynamically updates the title and description to either "Find Crew" or "Find a Boat." This ensures the dashboard entry point is relevant to the user's current status.

## Invariants

- **Uses `profileApi.getBoats()` to determine state.** The widget relies on the length of the returned boat array to toggle between owner and seeker modes.
- **Default state is `null`.** The `isBoatOwner` state starts as `null` to prevent layout shift or incorrect text before the API call resolves.
- **Fallback to "Find a Boat" on error.** If the API call fails, the component catches the error and sets `isBoatOwner` to `false`, defaulting the UI to the seeker experience.
- **Navigation target is static.** The "Browse Crew Finder" button always links to `/members?tab=profile`.

## Gotchas

- **Async loading state.** Because `isBoatOwner` starts as `null`, the title defaults to "Crew Finder" during the initial render before the `useEffect` completes. This can cause a brief text flicker if the API is slow.
- **Dependency on `profileApi`.** Any change to the signature of `getBoats()` will break this widget's ability to determine user role.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to successfully call `profileApi.getBoats()`.
- **Side effects**: Updates the text content of the dashboard view based on the user's profile data.

## External consumers

None known.
