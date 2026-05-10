---
node_id: concorda-web::src/app/members/socials/page.tsx::SocialCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7ee0e5a800ee4f800440f24af2029f52877220922c3229ca04aac1d2d5fba9fe
status: llm_drafted
---

# SocialCard

## Purpose

The `SocialCard` component renders a visual summary of an event within the Socials page layout. It displays the event's date, time, location, and price, while providing a registration link and a progress indicator if linked to a `ScheduleItem`. It is used to provide a high-level overview of upcoming social events, distinct from the more granular detail views found in the main schedule.

## Invariants

- **Requires `tz` for date rendering.** The `event.date` must be passed through `formatDate(event.date, tz)` to ensure the display matches the organization's timezone rather than the user's local time.
- **`isPast` controls visual state.** When `isPast` is true, the card receives an `opacity-50` class to visually de-emphasize completed events.
- **`event.slug` drives registration.** The "Register" button only renders if `event.slug` is present, and it uses an `<a>` tag with `e.stopPropagation()` to prevent event bubbling.
- **`scheduleItem` is optional.** If provided, it triggers the rendering of the `<PlanProgress />` component at the bottom of the card.

## Gotchas

- **Timezone alignment is critical.** Per commit `f444b4c`, all backend datetimes must be rendered using the provided `tz` (the organization's timezone) to avoid displaying incorrect local times to users.
- **Price formatting.** The component uses `Number(event.price).toFixed(0)` for the display; ensure that `event.price` is a valid number to avoid `NaN` appearing in the badge.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Displays event status (Past/Members Only/On Schedule) which is a visual indicator of the event's current lifecycle state.

## External consumers

None known.
