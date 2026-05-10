---
node_id: concorda-web::src/components/admin/response-time-drilldown.tsx::statusBadgeVariant
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 833561c9428560286fca661644dbf64170e955c71d3c8acc03d892f42df6eccf
status: llm_drafted
---

# statusBadgeVariant

## Purpose

Determines the visual severity of a status badge based on a numeric status code. It maps status ranges to specific UI variants (`default`, `secondary`, or `destructive`) to provide immediate visual feedback on API health. This is a pure helper used within the `ResponseTimeDrilldown` component to color-code the status of specific API paths.

## Invariants

- **Input is a numeric status code.** It accepts `number | null`.
- **Returns a string literal.** The return type is strictly `"default" | "secondary" | "destructive"`.
- **Null/Undefined handling.** If the input `s` is `null` or `undefined`, it returns `"default"`.
- **Thresholds are fixed.** `s >= 400` triggers `secondary` (warning/client error), and `s >= 500` triggers `destructive` (critical/server error).

## Gotchas

- **Visual hierarchy is order-dependent.** The function checks `s >= 500` before `s >= 400`. If the order were reversed, a 500 error would be incorrectly flagged as `secondary` instead of `destructive`.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Used to color the status indicators in the `ResponseTimeDrilldown` drawer, which visualizes the health of the `adminHealthApi` endpoints.

## External consumers

None known.
