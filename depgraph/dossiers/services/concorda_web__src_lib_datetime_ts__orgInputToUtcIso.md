---
node_id: concorda-web::src/lib/datetime.ts::orgInputToUtcIso
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a2129e46c16419b802c9c764b3350c195a394e343105e639e39f491d170f72c8
status: current
---

# orgInputToUtcIso

## Purpose

Take a wall-clock string from `<input type="datetime-local">` (e.g. `"2026-05-23T18:55"`) and produce a UTC ISO string for the wire, **interpreting the wall-clock as being in the org's timezone, not the browser's**. This is the save-side counterpart to `ymdInOrgTz` (which is read-side bucketing): together they enforce the convention that humans type and read times in org TZ regardless of where the editor's laptop happens to be. Critical for race and event scheduling — if the form save inferred timezone from the browser, a regatta organizer travelling to California would silently shift every Boston race by three hours when they edited it.

## Invariants

- **Returns `undefined` for empty/null/unparseable input**, never throws. The regex enforces strict `YYYY-MM-DDTHH:MM[:SS]` shape; anything else is rejected as `undefined` (callers treat that as "leave unchanged" or "field cleared," depending on context).
- **Pure function** — no globals, deterministic given `(value, tz)`. No reads of `Date.now()` or browser TZ.
- **Output always has a UTC offset** (`...Z`) because it goes through `Date#toISOString()`. Backends parse it via Pydantic `UtcDateTime`; do not strip the offset before sending.
- **`tz` is the org timezone**, sourced from `useConstants().timezone` (default `"America/New_York"`). Never pass `Intl.DateTimeFormat().resolvedOptions().timeZone`; that is exactly the bug this helper exists to prevent.
- **Round-trips with `utcIsoToOrgInput`**: `orgInputToUtcIso(utcIsoToOrgInput(iso, tz), tz)` equals `iso` (modulo seconds, which the input drops).

## Gotchas

- **DST corner cases.** At spring-forward, the wall-clock 2:00–2:59 AM doesn't exist in the org TZ; the helper resolves it to the offset *after* the gap (effectively shifts forward). At fall-back, the duplicated 1:00–1:59 AM resolves to the first occurrence (pre-change offset). Concorda doesn't schedule races in those windows, but if a future feature does, this helper's behavior is implementation-defined, not configurable.
- **The "fake UTC" trick is subtle.** The function builds a `Date` as if the wall-clock were UTC, asks `Intl` what that instant looks like in the org TZ, and uses the delta as the offset. This is correct because `Intl` is the only reliable cross-browser source of historical/DST-aware offsets, but it means a misconfigured `tz` (typo, IANA zone removed) will silently produce garbage rather than throw.
- **Seconds are accepted but not emitted by the input.** `<input type="datetime-local">` typically returns minute precision; the regex tolerates `:SS` because some browsers (and our `orgDateInputToUtcIso`) synthesize it. Don't tighten the regex.
- **The audit on 2026-05-07** found ~30 components doing form-save with raw `new Date(value).toISOString()` — that path is the bug this helper fixes. On every form-save edit, scan for `new Date(...).toISOString()` and migrate to this helper.

## Cross-cutting concerns

- **Timezone convention** is enforced via `feedback_naive_datetime_convention.md` (storage = UTC-aware via `UtcDateTime`) and `feedback_timezone_helpers_mandatory.md` (UI must use these helpers). This function is the canonical save path.
- **Companion `orgDateInputToUtcIso`** delegates here with `T00:00` appended — so date-only fields (Series start/end) anchor to org-TZ midnight, which is what backend day-bucketing logic expects. Bypassing it (e.g. sending `${value}T00:00:00Z`) yields a UTC midnight that lands on the previous calendar day in EDT.
- **No logigraph rule yet** captures "all `<input type=datetime-local>` save paths must funnel through `orgInputToUtcIso`." Worth a `rule::ui::form_save_timezone` enforces target.
- **Read-side counterpart**: `ymdInOrgTz` and `formatInOrgTz` for display; `utcIsoToOrgInput` to seed the input from a saved value. Edits to the signature here should be mirrored on `utcIsoToOrgInput` to preserve the round-trip.

## External consumers

Form-save call sites in `concorda-web` (13 references as of 2026-05-10):

- `src/app/members/admin/events/[id]/page.tsx::EventDetailContent` — admin event editor; both event window and per-race start/end.
- `src/app/members/admin/events/races/[id]/page.tsx::RaceEditorContent` — race editor start/end.
- `src/app/members/admin/events/import/page.tsx::DateField` — bulk event import field.
- `src/app/members/events/new/page.tsx::NewSailingEventPage` — owner-flow new-event creation.
- `src/app/members/schedule/[id]/page.tsx::ScheduleEventDetail` — schedule detail edit.
- `src/components/dashboard/event-plan-panel.tsx::EventPlanPanel` — dashboard quick-edit.

No backend or external integration consumers; this is a frontend save helper.

## Open questions

- Should DST-gap input (e.g. a typo'd `02:30` on spring-forward day) raise a visible warning rather than silently snap forward? Currently silent. Probably YAGNI until a sailor reports a mis-scheduled race.
- If Concorda ever multi-tenants with different org TZs, the signature is fine (already takes `tz`); the form components need to thread the right org's `tz` per record being edited, not assume `useConstants().timezone`.
