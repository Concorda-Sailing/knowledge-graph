---
node_id: concorda-web::src/components/profile/sections/calendar-subscription-section.tsx::CalendarSubscriptionSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8b5e5bb60fbd09b21a83d1b4c23e0cb9b520284899be6c81d477e6a57e665288
status: current
---

# CalendarSubscriptionSection

## Purpose

Provides the UI for managing the user's external calendar subscription (webcal/iCal). It allows users to view their current subscription URLs, generate/rotate new tokens, or disable the subscription entirely. This is distinct from the `SecuritySection` as it manages external data consumption (pushing events to the user's calendar) rather than internal account security.

## Invariants

- **Uses `calendarApi` for all state changes.** All calls to `.status()`, `.rotate()`, and `.disable()` must be routed through this specific API client.
- **Requires `CalendarTokenIssued` shape.** The `issued` state must contain both `webcal_url` and `subscription_url` to ensure the UI can render both the copyable link and the QR code.
- **`setHasToken(false)` on error.** If the initial status check or a rotation fails, the component must explicitly set the token state to false to prevent showing stale/broken links.

## Gotchas

- **`navigator.clipboard` availability.** The `copyUrl` function relies on the browser's Clipboard API; in environments where this is restricted or unavailable, the `catch` block triggers a "destructive" toast.
- **`confirm()` blocking.** The `disable` method uses a native `window.confirm` dialog. This is a blocking call that can interrupt the React render cycle if not handled carefully in more complex flows.

## Cross-cutting concerns

- **Auth**: Uses `calendarApi`, which requires an authenticated session (likely via the bearer token established in `ApiClient`).
- **Side effects**: Disabling the subscription via `calendarApi.disable()` will stop the push of event updates to the user's external calendar app.

## External consumers

None known.
