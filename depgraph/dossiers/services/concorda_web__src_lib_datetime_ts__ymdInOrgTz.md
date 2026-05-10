---
node_id: concorda-web::src/lib/datetime.ts::ymdInOrgTz
node_kind: service
feature: timezone-helpers
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3dd51d1a9e8360c041c22eedcd066068ab1b69400b9d909b936cd4e717d69e71
status: current
---

# ymdInOrgTz

## Purpose

Extract `{ year, month, day }` numeric parts from a UTC ISO string,
*as observed in the organization's timezone* (not the browser's).
Used everywhere the UI needs to bucket events by calendar day —
schedule month grouping, calendar grid placement, "Today / Tomorrow /
Yesterday" labels, expiry-window badges.

This is the canonical bucketing primitive. Every component that
needs "what calendar day is this event in for our users?" must use
this; never use `new Date(iso).getMonth()` or any raw `Date` method,
because those rebase off the browser's timezone.

## Invariants

- **`month` is 0-based** (matches `Date.getMonth()` convention).
  Callers that compose dates back via `new Date(year, month, day)`
  need this; callers that display months as strings need to add 1
  or use `formatInOrgTz`. **Don't change this** — there are 35+
  callers and the off-by-one risk is significant.
- **Returns `null` on empty/invalid input**, never throws. Callers
  should null-check, not try-catch.
- **Pure function** — no side effects, no global state, deterministic
  given (iso, tz).
- **`tz` is the org timezone**, not the user's. Source of truth is
  `useConstants().timezone`, default `"America/New_York"`. Don't pass
  `Intl.DateTimeFormat().resolvedOptions().timeZone` (browser TZ);
  that defeats the convention.

## Gotchas

- **`new Date(iso)` parses correctly only for ISO 8601 strings with
  offset (`...+00:00` or `...Z`).** Naive ISO strings without offset
  parse as browser-local. The whole TZ system breaks if the wire
  format drifts. Pydantic's `UtcDateTime` ensures the backend always
  emits aware ISO; verify in tests if you suspect drift.
- **DST transitions are handled correctly** for normal cases; race
  scheduling at exactly the spring-forward hour (2:00–2:59 AM
  America/New_York) is undefined behavior. Concorda doesn't schedule
  races there in practice.
- **The audit on 2026-05-07** found ~30 components drifting away from
  this helper (using raw `Date.getMonth()` or `toLocaleString` without
  `timeZone`). See `feedback_timezone_helpers_mandatory.md` — on every
  edit, scan the file for `getHours`/`getMonth`/`toLocale*` without
  `timeZone` and migrate to this helper.

## Cross-cutting concerns

- **Timezone convention** is enforced via two memory entries:
  `feedback_naive_datetime_convention.md` (storage side) and
  `feedback_timezone_helpers_mandatory.md` (display side). This
  function is on the display side.
- **35+ callers** as of 2026-05-10 (per depgraph). Editing the
  signature would propagate widely; use additive changes.
- **No logigraph rule yet** captures "all calendar bucketing must go
  through ymdInOrgTz." Worth adding as a `rule::ui::calendar_bucketing`
  with this as the canonical enforces target.

## Companion functions in this module

- `formatInOrgTz(iso, tz, options)` — render display strings; use this
  for any user-visible date/time text.
- `orgInputToUtcIso(value, tz)` — convert `<input type="datetime-local">`
  wall-clock back to UTC ISO for save.
- `utcIsoToOrgInput(iso, tz)` — converse: render a saved UTC ISO into
  the wall-clock string the input expects.
- `orgDateInputToUtcIso` / `utcIsoToOrgDateInput` — date-only
  variants for `<input type="date">`.
- `partsInTz` — internal helper. Don't use directly.

## External consumers

- None outside `concorda-web` (this is a frontend helper).

## Open questions

- Should there be a *server-side* equivalent for places where the API
  needs to bucket by calendar day in org TZ (currently the API tends
  to return UTC and let the frontend bucket)? Not needed yet.
- The org TZ is currently a single global value via `OrgConfig`. If
  Concorda ever supports multiple orgs with different TZs, the helper
  signature is fine (already takes `tz`); the consumers need to
  thread the right `tz` per record.
