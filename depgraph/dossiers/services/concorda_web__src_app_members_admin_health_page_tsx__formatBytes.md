---
node_id: concorda-web::src/app/members/admin/health/page.tsx::formatBytes
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d00711a8f11615c817f6ec06cb2eee2da595aa08f617156adb1c21c84e73c933
status: current
---

# formatBytes

## Purpose

A utility function for converting numeric byte counts into human-readable strings (B, KiB, or MiB). It is used within the `HealthPage` component to display database pool statistics. Use this when displaying memory or buffer sizes in the admin health dashboard to ensure consistent binary prefix notation.

## Invariants

- **Input is a number or null.** If the input is `null`, the function returns the em-dash string `"—"`.
- **Uses binary prefixes.** Calculations are based on powers of 1024 (KiB/MiB) rather than decimal powers (KB/MB).
- **Returns a string.** The output is always a string formatted for UI display.

## Gotchas

- **Manual null handling required.** The function does not throw on `null`; it returns `"—"`. If a caller expects a number or an empty string, they must account for this specific string return.

## Cross-cutting concerns

- **Auth**: Requires `adminHealthApi` access (implicitly requires admin-level authentication/authorization).
- **Side effects**: Used to render the `pool` stats in the `HealthPage` dashboard.

## External consumers

None known.
