---
node_id: concorda-web::src/lib/api.ts::eventsApi.getBySlug
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f2fe7e6e64bd8170b66dab561dcb81bf12e5d948dae575d6c6fa7df24d56ea38
status: llm_drafted
---

# eventsApi.getBySlug

## Purpose

Fetches the public-facing `Event` object using its URL slug. This is the primary method for populating the public event view when a user navigates to a specific event page via a link. It is distinct from `getDetail`, which is an authenticated call used for the schedule detail page that includes viewer-specific roles and permissions.

## Invariants

- **Method is GET** via `fetchApi`.
- **Input is a string `slug`** representing the unique identifier in the URL.
- **Returns an `Event` object** containing public metadata.
- **Does not require authentication**, making it suitable for unauthenticated public access.

## Gotchas

- **Decoupled from `getDetail`** — per commit `1b5d864`, this method (and the underlying API) was refactored to ensure the detail page calls `/api/events/{id}/detail` instead of relying on `mySchedule` or other coupled logic.
- **Slug vs ID** — ensure you are passing the string slug and not the UUID/ID; using the ID in this method will result in a 404 or empty response.

## Cross-cutting concerns

- **Auth**: None (publicly accessible).
- **Side effects**: Used by `PublicEventPage` to render the primary event content.

## External consumers

None known.
