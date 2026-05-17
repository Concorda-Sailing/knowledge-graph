## Prediction (written before running classifier)

Function: `test_create_event` in `tests/test_api.py` with decorator
`@router.post`.

This function satisfies two independent classifier predicates:

1. **test_kind**: file is `tests/test_api.py` → `_in_test_file` returns True
   (filename starts with "test_"). Name `test_create_event` starts with "test".
   Condition (c) in test_kind fires.

2. **endpoint**: decorator `router.post` is in `config.route_decorators`.
   Endpoint predicate fires independently of file location.

Classifier order: test_kind runs first, endpoint runs after. Engine logic:
- test_kind returns decision → `decisions[id] = Decision(kind="test", ...)`.
- endpoint returns decision → prior.kind is "test" != "endpoint" →
  `prior.conflicts.append("endpoint")`.

Prediction: `kind = "test"`, `conflicts = ["endpoint"]`.

## Actual result (after running)

`kind = test`, `conflicts = ['endpoint']`. Matches prediction exactly.

## Conflict mechanism confirmed

This is the genuine conflict case the fixture is designed to pin. The engine
records conflicts without crashing, without silently resolving, and without
losing the original classification. The first classifier to fire wins; all
subsequent classifiers that would fire for the same id append to `conflicts`.

The fixture name `classification_conflict_logged` refers to this accumulation
behaviour in `Decision.conflicts`. There is no separate logging call; the
conflict is recorded in the Decision dataclass and can be surfaced by any
consumer (graphui, linters, reports).

## Why endpoint_AND_service_conflict doesn't produce a conflict

See that fixture's verification.md. Service explicitly skips nodes already
classified as endpoint. The test+endpoint case works because the endpoint
classifier has no guard against test-file functions — it only checks for
route decorators regardless of file location.
