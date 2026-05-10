---
node_id: concorda-web::src/app/members/admin/events/import-social/page.tsx::ImportSocialsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e4989b678ceb9f4043ccbfac3fb93ff9e960ddbd5ccb928a7e1deda5754f25f4
status: llm_drafted
---

# ImportSocialsPage

## Purpose

The administrative interface for uploading and parsing external social event data (e.g., spreadsheets or documents) into the Concorda system. It manages a two-phase workflow: uploading a file to the `norApi.uploadAndExtract` endpoint and then reviewing/editing the extracted form data before final submission. This page is the primary entry point for converting unstructured external data into structured event objects.

## Invariants

- **Requires `events.edit` permission** via the `PermissionGate` wrapper.
- **Uses `norApi.uploadAndExtract(file, "social")`** to perform the extraction; the second argument must be exactly `"social"` to trigger the correct extraction logic.
- **Generates unique IDs for items** using a combination of `Date.now()` and a random string to prevent collisions during the review phase.
- **Transforms raw API data via `evtToForm`** to ensure string-based form compatibility, specifically stripping time-specific suffixes (e.g., `" 00:00:00"`) from date and time strings.

## Gotchas

- **The `evtToForm` function performs destructive string manipulation.** It uses `.replace(" 00:00:00", "")` and regex-based time stripping (e.g., `^(\d{2}:\d{2}):\d{2}$`). If the API format for dates or times changes, these regexes may fail to strip the suffix, leading to validation errors in the form-filling stage.
- **Multi-item extraction vs. Single-item extraction.** The logic branches based on `result.extracted_items`. If the API returns a single object instead of an array, the code handles it by wrapping the single object in an array to maintain the `ImportedItem` shape.
- **The `result.status` check is critical.** If the status is not `"extracted"`, the component treats the result as a failed/empty extraction and populates the form with an empty object (`form: {}`), which may lead to unexpected UI behavior if the user attempts to "save" a failed extraction.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `PermissionGate`.
- **Side effects**: Successful imports via this page populate the social events calendar and the schedule detail view.

## External consumers

None known.

## Open questions

- The `evtToForm` function relies on hardcoded string replacements for time/date formatting (e.g., `replace(" 00:00:00", "")`). Should this be moved to a centralized utility to ensure consistency with the `formatInOrgTz` pattern used elsewhere in the web app?
