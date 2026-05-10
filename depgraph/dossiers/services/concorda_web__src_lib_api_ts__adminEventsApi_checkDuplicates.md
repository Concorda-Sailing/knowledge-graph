---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.checkDuplicates
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 95a55282e85b9104c36b3aab541ae46d875ab4504e824d77f3f4006637879aac
status: current
---

# adminEventsApi.checkDuplicates

## Purpose

Provides a server-side validation check to identify potential duplicate events before they are committed to the database. It accepts an array of name/date pairs and returns a list of matches found in the existing event registry, including metadata like `match_id` and `match_type`. This is used primarily during bulk imports or manual creation flows to prevent accidental duplicate entries.

## Invariants

- **Method is `POST`** — The endpoint requires a POST request to send the `items` payload.
- **Input structure** — Accepts an array of objects containing at least a `name` (string) and an optional `date` (string).
- **Return shape** — Returns an array of objects containing `name`, `date`, `match_id`, `match_name`, `match_date`, and `match_type`.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to execute the check.

## Gotchas

- **Strictly for pre-commit validation** — This is a "check-only" utility; it does not mutate state. It is used by the `ImportContent` component in `src/app/members/admin/events/import-social/page.tsx` to warn users of collisions before the actual import occurs.
- **Date sensitivity** — Because the input `date` is optional, the backend matching logic may vary in precision (e.g., matching on name only vs. name and date).

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Used by the `ImportContent` component in the social media import flow to provide real-time collision feedback.

## External consumers

- `concorda-web::src/app/members/admin/events/import-social/page.tsx` (ImportContent component)
