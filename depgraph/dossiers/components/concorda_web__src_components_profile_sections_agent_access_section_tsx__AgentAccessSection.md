---
node_id: concorda-web::src/components/profile/sections/agent-access-section.tsx::AgentAccessSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7cad5ed8c3cbacee25d52b2045d5d263da20cdd2d0623fa0e8658ca70502e48a
status: llm_drafted
---

# AgentAccessSection

## Purpose

A UI component that displays the status and entry point for AI agent access within the user profile. It serves as a high-level informational card, signaling to the user that their data (schedule, profile, and crew commitments) can be shared with LLMs like Claude or ChatGPT. It provides a direct link to the `/members/agents` management route.

## Invariants

- **Static UI structure**: The component is a purely presentational wrapper around a `Card` and a `Link`.
- **Navigation target**: The "Manage access" button must always link to `/members/agents`.
- **Visual identity**: Uses the `Bot` icon from `lucide-react` and the `primary` color scheme to distinguish agent-related features from standard profile settings.

## Gotchas

- **Recent UI polish**: Per commit `f1886fd`, this component was part of a recent "sail flow + UI polish" push which included adding analytics date ranges. Ensure any styling changes to the `Card` or `Button` maintain the established visual density of the profile sections.

## Cross-cutting concerns

- **Auth**: None (this is a static link; actual permission checks occur on the `/members/agents` route).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.
