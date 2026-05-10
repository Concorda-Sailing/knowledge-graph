---
node_id: concorda-web::src/lib/datetime.ts::utcIsoToOrgDateInput
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2d8cd590f068b004eb443a381a1f412e201548909f7f8288e1387e1a0bba8d6a
status: current
---

# utcIsoToOrgDateInput

## Purpose

Convert a UTC ISO string (e.g. `"2026-05-23T03:30:00+00:00"`) into the `YYYY-MM-DD` string that `<input type="date">` expects, with the date computed in the *organization's* timezone rather than the browser's. Critical for forms where a moment near midnight UTC is actually the previous or next calendar day for the user — without this helper, an event scheduled at 11pm EDT (03:00 UTC the next day) would render in the date picker as tomorrow. Fans to 9 form/date-picker call sites: series start/end edit dialogs, policy effective-date display, schedule event edit, and the dashboard event plan panel.

## Invariants

- **Returns `""` on empty/invalid input**, never throws. Date-input controls treat empty string as cleared, so this is the right shape for direct binding to `value=`.
- **Output is always `YYYY-MM-DD` zero-padded** (en-US `2-digit` parts via `Intl.DateTimeFormat`). Callers can compare these as strings safely.
- **`tz` is the org TZ**, sourced from `useConstants().timezone` (default `"America/New_York"`). Never pass the browser's resolved timezone — that defeats the whole convention.
- **Pure function**, deterministic given `(iso, tz)`. No globals, no I/O.

## Gotchas

- **The bug this exists to prevent:** `new Date(iso).toISOString().slice(0,10)` looks innocent and is wrong — it slices the UTC date, not the org-TZ date. The audit on 2026-05-07 (see `feedback_timezone_helpers_mandatory.md`) found ~30 components drifting that way; on every edit in this neighborhood, grep for `toISOString().slice`, `getDate()`, `getFullYear()`, `getMonth()` without `timeZone` and migrate.
- **Wire format must carry an offset** (`...+00:00` or `...Z`). A naive ISO without offset is parsed as browser-local by `new Date(iso)`, silently shifting the day. Backend's `UtcDateTime` guarantees aware output; pre-2026-05-06 imports may be off (see `feedback_naive_datetime_convention.md`).
- **Round-trip with `orgDateInputToUtcIso`:** that companion sets wall-clock `00:00` in org TZ. Round-tripping a UTC ISO that had any time component through `utcIsoToOrgDateInput` → `orgDateInputToUtcIso` will collapse the time to midnight. Date-only fields (Series start/end) are fine; don't use this pair for datetime fields.

## Cross-cutting concerns

- **Timezone convention** is enforced via `feedback_naive_datetime_convention.md` (storage) and `feedback_timezone_helpers_mandatory.md` (display). This helper is the display-side primitive for date-only inputs.
- **9 direct callers** as of 2026-05-10. Signature is stable; additive changes only.
- **No logigraph rule yet** enforces "all `<input type='date'>` value bindings for org-TZ dates must use this helper." Worth adding alongside the `ymdInOrgTz` rule as a paired `rule::ui::date_input_binding`.

## External consumers

None outside `concorda-web` (frontend helper).

## Open questions

None.
