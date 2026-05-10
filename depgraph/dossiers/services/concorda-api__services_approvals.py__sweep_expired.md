---
node_id: concorda-api::services/approvals.py::sweep_expired
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6c4a76f812b2e10170e9cb0ce47d73547e5864be9de6dd253ee8861b6919f978
status: current
---

# sweep_expired

## Purpose

The `sweep_expired` function is a maintenance utility designed to transition `pending` approval requests to an `expired` state once their `expires_at` timestamp has passed. It serves as a cleanup mechanism to ensure that stale requests do not remain in a `pending` state indefinitely, preventing them from being accidentally resolved by late-arriving votes or manual actions.

## Invariants

- **Only targets `pending` requests.** A request must have a status of `"pending"` to be eligible for expiration.
- **Requires an expiration timestamp.** The function only selects requests where `expires_at` is not null and is strictly less than the current UTC time.
- **Uses `datetime.utcnow()` for comparison.** The comparison is performed against the current UTC time to maintain consistency with the `_finalize` method's timestamping.
- **Returns the count of expired requests.** The integer return value represents the number of requests transitioned from `pending` to `expired`.

## Gotchas

- **Double-finalize protection is critical.** Per commit `2fe8ad5`, the logic must ensure that a request cannot be transitioned to `expired` if it has already been resolved (e.g., by a vote or a manual cancellation). The `_finalize` function handles this by checking `if req.status != "pending": return`.
- **Rule-based logic complexity.** While this function handles the temporal expiration, the actual resolution logic (unanimous vs. majority) is handled by `_evaluate`. Ensure that `sweep_expired` does not bypass the status check required by the engine.

## Cross-cutting concerns

- **Auth**: none.
- **Websocket**: none.
- **Audit**: Y (updates `status` and `resolved_at` via `_finalize`).
- **Rate limit**: none.
- **Side effects**: Transitioning a request to `expired` may affect the visibility of requests in `list_requests_for_voter` or `list_requests_for_requester` if they filter by status.

## External consumers

Likely called by a periodic background task or a cron job to maintain database hygiene.

## Open questions

- Should the expiration logic be moved into a more generic `_evaluate` step to ensure that "expired" is treated as a formal resolution type consistent with "rejected" or "approved"?
