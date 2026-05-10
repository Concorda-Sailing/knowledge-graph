---
node_id: concorda-test::tests/dashboard/mobile-dashboard.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c9abaf2251133d2ec258f17a2c57308ea91b0c509029f3093a4d6dccf2aad5c2
status: llm_drafted
---

# dashboard tab list does not wrap at 375px

## Purpose

Verifies the layout integrity of the dashboard tab list on mobile viewports. Specifically, it ensures the `tablist` does not wrap to a second row at a width of 375px and that the vertical height remains within a reasonable threshold (~60px). This prevents UI regressions where navigation elements stack vertically and consume excessive screen real estate on small devices.

## Invariants

- **Viewport width is fixed at 375px** for the duration of the test to simulate mobile dimensions.
- **`tablist` must be a single row.** The height of the `role="tablist"` element must be less than 60px.
- **Navigation is non-wrapping.** The test fails if the `boundingBox().height` exceeds the threshold, indicating a layout break.

## Gotchas

- **Layout is sensitive to viewport width.** Recent changes in `dc55160` (dashboard mobile: dashboard mobile viewport + sidebar IA cleanup) suggest the mobile layout and sidebar interaction are currently being refined; ensure any changes to the `tablist` component do not inadvertently trigger a wrap at the 375px breakpoint.

## Cross-cutting concerns

- **Auth**: Uses `storageState: 'auth-states/member.json'` via the desktop regression block, though this specific test relies on the `/members` route being accessible.
- **Side effects**: Layout regressions here can break the visual hierarchy of the "pending invite banner" and the "upcoming event" cards if the tab list expands too far vertically.

## External consumers

None known.
