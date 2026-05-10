---
node_id: concorda-web::src/components/dashboard/profile-completion.tsx::ProfileCompletion
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 95cd667f3242c1ada49b01664404be4fb90ad18f61832df3d5d0c3a3cf5bc7e3
status: llm_drafted
---

# ProfileCompletion

## Purpose

The `ProfileCompletion` component renders a checklist of onboarding tasks for new members. It visualizes progress by mapping a list of tasks (derived from `buildTasks`) to interactive links that guide users toward a complete profile. It is distinct from a simple progress bar because it provides specific "missing" context (e.g., what exactly is missing from a resume) to drive user action.

## Invariants

- **Input is a `ProfileCompletionData` object.** This must contain a `tasks` array and a `completed` count.
- **Task items are interactive links.** Each task must provide a `href` and a `label` to ensure the user can navigate to the relevant setup page.
- **Visual state is driven by `task.done`.** Completed tasks use a `line-through` text style and a muted color palette, while incomplete tasks use an amber-themed highlight to draw attention.
- **The `missing` array determines the "Needs" sub-text.** If `task.missing.length > 0`, the component renders a specific list of missing requirements to provide clarity.

## Gotchas

- **Onboarding-specific styling.** Per commit `23fb96c` (Add setup wizard for new member onboarding), the component uses a specific amber color scheme (`bg-amber-50`, `border-amber-300`) for incomplete tasks to differentiate "onboarding" tasks from standard dashboard alerts.
- **Data dependency.** The component relies on the `buildTasks` helper, which consumes `Profile`, `SailingResume`, and `Boat[]`. If the `getResumeMissing` or `getPrefsMissing` logic changes, the UI output for "Needs" will change implicitly.

## Cross-cutting concerns

- **Auth**: None (it is a purely presentational component driven by the `data` prop passed from a parent container).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Drives the user experience for the "Setup Wizard" flow introduced in recent onboarding updates.

## External consumers

None known.
