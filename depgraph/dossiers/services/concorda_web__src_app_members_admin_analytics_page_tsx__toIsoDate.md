---
node_id: concorda-web::src/app/members/admin/analytics/page.tsx::toIsoDate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8344dca869d834353814f9b3089d075af82a6736046b893b5adf2f28fc15c581
status: current
---

# toIsoDate

## Purpose

A low-level utility to convert year, month, and day integers into a zero-padded ISO date string (`YYYY-MM-DD`). It is used by `presetRange` to transform date components derived from `ymdInOrgTz` into a format compatible with the `analyticsApi` endpoints.

## Invariants

- **Input is numeric.** Expects `y` (year), `m` (0-indexed month), and `day` (1-indexed day).
- **Returns a string.** The output is always a string in the format `YYYY-MM-DD`.
- **Month is 0-indexed in input.** The function adds `1` to the month parameter to convert from 0-indexed JavaScript date logic to 1-indexed ISO string representation.
- **Padding is mandatory.** Uses `padStart(2, "0")` on both month and day to ensure valid ISO 86 form.

## Gotchas

- **Per commit `f444b4c`, date logic must be driven by the organization's timezone.** This function is a building block for `presetRange`, which relies on `ymdInOrgTz` to ensure that "Today" or "Last 7 days" reflects the organization's local date rather than the user's browser time. If this logic were to use a standard `new Date()`, it would cause a drift where an admin in a different timezone sees the wrong analytics window.

## Cross-cutting concerns

- **Auth**: Protected by `PermissionGate` with `admin.users.view` at the `AnalyticsPage` level.
- **Side effects**: Used to calculate the date ranges for `analyticsApi.summary`, `topEndpoints`, `activeUsers`, and `dailyActivity`.

## External consumers

None known.
