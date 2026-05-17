## Prediction (written before running classifier)

The function `get_events` has `@router.get` (endpoint predicate fires) AND a
direct `db_access` edge (would satisfy service's side-effect requirement).

Prediction: `kind = endpoint`, `conflicts = ["service"]`.

Rationale: endpoint classifier runs before service. Service would need to also
fire on this id and record the conflict. The service classifier does BFS from
endpoints, but then guards with `if p["id"] in endpoints: continue`. So service
skips functions that are already classified as endpoint.

## Actual result (after running)

`kind = endpoint`, `conflicts = []`.

## Discrepancy

Prediction was wrong about conflicts. The service classifier's endpoint-guard
(`if p["id"] in endpoints: continue`) prevents service from ever returning a
decision for a node that is itself an endpoint. Since service returns no
decision for this id, the engine's conflict-recording branch never fires.
`Decision.conflicts` stays empty.

## Design note

The guard is correct behaviour: an endpoint that directly issues a DB query
is still an endpoint, not a service. The service classification only applies
to functions *called by* endpoints, not to the endpoints themselves. The
`endpoint_AND_service_conflict` name reflects the intent of the fixture (can
these two predicates conflict on one node?) — the answer is no, by design.

For a genuine conflict between classifiers on one node see the
`classification_conflict_logged` fixture (test + endpoint on a function in a
test file with a route decorator).
