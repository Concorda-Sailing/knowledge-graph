---
node_id: GET::/api/crewfinder/detail/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 60c228dbd416cbe947053128c802a8186e4e89fadfe056bbd61fb3df937de914
status: llm_drafted
---

# GET /api/crewfinder/detail/{person_id}

## Purpose

Fetches detailed profile information for a specific person within the crew finder. It provides a distinction between a "stub" profile (used when a person has not yet published a `SailingResume`) and a full profile, ensuring the frontend can render a consistent UI even for unpublished data. It also implements complex visibility logic: data is only exposed if the user has opted into the crew finder OR if the requester is a boat owner with an active relationship (owner/invitee/prospective) to the person.

## Invariants

- **Requires `crewfinder.view` permission** via the `require_permission` dependency.
- **Returns a `CrewfinderProfileDetail` object.** The shape is dictated by the `response_model` and includes fields for both basic person data and expanded resume data.
- **Strict visibility gating.** If `prefs.get("opt_in")` is false and the user is not a verified boat owner of the person, a `404` is raised.
- **PII protection.** `email` and `phone_number` are explicitly set to `None` if the person's preferences or the owner-override do not permit visibility.
- **Fallback behavior.** If no `SailingResume` exists, the endpoint returns a profile with empty resume fields rather than a 404, allowing the UI to show a "not published" state.

## Gotchas

- **PII/Privilege Gap:** Per commit `33a37a3`, this endpoint was part of a security hardening effort to ensure sensitive fields (email/phone) are strictly gated by both user preferences and the `is_boat_owner_of_person` check.
- **Unpublished Resume Logic:** As noted in the source comments (line 371), the absence of a `SailingResume` is a valid state, not an error. The frontend must handle the "stub" profile to avoid breaking when a user hasn't filled out their sailing details.
- **Owner-Override Logic:** A user can see a person's contact info even if the person has `opt_in: false`, provided the user is an active owner of a boat associated with that person (see lines 344-359).

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `crewfinder.view` permission.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The visibility of this data affects how the "crew finder" search results are presented to boat owners vs. general users.

## External consumers

- `concorda-web` (via `crewfinderApi.getCrewDetail`)
