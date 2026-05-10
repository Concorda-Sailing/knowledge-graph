---
node_id: GET::/api/regattas/{0}/match-roster
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e4f78c7513103f0c7a49ff6b04fe56c1a82e8ad376aca6f74c6ce1c381ad94bc
status: current
---

# GET /api/regattas/{regatta_id}/match-roster

## Purpose

Retrieves the available boats and crew members for a specific regatta. It is a permission-gated endpoint that selectively returns data based on the user's specific viewing rights. Unlike standard regatta detail endpoints, this is optimized for the "finder" view, where the presence of the `boats` or `crew` sections in the response is determined by whether the user holds `boatfinder.view` or `crewfinder.view` permissions respectively.

## Invariants

- **Method is GET** and requires a valid `regatta_id`.
- **Requires `require_auth`** via the `current_user` dependency.
- **Returns a `MatchRoster` object** which may have conditional fields based on permissions.
- **Throws 404** if the `regatta_id` does not exist in the database.
- **Throws 403** if the user lacks both `boatfinder.view` and `crewfinder.view` permissions.

## Gotchas

- **Tier-C scope enforcement:** Per commit `058aa8c`, this endpoint is subject to strict cross-org scope enforcement. Ensure that the `regatta_id` belongs to the user's organization to avoid unauthorized access.
- **Permission-dependent response shape:** The presence of boat or crew data is not guaranteed. If a user has `boatfinder.view` but not `crewfinder.view`, the `crew` section of the `MatchRoster` will be omitted or empty.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and checks for specific permission strings (`boatfinder.view` or `crewfinder.view`).
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: N/A

## External consumers

- `concorda-web::src/lib/api.ts::regattaApi.getMatchRoster`
