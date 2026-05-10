---
node_id: concorda-web::src/app/members/agents/page.tsx::AgentsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b180582715408c570cfe6e0d95ce5227f4cea11e9f5fa1870692132d08fccda5
status: current
---

# AgentsPage

## Purpose

The administrative interface for managing machine-to-machine (agent) access tokens. It allows users to create new agents with specific names, rotate existing tokens to refresh secrets, and revoke access. This page is the primary interface for managing programmatic access for external integrations or automated processes.

## Invariants

- **`agentTokensApi` is the sole data provider** for listing, creating, rotating, and revoking tokens.
- **`MAX_TOKENS` governs the `atLimit` state**, which triggers a visual warning if the number of active (non-revoked and non-expired) tokens exceeds the threshold.
- **`activeCount` calculation is client-side**, filtering the `tokens` list based on `revoked_at` and `expires_at` timestamps.
- **`handleCreate` requires a non-empty, trimmed `name`** to proceed with the API call.

## Gotchas

- **Timezone-aware rendering is mandatory.** Per commit `f444b4c`, all backend datetimes (like `expires_at`) must be rendered using the organization's timezone rather than the browser's local time to prevent misleading expiration displays.
- **The `secretShown` state is transient.** When a new agent is created or a token is rotated, the secret is held in local state (`secretShown`) to allow the user to copy it before it is lost on the next refresh or navigation.

## Cross-cutting concerns

- **Auth**: Relies on the authenticated session established by the `ApiClient` (or equivalent) to authorize `agentTokensApi` calls.
- **Side effects**: Creating or rotating a token updates the `tokens` list via the `refresh()` call, which is the primary way the UI stays in sync with the backend state.

## External consumers

None known.
