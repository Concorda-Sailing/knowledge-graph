---
node_id: concorda-web::src/app/members/admin/llm/page.tsx::LLMConfigPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bb01bdaf34aaf474ed72b422ceba0d7aed18213f39dc955124e7dc792a019f0c
status: llm_drafted
---

# LLMConfigPage

## Purpose

The administrative interface for configuring the LLM provider settings (provider, base URL, model, and API key) and managing system prompts. It serves as the central control plane for the AI-driven features of the application, allowing admins to switch between providers like Groq or OpenAI and adjust the active model.

## Invariants

- **Uses `fetchApiAuthenticated`** — All configuration updates and fetches must use this helper to ensure the request includes the necessary bearer token.
- **`vision_model` is optional** — If no vision model is provided, the payload must explicitly pass `undefined` (or omit it) to avoid breaking the API contract.
- **`api_key` is conditional** — The `api_key` field is only included in the `PUT` payload if the `apiKey` state is non-empty.
- **State synchronization** — The component performs a dual-fetch on mount (`/api/admin/llm-config` and `llmApi.listPrompts()`) to ensure the UI reflects both the provider settings and the current prompt list simultaneously.

## Gotchas

- **Mobile layout constraints** — Per commit `0564f06`, admin dialogs and subpages must account for width capping and footer stacking on `<md` breakpoints to prevent broken layouts on mobile devices.
- **UI/UX feedback loop** — The `setSaved(true)` state is transient; it uses a `setTimeout` of 3000ms to reset the "Saved" indicator, which may feel too short if the user is performing multiple rapid edits.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` for both GET and PUT operations.
- **Side effects**: Changes to the `model` or `base_url` directly impact the behavior of any downstream AI-driven features (e.g., the "scout" or "assistant" features) that consume these settings.

## External consumers

None known.
