---
node_id: concorda-web::src/app/members/admin/health/page.tsx::poolBadgeVariant
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6f4e35f101333337bde191df8eaee85c0aea5a85b103ba37e5a16a6d418ecaf1
status: current
---

# poolBadgeVariant

## Purpose

Determines the visual severity level of the database pool status. It maps the ratio of `checkedOut` connections to total `capacity` to a UI variant (`default`, `secondary`, or `destructive`). This is used to provide immediate visual feedback on database pressure within the Admin Health page.

## Invariants

- **Returns a string literal** of type `"default" | "secondary" | "destructive"`.
- **`capacity` is the denominator.** If `capacity` is 0, it returns `"default"` to avoid division by zero or NaN issues.
- **Thresholds are fixed:** `"secondary"` is triggered at $\ge 60\%$ utilization; `"destructive"` is triggered at $\ge 90\%$ utilization.
- **Input types are numeric.** The function expects `number` for both arguments.

## Gotchas

- **Capacity calculation is external to this function.** The `capacity` passed in is derived from `pool.pool_size + pool.max_overflow` in the parent component. If the definition of "capacity" changes in the backend, this function's thresholds may become misleading.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission via the parent `SettingsPage`.
- **Side effects**: Visual state of the DB pool status indicator in the Health page.

## External consumers

None known.
