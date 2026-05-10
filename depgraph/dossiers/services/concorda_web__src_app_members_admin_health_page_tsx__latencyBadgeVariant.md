---
node_id: concorda-web::src/app/members/admin/health/page.tsx::latencyBadgeVariant
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7c79f42c8500ea92e2382aa176c4320f427d52cf8f89e6b74de42fcdcb14ab8b
status: current
---

# latencyBadgeVariant

## Purpose

Determines the visual severity level of a latency badge based on a millisecond threshold. It maps a numeric latency value to a UI variant (`"default"`, `"secondary"`, or `"destructive"`) to provide immediate visual feedback on API performance. This is distinct from `poolBadgeVariant`, which tracks resource saturation rather than time-based latency.

## Invariants

- **Input is a number** representing milliseconds (`ms`).
- **Returns a string literal** of type `"default" | "secondary" | "destructive"`.
- **Thresholds are fixed:** `500ms` triggers `"secondary"` and `2000ms` triggers `"destructive"`.
- **Order of evaluation matters:** The function checks the highest threshold (`2000`) first to ensure high latency is flagged as destructive before falling back to secondary.

## Gotchas

- **Hardcoded thresholds:** The thresholds (500 and 2000) are hardcoded in the function body. If the definition of "slow" changes for the organization, this function must be updated to prevent the UI from being perpetually in a "destructive" state during normal high-load periods.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission via the `SettingsPage` wrapper in the parent component.
- **Side effects**: Visual state of the `HealthPage` latency indicators depends on this function.

## External consumers

None known.
