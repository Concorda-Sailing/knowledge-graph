---
node_id: concorda-web::src/components/dashboard/profile-completion.tsx::buildTasks
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e21e4762f1edfd109f46221e0c9b5f04daa227d07b4ea7c8ddcd2718a3b8ddf9
status: llm_drafted
---

# buildTasks

## Purpose

Generates a list of actionable `Task` objects used to drive the "Profile Completion" UI in the user dashboard. It evaluates the completeness of a user's `Profile`, `SailingResume`, and `Boat` data to provide specific feedback on what information is missing (e.g., "About me", "Race areas") and provides direct links to the relevant profile or boat configuration tabs.

## Invariants

- **Input requirement**: Requires a `Profile`, a potentially null `SailingResume`, and an array of `Boat[]`.
- **Output shape**: Returns an array of `Task` objects, each containing a `label`, `description`, `done` (boolean), `missing` (string array), and a `href` for navigation.
- **Navigation target**: All profile-related tasks (picture, resume, preferences) target the `/members?tab=profile` route.
- **Boat logic**: If the `boats` array is non-empty, a specific task is injected that links directly to the first boat's configuration via `?tab=boats&boat=${boats[0].id}`.

## Gotchas

- **Implicit dependency on `getResumeMissing` and `getPrefsMissing`**: The completeness of the "Sailing Resume" task is strictly tied to these helper functions. If a field is added to the `SailingResume` type, these must be updated to ensure the task doesn't report a false positive for completion.
- **Boat detail requirement**: Per commit `a29494e`, the boat task is designed to inline boat details; if the `boats` array is empty, the task is omitted entirely, meaning users with no boats won't see a prompt to "Complete your boat profile."

## Cross-cutting concerns

- **Auth**: Relies on the authenticated user's `Profile` and `SailingResume` data fetched via the session.
- **Side effects**: Updates to the profile completion status are driven by the user's interaction with the `/members?tab=profile` and `/members?tab=boats` routes.

## External consumers

None known.
