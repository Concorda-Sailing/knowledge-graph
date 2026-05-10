---
node_id: POST::/api/events/{0}/duplicate
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4a0668a00d5ec383d2af3e63ee1c918014b07a1f1c1a3763fc22ede63feea432
status: current
---

# POST /api/events/{event_id}/duplicate

## Purpose

Creates a duplicate of an existing event and its associated active ticket products. This is used to clone event templates or recurring structures while preserving the core configuration (date, location, organizer) and active product availability. It is distinct from a simple copy-paste of a single record; it performs a deep copy of the `Event` and its related `Product` and `EventOA` (Organizer/Attendee) data.

## Invariants

- **Requires `events.create` permission** via the `require_permission` guard.
- **Returns `EventReadWithRegatta`** which includes the full event structure and any associated regatta data.
- **Generates a unique slug** using `ensure_unique_slug` to prevent collisions with the original event.
- **Clones only active products**; `Product.is_active` must be `True` for a product to be carried over to the new event.
- **Preserves core attributes** including `date`, `location`, `price`, and `organizing_club_id`.

## Gotchas

- **Slug collision risk:** The function uses `generate_slug(f"Copy of {source.name}")`. While `ensure_unique_slug` handles the database-level collision, the resulting name might be undesirable for users if they duplicate many items.
- **Regatta dependency:** If the source event is a `regatta` category, the logic for handling the linked `Regatta` record is handled upstream in the deletion logic (see `db_event.category == "regatta"` in the source), but this endpoint specifically focuses on the creation side.

## Cross-cutting concerns

- **Auth**: Requires `events.create` permission.
- **Side effects**: Triggers a new event record which may appear in the `schedule` and `calendar` views.
- **Audit**: N/A.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.duplicate`

## Open questions

- Should the duplication process include a prompt to the user to decide if they want to include/exclude certain product types (e.g., only active products vs. all products)? Currently, it is hardcoded to only clone `is_active == True`.
