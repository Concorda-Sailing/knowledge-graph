---
node_id: concorda-web::src/components/admin/response-time-drilldown.tsx::formatRequestTime
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: af29645d6b575e6ed43bae7332789ae3a2fa6f7c7dbed12aed9349866e4a1652
status: llm_drafted
---

# formatRequestTime

## Purpose

The `formatRequestTime` helper normalizes and localizes raw database timestamps for the admin drilldown UI. It is distinct from the sibling inline formatters because it explicitly handles the conversion of plain SQL datetime strings (which lack a 'Z' suffix) into valid UTC ISO strings before passing them to `formatInOrgTz`. Use this when displaying timestamps from the `adminHealthApi` response-time endpoints to ensure the time is rendered in the organization's timezone rather than the viewer's local time.

## Invariants

- **Input is a raw SQL datetime string.** The function expects a string that may lack the `T` separator or the `Z` offset (e.g., `"2026-05-08 14:30:00"`).
- **Normalization is mandatory.** It must inject `"T"` and `"Z"` to ensure `formatInOrgTz` treats the input as UTC.
- **Output is a localized string.** The result is a human-readable string including year, month, day, hour, minute, and second.

## Gotchas

- **Must handle non-ISO strings.** Per commit `f444b4c`, the function must ensure backend datetimes are rendered in the org TZ. If the `iso.replace(" ", "T") + "Z"` logic is altered, the time will drift from the organization's actual event time to the viewer's local time.
- **Implicit UTC assumption.** The function assumes the input string is UTC. If the API is updated to provide offset-aware strings, the manual string manipulation (`replace` and `+ "Z"`) could result in double-offsetting or invalid ISO formats.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
