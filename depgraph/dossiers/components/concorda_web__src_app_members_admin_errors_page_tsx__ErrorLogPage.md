---
node_id: concorda-web::src/app/members/admin/errors/page.tsx::ErrorLogPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2adc14a3a22262d0e0ceb341c1d70396ff10b0e24ea5bb2e709bb7d45d1bf703
status: llm_drafted
---

# ErrorLogPage

## Purpose

The `ErrorLogPage` is an administrative dashboard used to monitor system health, specifically tracking 5xx exceptions and 429 rate-limiting events. It provides a high-level view of recent errors and allows admins to drill down into specific error details. This component is distinct from general audit logs, as it focuses on operational failures rather than user-driven business events.

## Invariants

- **Permission Requirement**: Access is guarded by the `admin.audit.view` permission via the `SettingsPage` wrapper.
- **Data Fetching**: Uses `adminErrorLogApi.list` to fetch a list of up to 200 error entries.
- **Detail Retrieval**: Clicking an error triggers `adminErrorLogApi.get(id)` to fetch the full error context.
- **State Management**: The component manages three distinct loading/error states: `refreshing` (for the list), `loadingDetail` (for the specific error), and `error` (for API failures).

## Gotchas

- **Alert Suppression**: Per the subtitle in the source, the "bell icon" logic (cooldown) is handled server-side to suppress repeat notifications; the UI only reflects whether the alert was fired, not the frequency of the underlying error.
- **Error Type Handling**: The `catch` blocks in both `load` and `handleOpenDetail` explicitly check `err instanceof Error` to extract the message, ensuring the UI displays a human-readable string rather than an opaque object.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission.
- **Audit**: Displays 5xx exceptions and 429 rate-limit events (the source of the error data).
- **Side effects**: The "cooldown" mechanism mentioned in the subtitle implies that the visibility of the alert status is tied to the server-side suppression logic.

## External consumers

None known.
