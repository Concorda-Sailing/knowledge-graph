---
node_id: concorda-web::src/lib/api.ts::boatfinderApi.getDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cd3726566a21cb09fb497f67926b975f98d443295eed4919025f3042221d400b
status: llm_drafted
---

# boatfinderApi.getDetail

## Purpose

Fetches detailed profile information for a specific boat/crew entry via the `/api/boatfinder/detail/{boatId}` endpoint. This is the primary method for retrieving the full context of a boat (such as its specific configuration or status) when a user navigates to a detail view. It is distinct from `list`, which is used for filtered searches, and `apply`, which is used to submit a membership/interest request.

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to execute the request.
- **Input is a `boatId` string** — must be URI-encoded via `encodeURIComponent` to prevent path traversal or malformed requests.
- **Returns a `BoatCrewfinderProfileDetail` object** — the shape of this object is the source of truth for the detail view UI.

## Gotchas

- **Dependency on `boat_config_id`** — per commit `bf15808`, the system was updated to use a stored `boat_config_id` instead of relying on shape-matching. Ensure any logic consuming this detail view respects the specific configuration ID rather than attempting to infer it from the object structure.
- **Relationship to `apply`** — while this fetches the detail, the actual interaction (applying to join/co-own) is handled by the sibling `apply` method.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires a valid user session.
- **Side effects**: The data returned here populates the `BoatDetailPage` in the members/boatfinder route.

## External consumers

- `concorda-web::src/app/members/boatfinder/[id]/page.tsx` (BoatDetailPage)
