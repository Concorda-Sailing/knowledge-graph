---
node_id: concorda-web::src/app/members/agents/page.tsx::tokenStatus
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 821901d9a7407f18ea756be1faefc3dc2e5290e04dd5f95c7f70ac62da57dd53
status: llm_drafted
---

# tokenStatus

## Purpose

Determines the visual status of an agent token by evaluating its lifecycle state. It maps the raw `AgentTokenSummary` data into a UI-friendly object containing a human-readable label and a semantic tone. This is used to drive the color/styling of the token status badges in the Agents UI.

## Invariants

- **Input is `AgentTokenSummary`** — expects an object with `revoked_at` and `expires_at` fields.
- **Returns a status object** — always returns an object with `{ label: string; tone: "active" | "expired" | "revoked" }`.
- **Priority is Revocation** — if `revoked_at` is present, the status is "Revoked" regardless of the expiration date.
- **Expiration is checked against current time** — uses `new Date()` to determine if a token has passed its `expires_at` threshold.

## Gotchas

- **Must use organization timezone for display** — per commit `f444b4c`, all datetime rendering in this module must avoid browser-local time. While `tokenStatus` performs the logic check, any subsequent rendering of the `expires_at` string via `formatDate` must use `formatInOrgTz` to ensure consistency with the fix.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Affects the visual state of the agent token list in the `AgentsPage`.

## External consumers

None known.
