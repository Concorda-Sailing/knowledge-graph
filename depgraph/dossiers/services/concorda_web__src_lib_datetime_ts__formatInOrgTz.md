---
node_id: concorda-web::src/lib/datetime.ts::formatInOrgTz
node_kind: service
feature: datetime-display
last_reviewed: 2026-05-09
last_reviewed_against_hash: 3234e09d0f904fa84725d3f27f9e0eb5d912a46c819c880989672c53bf15c724
status: current
---

# formatInOrgTz

## Purpose

The single canonical helper for rendering a UTC ISO timestamp in the organization's timezone. Wraps `Intl.DateTimeFormat` with `timeZone: tz` so every component shows the same instant rendered consistently for the org's local audience (e.g., Mass Bay Sailing's events should show in `America/New_York` regardless of where the viewer is).

70 components depend on it. It is the most-depended-on function in the web codebase.

## Invariants

- **Input is a UTC ISO string** (`"2026-05-08T14:30:00Z"` or `"...+00:00"`). Per memory `feedback_naive_datetime_convention`, the API stores datetimes as naive UTC and surfaces them as ISO with explicit offset; the input format here matches that contract.
- **Output is for display only.** The string is timezone-localized prose ("May 8, 2026, 10:30 AM"). Do not parse it back into a Date — it lost timezone information at format time.
- **Empty/invalid input returns `""`**, not `null` or a thrown error. Components rendering this in JSX rely on the empty-string fallback to produce no DOM.
- **`tz` MUST be the org timezone**, not the browser's. Pass `useConstants().timezone` or its equivalent — never default to `Intl.DateTimeFormat().resolvedOptions().timeZone` (the user's local TZ).
- **`options` is required.** It carries the format intent (`year: "numeric", month: "short", day: "numeric"` etc). There is no default — passing `{}` produces an unspecified format.

## Gotchas

- **Per memory `feedback_timezone_helpers_mandatory`**, every datetime render in concorda-web MUST go through these helpers. A naked `date.toLocaleString()` or `date.getHours()` is a bug — it silently uses the viewer's timezone, which on a sailor traveling to a regatta in another zone produces the wrong start time. An audit on 2026-05-07 found ~30 components drifting; on every edit, scan for `getHours/getMonth/toLocale*` without `timeZone:` set.
- **Pre-2026-05-06 imported events** may have been ingested with naive-not-UTC datetimes (4–5h off). Per memory `feedback_naive_datetime_convention`, fix those by hand if discovered; this helper assumes inputs are correctly UTC-tagged.
- **`Intl.DateTimeFormat` returns "Invalid Date" for non-Date inputs.** The function guards with `isNaN(d.getTime())` and returns `""` instead. If you remove this guard, malformed inputs will render literally as "Invalid Date" in the UI.
- **70 dependents.** Renaming this function (or changing its signature) is a sweep across most of the web app. The structural_hash on this node will flip and dossiers across the dependent set will mark as needs-review.

## Cross-cutting concerns

- **Sibling helpers** in the same file: `ymdInOrgTz` (date bucketing), `partsInTz` (parts extraction), `orgInputToUtcIso` / `utcIsoToOrgInput` (form-input round-trips). They share the convention.
- **API contract:** All API responses use UTC ISO strings; this is the rendering side of that contract.
- **Tests:** Playwright specs that assert on rendered datetime strings need to set the test browser's clock or mock the org TZ — but most specs avoid this by checking semantics (e.g., the row exists) rather than literal text.

## External consumers

- N/A — purely internal to the web app. Not used by Expo (which has its own timezone helpers it should standardize on a similar pattern).

## Open questions

- Should we provide a typed `formatInOrgTz<"date" | "time" | "datetime">(...)` wrapper that pre-fills the common option presets? Today every caller spells out the options.
