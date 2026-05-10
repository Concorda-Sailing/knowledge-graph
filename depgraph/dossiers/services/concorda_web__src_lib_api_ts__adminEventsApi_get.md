---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d0cdbcd12039bae65d8ec24e4070abddf3882950a26f5361474c6b59073a6483
status: current
---

# adminEventsApi.get

## Purpose

Provides the primary interface for administrative event management. It handles the full lifecycle of an event, including retrieval, creation, updates, and deletions. Use this method when you need to fetch a single event's full data by its unique ID, or when performing administrative actions like uploading images or checking for duplicate event entries.

## Invariants

- **Requires authentication** — uses `fetchApiAuthenticated` to ensure the request includes the bearer token.
- **Returns a single `Event` object** — the `get` method returns the full event object for the provided ID.
- **Method-specific payloads** — `create` and `update` require structured `EventCreate` or `EventUpdate` objects respectively.
- **Image handling** — `uploadImage` uses `fetchApiUpload` to handle multipart/form-data for file transfers.

## Gotchas

- **Coupling with detail views** — per commit `1b5d864`, the detail page was previously calling a specific `/detail` endpoint; it now relies on this `get` method to avoid coupling issues with `mySchedule` data.
- **Duplicate detection** — `checkDuplicates` is a specialized POST-based utility used to identify potential name/date collisions before creation.
- **Registration data access** — `getRegistrations` and `getRegistrationCounts` are separate calls from the main `get` method; if the UI needs to show how many people are signed up, it must call these explicitly.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid session/token).
- **Side effects**: Updates to this endpoint (via `update` or `delete`) will affect the data displayed on the `EventDetailContent` component in the admin dashboard.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (EventDetailContent)
