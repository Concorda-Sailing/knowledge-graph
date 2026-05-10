---
node_id: concorda-web::src/app/members/admin/events/import-social/page.tsx::evtToForm
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2bbdf22466f69047b2669c845584e34354c0d32336bdfeedc9262595987057c1
status: current
---

# evtToForm

## Purpose

The `evtToForm` helper normalizes raw, unstructured data extracted from social media or spreadsheet-based imports into a standardized `Record<string, string>` format. It acts as a translation layer between the `norApi.uploadAndExtract` output and the application's internal event forms. Use this when you need to ensure that extracted fields (like `date`, `time`, or `price`) are cast to strings and stripped of problematic formatting before being passed to a form state or a submission handler.

## Invariants

- **Returns a flat `Record<string, string>`** — all values are cast to strings to prevent type mismatches in the UI components.
- **Normalizes temporal strings** — strips `" 00:00:00"` from `date` and `end_date`, and truncates `time` and `end_time` to `HH:mm` format using regex.
- **Handles null/undefined gracefully** — uses empty strings as fallbacks for all keys to ensure the resulting object is safe for form consumption.
- **Input is a record of unknown types** — the function accepts `Record<string, unknown>` to accommodate the varying shapes of `extracted_data` or `extracted_items`.

## Gotchas

- **Regex truncation for time** — the function uses `.replace(/^(\d{2}:\d{2}):\d{2}$/, "$1")` for `time` and `end_time`. If the input time format deviates from `HH:mm:ss`, the regex will fail to match and the suffix will remain, potentially causing validation errors in the downstream form.
- **Price casting** — `price` is only cast to a string if the value is truthy; otherwise, it returns an empty string.

## Cross-cutting concerns

- **Auth**: Wrapped in a `PermissionGate` with `permission="events.edit"` at the component level (see `ImportSocialsPage`).
- **Side effects**: This function is a critical step in the "spreadsheet multi-import" flow introduced in commit `e56387c`.

## External consumers

None known.
