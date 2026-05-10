---
node_id: concorda-web::src/app/members/socials/page.tsx::PlanProgress
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a051ea8293512b5a443348be6d34c8c41036c086d886380e2476845dad78d8d
status: llm_drafted
---

# PlanProgress

## Purpose

Visualizes the completion status of a `ScheduleItem` through a horizontal step indicator. It uses `getPlanProgress` to determine which stages of a plan (e.g., docking, crew selection, crew confirmation) are complete and renders them as a sequence of labeled badges. This provides a high-level status overview for users viewing the socials calendar or schedule details.

## Invariants

- **Requires a `scheduleItem`** — The component relies on the `getPlanProgress` helper to map the item's state to the `PLAN_STEPS` array.
- **Returns `null` if no progress is found** — If `getPlanProgress` returns a falsy value, the component renders nothing rather than an empty container.
- **Uses `PLAN_STEPS` for iteration** — The visual order and number of steps are strictly driven by the `PLAN_STEPS` constant.
- **Step-based styling** — Completed steps are styled with `bg-primary/10` and a `Check` icon, while incomplete steps use `bg-muted`.

## Gotchas

- **Timezone dependency** — While this component specifically handles the progress bar, its parent `SocialCard` is highly sensitive to timezone rendering. Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone rather than the browser's local time to avoid displaying incorrect event times to users.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Visual state is driven by the `ScheduleItem` state; changes to crew confirmation or dock status in the admin dashboard will reflect here.

## External consumers

None known.
