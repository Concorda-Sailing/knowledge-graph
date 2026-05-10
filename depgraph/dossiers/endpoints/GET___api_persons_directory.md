---
node_id: GET::/api/persons/directory
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 22571e464f7d9254751b4d9d65a21505bd4aa06e76afe3a1a0c898547409dcf2
status: current
---

# GET /api/persons/directory

## Purpose
Endpoint handler for the member directory — returns the `Person` list filtered to those who have set `preferences.directory.opt_in == True`, with per-row privacy controls (`show_phone`, `show_email`) applied while building the `PersonDirectory` response. Also bulk-resolves a `has_boat_management` flag (via `PersonProduct` → `TemporalProduct.grants_boat_management`) so the calling UIs can gate the co-owner invite action without N+1 lookups. Three frontend callers depend on it: `directoryApi.list` in `lib/api.ts`, plus the `BoatCrewInvite` and `InviteCoownerDialog` components which both consume it to populate invite pickers.

## Invariants
- Only members with `preferences.directory.opt_in == True` may appear. Opt-in is per-person and authoritative; do not infer it from membership status.
- `email` and `phone_number` are emitted only when the row's own `directory.show_email` / `show_phone` are truthy. Defaults are off — missing keys mean "do not expose."
- Endpoint requires authentication (`require_auth`). Even when `show_email`/`show_phone` are on, contact info must never be reachable anonymously — see docstring and the `33a37a3` security commit.
- `has_boat_management` is computed from `TemporalProduct.grants_boat_management`, not membership name or slug. Keep that the source of truth so new products don't silently lose eligibility.
- Search activates only when `q` has length ≥ 2; ordering is `(last_name, first_name)` and callers rely on stable alphabetical order.

## Gotchas
- `33a37a3 fix(security): close PII / privilege gaps in roles, finder, directory, media` — this endpoint specifically had PII leakage closed. Any change that broadens the response (new fields, looser filters, optional auth) should re-walk that commit's intent before merging.
- `8f94a94 feat(coowner): surface boat-management eligibility` added the bulk `boat_mgmt_ids` query. Resist the urge to inline `person.memberships` per row — the explicit comment says "rather than N round-trips," and the invite UIs render dozens of rows.
- `func.json_extract(... "$.directory.opt_in") == True` is a SQLite-flavored predicate. JSON1 returns 1/0, and `== True` works because SQLAlchemy compares to integer truthiness; on a Postgres migration this filter will need to be rewritten.
- `person.memberships[0].product.name` is unordered — "first" membership is arbitrary. Acceptable for a display label today; do not rely on it for authorization.
- `noqa: E712` on `grants_boat_management == True` is intentional (SQL boolean comparison, not a Python bool check). Don't "fix" it to `is True`.

## Cross-cutting concerns
- **Auth**: `require_auth` only — any logged-in user sees the directory. There is no org-scoping; cross-org members are visible if opted in. Revisit if multi-org isolation becomes a requirement (org_admin grandfather note in memory is adjacent).
- **Privacy**: per-row redaction happens server-side; clients must never receive masked contact info. Don't move redaction to the frontend.
- **Performance**: single bulk query for boat-management eligibility. Adding more derived flags (e.g., crew-pool membership) should follow the same bulk pattern.
- **No websocket/audit side effects**: read-only endpoint, no `broadcast_event`, no writes.

## External consumers
None known. All three direct dependents are first-party web components/clients. The Expo iOS app does not currently call this endpoint (verify before assuming).

## Open questions
- Should the directory be org-scoped once Tier C lands? Today a Mass Bay member can see opted-in members from any org sharing the deployment.
- `q` searches `email` even for rows where `show_email` is false — a user can confirm an email exists by typing it. Intentional, or a small leak worth closing?
