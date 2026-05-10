---
node_id: concorda-web::src/lib/api.ts::boatApi.createPunchlistItem
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a27fdd411bf24917542aa364de36b5764061973459328662f544fb7fd21081f4
status: llm_drafted
---

# boatApi.createPunchlistItem

## Purpose

The `createPunchlistItem` method allows users to add a new maintenance or task item to a specific boat's punchlist. It is part of the `boatApi` service and is used to transition from viewing a boat's status to actively managing its maintenance needs. Use this method when a user submits a new punchlist entry via the UI.

## Invariants

- **HTTP Method is `POST`** — used to create a new resource.
- **Endpoint path is `/api/boats/${boatId}/punchlist`** — the base path for the collection.
- **Requires a `boatId`** — the specific boat instance being modified.
- **Input `data` object** — must include `title` (string) and can optionally include `description`, `importance`, or `assigned_to_uuid`.
- **Returns a `PunchlistItem`** — the successfully created object, including its new server-generated ID.

## Gotchas

- **Authentication requirement** — relies on `fetchApiAuthenticated`, meaning a valid bearer token must be present in the session.
- **Data shape dependency** — the `data` object is a flat structure; ensure `assigned_to_uuid` is a valid user UUID to avoid downstream failures in assignment-related UI components.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Updates the state of the `BoatPunchlist` component (see `boat-punchlist.tsx:65`).

## External consumers

- `concorda-web::src/components/boat/boat-punchlist.tsx` (via `BoatPunchlist` component).
