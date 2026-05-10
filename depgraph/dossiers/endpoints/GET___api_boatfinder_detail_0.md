---
node_id: GET::/api/boatfinder/detail/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 168d51531850bb7ac70177dd785d6b28b4a8522b9bdbf6bf1f36fb07379e59ea
status: current
---

# GET /api/boatfinder/detail/{boat_id}

## Purpose

Fetches the full profile of a specific boat, including its public "resume" and owner details. This is the primary data source for the Boat Finder detail view. It is distinct from the list-view endpoints by providing deep-link data like `ethos`, `positions`, and the `viewer_is_crew` status, which allows the UI to conditionally show "Apply to Crew" or "Contact Owner" buttons.

## Invariants

- **Requires `boatfinder.view` permission** via the `require_permission` dependency.
- **Returns `BoatFinderProfileDetail` schema.**
- **Throws 404 if `boat_id` does not exist** or if no published `BoatResume` is found for that boat.
- **`viewer_is_crew` is calculated server-side** based on the `current_user.id` and the `BoatCrew` table.

## Gotchas

- **Requires a published resume.** If a boat exists but its `BoatResume.published` flag is `False`, this endpoint returns a 404. This is a common source of confusion when a boat is visible in search but fails to load the detail view.
- **Owner identity is sensitive.** The endpoint pulls `owner.first_name` and `owner.last_name` directly. Ensure that any UI displaying this data adheres to the privacy expectations established in the `boatfinder.contact` permission flow.
- **Recent schema expansion:** Per commit `7aae433`, this endpoint was recently updated to include `banner_url` and `picture_url`. If adding new media fields to the boat profile, they must be explicitly added to the `BoatFinderProfileDetail` response model and the `get_boat_detail` return statement.

## Cross-cutting concerns

- **Auth**: Requires `boatfinder.view` permission.
- **Audit**: N/A.
- **Side effects**: The `viewer_is_crew` flag determines the visibility of the contact/apply UI components in the web frontend.

## External consumers

- `concorda-web` (via `boatfinderApi.getDetail`)
