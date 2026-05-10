---
node_id: concorda-web::src/app/members/socials/page.tsx::getPlanProgress
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 871b69b7873feb2e88d176d970a2b4ffdd4b733df5071d9c3ea723653e76f0bf
status: llm_drafted
---

# getPlanProgress

## Purpose

Calculates the completion status of a sailing event's planning lifecycle. It derives a boolean state for four specific stages—`dock`, `crew_selected`, `crew_confirmed`, and `ready`—based on the presence of a `sailing_event` and its associated metadata. This function is used to drive the visual progress indicator in the `PlanProgress` component.

## Invariants

- **Input is a `ScheduleItem`** — The function expects an optional `ScheduleItem`. If `scheduleItem` or `scheduleItem.sailing_event` is missing, it returns `null`.
- **`ready` is a derived state** — The `ready` key is only `true` if `dock`, `allFilled`, and `crew_confirmed` are all truthy.
- **`crew_selected` depends on `positions_needed`** — This is determined by checking if every position object in the `positions_needed` array has a non-null `filled_by_uuid`.
- **`dock` requires two fields** — Both `dock_time` and `departure_location` must be present on the `sailing_event` to satisfy the `hasDock` condition.

## Gotchas

- **Timezone sensitivity** — Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. While this function calculates logical progress, any UI displaying the time-based triggers for these steps (like `dock_time`) must use the `tz` provided to the parent component to avoid local browser drift.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the visual state of the `PlanProgress` stepper in the Socials/Schedule views.

## External consumers

None known.
