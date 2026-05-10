---
node_id: concorda-web::src/app/members/admin/memberships/page.tsx::AdminMembershipsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 917aca7a5483013570d20588f868b94a3b93f9b35d6be7464613e263ad236b1c
status: current
---

# AdminMembershipsPage

## Purpose

The administrative dashboard for viewing high-level membership statistics. It provides a summary of current year registration status, total member counts, and active/pending status via the `adminApi.stats()` endpoint. This page is intended for organization admins to monitor the health of their membership base at a glance.

## Invariants

- **Requires `admin.memberships.view` permission** via the `PermissionGate` component to prevent unauthorized access to sensitive membership counts.
- **Relies on `adminApi.stats()`** to populate the dashboard; if the API call fails, the component defaults to showing `0` or `null` values rather than crashing.
- **Uses the `Stats` interface** for type safety; the `total_members` and `active_members` fields are expected to be numeric.

## Gotchas

- **Type safety requirement:** Per commit `dfcc7db`, this component must use the explicit `Stats` interface rather than a generic `Record<string, unknown>` to ensure the `total_members` and `active_members` properties are correctly accessed and typed.

## Cross-cutting concerns

- **Auth**: Protected by `PermissionGate` with the `admin.memberships.view` permission.
- **Side effects**: Displays data derived from the `adminApi.stats()` endpoint.

## External consumers

None known.
