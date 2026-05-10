---
node_id: GET::/api/organizations/delegates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 53d68f9de16b4f392e83b86460340fdcd3bce23076d218e4751a84db90d91a5a
status: current
---

# GET /api/organizations/delegates

## Purpose

Provides a public-facing directory of member organizations and their associated delegates. It filters the `Organization` table specifically for high-level entities (Yacht Clubs, Associations, and Sailing Centers) and joins the `Person` data via the `steward_id` to surface contact details. Use this endpoint for the "Member Directory" or "Directory" views where a user needs to see who the primary contact/steward is for a specific club.

## Invariants

- **Returns a list of `_DelegatesEntry` objects.** Each entry contains a full `OrganizationRead` object and an optional `_DelegatePublic` object.
- **Filters by `org_type`.** Only organizations with types `"Yacht Club"`, `"Association"`, or `"Sailing Center"` are returned.
- **Ordering is alphabetical.** Results are ordered by `Organization.name`.
- **`delegate` is nullable.** If a club has no `steward_id` or the ID does not resolve to a person, the `delegate` field is `null`.

## Gotchas

- **Hard-coded type filter.** Per commit `45f2bec`, this endpoint was updated to include "Sailing Centers" and "Associations" in the filter. If a new organization type is added to the system, it will not appear in this list unless the filter in `list_delegates` is explicitly updated.
- **Implicit join via `steward_id`.** The function performs a manual lookup for the `Person` record. If the `steward_id` exists but the `Person` record has been soft-deleted or is missing, the `delegate` field returns as `null` rather than failing the request.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible/Member-facing).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `concorda-web::src/lib/api.ts::organizationsApi.delegates` to populate directory components.

## External consumers

- `concorda-web` (via `organizationsApi.delegates`)
