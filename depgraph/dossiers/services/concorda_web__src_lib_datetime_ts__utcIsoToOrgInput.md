---
node_id: concorda-web::src/lib/datetime.ts::utcIsoToOrgInput
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 59caad98502ea0ca69d7948a66a98d563d12b089c3e23a6e4f74e5e9a913826d
status: current
---

# utcIsoToOrgInput

## Purpose

Convert a UTC ISO string (e.g. `"2026-05-23T13:55:00+00:00"`) into the `YYYY-MM-DDTHH:MM` string that `<input type="datetime-local">` expects, with the wall-clock computed in the *organization's* timezone rather than the browser's. Sibling of `utcIsoToOrgDateInput` but for full datetime inputs — where date pickers care about the day, this one carries hours and minutes too. Without it, an admin in PDT editing an EDT regatta would see times shifted three hours; with it, the editor's browser TZ is irrelevant. Fans to 9 form call sites: the admin event detail editor (start/end and three other moment fields), the race editor (start/finish), and the events import DateField.

## Invariants

- **Returns `""` on empty/invalid input**, never throws. Datetime-input controls treat empty string as cleared, so this is the right shape for direct binding to `value=`.
- **Output is always `YYYY-MM-DDTHH:MM`** — minute precision, no seconds. `<input type="datetime-local">` accepts seconds optionally but most browsers hide them; matching what the input renders avoids spurious "dirty" form state.
- **Hour is `h23`** (00–23) via `partsInTz`'s `hourCycle: "h23"`. Critical: the en-US default is `h12` with AM/PM, which the input would reject.
- **`tz` is the org TZ**, sourced from `useConstants().timezone` (default `"America/New_York"`). Never pass the browser's resolved timezone — that defeats the convention.
- **Round-trips losslessly with `orgInputToUtcIso`** at minute precision (sub-minute components are dropped, which is intended for form editing).
- **Pure function**, deterministic given `(iso, tz)`. No globals, no I/O.

## Gotchas

- **The bug this exists to prevent:** binding `iso.slice(0,16)` directly to a `datetime-local` input ships the UTC wall-clock, so a 13:55 UTC race displays as "13:55" in the editor regardless of org TZ — and saving that round-trips wrong. The 2026-05-07 audit (see `feedback_timezone_helpers_mandatory.md`) found ~30 components drifting; on every edit in this neighborhood, grep for `toISOString().slice`, `getHours()`, `getMinutes()` without `timeZone` and migrate.
- **Wire format must carry an offset** (`...+00:00` or `...Z`). A naive ISO without offset is parsed as browser-local by `new Date(iso)`, silently shifting hours. Backend's `UtcDateTime` guarantees aware output; pre-2026-05-06 imports may be 4–5h off (see `feedback_naive_datetime_convention.md`).
- **DST asymmetry with the inverse:** `orgInputToUtcIso` documents that "spring forward" maps the missing hour forward and "fall back" maps the duplicated hour to the first occurrence. `utcIsoToOrgInput` is one-to-one in both directions *except* on the fall-back hour where two distinct UTC moments produce the same display string — round-tripping the second occurrence collapses it to the first. Race scheduling doesn't sit in the 1–2am window so this is fine in practice.

## Cross-cutting concerns

- **Timezone convention** is enforced via `feedback_naive_datetime_convention.md` (storage) and `feedback_timezone_helpers_mandatory.md` (display). This helper is the display-side primitive for full-precision datetime inputs; `utcIsoToOrgDateInput` covers date-only.
- **9 direct callers** as of 2026-05-10. Signature is stable; additive changes only.
- **No logigraph rule yet** enforces "all `<input type='datetime-local'>` value bindings for org-TZ moments must use this helper." Worth adding as `rule::ui::datetime_input_binding` paired with the date-input rule.

## External consumers

None outside `concorda-web` (frontend helper).

## Open questions

None.
