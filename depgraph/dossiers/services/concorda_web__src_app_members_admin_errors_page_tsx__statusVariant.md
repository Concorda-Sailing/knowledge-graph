---
node_id: concorda-web::src/app/members/admin/errors/page.tsx::statusVariant
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e01a481cd85bcf78d7c52b9936a82b6103fb4a5cf34035060e34d012f7383394
status: llm_drafted
---

# statusVariant

## Purpose

Maps HTTP status codes to UI visual styles for the error log table. It determines whether a row should be rendered with a "destructive" (error), "secondary" (rate limit), or "default" (normal) visual weight. This ensures that critical 5xx failures are visually distinct from transient 429 rate-limiting events.

## Invariants

- **Input is a numeric status code.** The function expects a `number` representing an HTTP response status.
- **Returns a Shadcn/UI compatible variant.** The output is strictly limited to `"default" | "destructive" | "secondary"`.
- **5xx codes map to "destructive".** Any status code 500 or higher is treated as a high-priority error.
- **429 maps to "secondary".** This specifically targets rate-limiting events to distinguish them from actual server crashes.

## Gotchas

- **Hardcoded threshold logic.** The distinction between a "critical error" and a "rate limit" is hardcoded via the `status >= 500` and `status === 429` checks. If the API introduces new status-based alerting logic (e.g., a new 4xx error that requires a "destructive" highlight), this function must be updated manually.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission via the `SettingsPage` wrapper in the parent component.
- **Audit**: Visualizes data retrieved from `adminErrorLogApi.list`, which tracks 5xx exceptions and 429 rate-limits.
- **Side effects**: The visual state of this variant directly impacts the visibility of the "alert email" status mentioned in the `SettingsPage` subtitle.

## External consumers

None known.
