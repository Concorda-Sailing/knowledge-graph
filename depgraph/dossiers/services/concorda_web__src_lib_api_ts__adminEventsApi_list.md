---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 62c2ba589d371d4bba9138128f06bdc35771f3ce275f3c28579b9c7ae885ac7a
status: llm_drafted
---

# adminEventsApi.list

## Purpose

Provides an administrative interface for managing event-related data, including lifecycle operations (create, update, delete), image handling, and registration lookups. It is distinct from the public-facing `eventsApi` by providing higher-privilege actions like `duplicate`, `checkDuplicates`, and `getRegistrationCounts`. Use this when an admin-level action is required that involves modifying or auditing the event lifecycle.

## Invariants

- **Requires authentication.** All methods call `fetchApiAuthenticated`, meaning a valid bearer token is required.
- **Input parameters are optional for `list`.** The `params` object can be partially populated with `start_date`, `end_date`, or `category`.
- **Returns `Event` or `Event[]` types.** Most methods return the full event object or a list of events, maintaining consistency with the core `Event` type.
- **`checkDuplicates` returns a specific shape.** It returns an array of objects containing `match_id`, `match_name`, `match_date`, and `match_type`.

## Gotchas

- **`duplicate` is a POST request.** Unlike `get` or `list`, the `duplicate` method uses the `POST` method to create a copy of an existing event.
- **Image uploads use a specialized fetcher.** `uploadImage` uses `fetchApiUpload` rather than `fetchApiAuthenticated` to handle multipart/form-data for `File` objects.
- **Registration counts are global-ish.** `getRegistrationCounts` returns a `Record<string, number>` and does not take an ID, implying it returns aggregate counts across the system or current context.

## Cross-cutting concerns

- **Auth**: Requires authenticated user session via `fetchApiAuthenticated`.
- **Side effects**: Changes to these endpoints (specifically `create`, `update`, or `delete`) will affect the visibility of events in the public `eventsApi` and the `schedule-card` count.

## External consumers

- `SocialsPage` (via `admin/events/socials/page.tsx`)

## Open questions

- The `checkDuplicates` method returns a `match_id` and `match_name`, but it is unclear if the UI should automatically resolve these or if the user must manually confirm the match.
