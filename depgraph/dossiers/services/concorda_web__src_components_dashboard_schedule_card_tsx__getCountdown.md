---
node_id: concorda-web::src/components/dashboard/schedule-card.tsx::getCountdown
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5210dbf20416a49f5201d0ee2ae6d25a387aacfb09893b883a024758d397d0ab
status: current
---

# getCountdown

## Purpose

Calculates a human-readable countdown string and an urgency level for a scheduled event. It compares the event's date against the current time using the organization's specific timezone to ensure "Today" and "Tomorrow" labels align with the calendar days seen by the user, rather than a raw 24-hour hour difference.

## Invariants

- **Input is a UTC ISO string** (`dateStr`) and a timezone string (`tz`).
- **Returns an object** containing a `text` string and an `urgency` level (`"normal" | "soon" | "imminent"`).
- **Uses `ymdInOrgTz` for date comparison** to ensure the countdown logic respects the organization's calendar day boundaries.
- **"Done" state is triggered** when the event's timestamp is strictly less than the current time.

## Gotchas

- **Off-by-one errors on calendar days:** Per commit `cff2420`, the function must compare calendar days (via `ymdInOrgTz`) rather than raw hour differences. If an event is <24h away but falls on a different calendar day in the org TZ, it must not be labeled "Today" prematurely.
- **Timezone-sensitive rendering:** As noted in `f444b4c`, all date logic must use the provided `tz` to avoid the "browser-local" trap where a user's local time makes an event appear to be "Today" when it is actually "Tomorrow" in the regatta's location.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `ScheduleCard` to drive the visual urgency styling (colors/icons) in the dashboard view.

## External consumers

None known.
