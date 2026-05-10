---
node_id: concorda-web::src/lib/datetime.ts::orgDateInputToUtcIso
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e94c866b1cac216a5fc1f636cae215933ba7e7515f08aab52c4decd3f6d5df09
status: current
---

# orgDateInputToUtcIso

## Purpose

Frontend datetime helper — inverse of `utcIsoToOrgDateInput`. Takes a `YYYY-MM-DD` value from `<input type="date">` and produces a UTC ISO marking `00:00` wall-clock in the org's timezone, used in form save paths for day-granularity records (Series start/end). Thin wrapper that appends `T00:00` and delegates to `orgInputToUtcIso`, so all the offset/DST math lives in one place. Exists so that "May 23 in Boston" round-trips through the wire as a UTC instant that re-renders as May 23 — not May 22 in EDT, which is what naively sending `${value}T00:00:00Z` would yield.

## Invariants

- **Returns `undefined` for empty/null input**, never throws. Callers treat `undefined` as "leave the field unchanged" or "cleared" depending on patch shape.
- **Delegates to `orgInputToUtcIso` with `T00:00` appended** — the two functions share parsing/DST behavior. Don't reimplement the offset math here.
- **Round-trips with `utcIsoToOrgDateInput`** at day precision: any sub-day component on the input ISO is collapsed to org-TZ midnight.
- **`tz` is the org TZ** (`useConstants().timezone`, default `"America/New_York"`). Never pass the browser's resolved zone.
- **Pure**, deterministic given `(value, tz)`.

## Gotchas

- **The bug this exists to prevent:** `${value}T00:00:00Z` looks fine and is wrong — it anchors to UTC midnight, which is the *previous* calendar day in EDT/EST. Series with a May-23 start would persist as May 22 and re-render shifted. The 2026-05-07 audit (see `feedback_timezone_helpers_mandatory.md`) caught this pattern in ~30 components; grep for `T00:00:00Z` and `new Date(value).toISOString()` on every form-save edit in this neighborhood.
- **DST inheritance from `orgInputToUtcIso`:** spring-forward and fall-back behavior is whatever the underlying helper does. Midnight is well outside the 1–2am DST windows, so date-only fields are unaffected in practice — but don't repurpose this for moments that could land near the gap.
- **Don't pair with `utcIsoToOrgInput` (datetime variant) for round-trips.** That counterpart preserves hours/minutes; this one zeroes them. Mixing them on the same field will silently collapse the time component.

## Cross-cutting concerns

- **Timezone convention** is enforced via `feedback_timezone_helpers_mandatory.md` (UI must use these helpers) and `feedback_naive_datetime_convention.md` (storage = UTC-aware via backend `UtcDateTime`). This is the save-side primitive for date-only inputs; `orgInputToUtcIso` covers datetime-local.
- **4 direct callers** as of 2026-05-10, all in the Series admin surfaces (`admin/events/series/[id]/page.tsx` and `admin/events/series/page.tsx`, each touching start and end). Signature is stable; additive changes only.
- **No logigraph rule yet** enforces "all `<input type='date'>` save paths must funnel through this helper." Worth a `rule::ui::date_input_save` paired with the read-side `rule::ui::date_input_binding`.

## External consumers

None outside `concorda-web` (frontend helper).

## Open questions

None.
