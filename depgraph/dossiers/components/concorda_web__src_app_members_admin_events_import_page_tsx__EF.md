---
node_id: concorda-web::src/app/members/admin/events/import/page.tsx::EF
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d42ace3dd586d8717ed1aea6e8065bca1e3b076c1141d2cc3434982a0f2e8696
status: current
---

# EF

## Purpose

The `EF` component is a specialized input field used within the event import workflow. It provides a labeled, single-line text input for simple string values. It is distinct from `DateField` in that it does not handle timezone-aware datetime conversions; it is intended for raw string data like names or descriptions where no temporal logic is required.

## Invariants

- **Input is a raw string.** The `value` prop must be a string, and `onChange` returns the raw string value from the input event.
- **Uses standard `Input` styling.** It relies on the base `Input` component for height (`h-8`) and text size (`text-sm`) to maintain consistency with the admin import grid.
- **Placeholder is optional.** If no `placeholder` is provided, the input remains a standard empty-state input.

## Gotchas

- **Timezone-sensitive fields must NOT use `EF`.** Per commit `f444b4c` (fix(timezone)), all backend datetimes must be rendered and edited using `DateField` to ensure they are rendered in the organization's timezone rather than the browser's local time. Using `EF` for dates will result in the loss of the UTC-to-Org-TZ conversion contract.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.
