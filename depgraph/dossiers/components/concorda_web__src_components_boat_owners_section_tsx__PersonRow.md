---
node_id: concorda-web::src/components/boat/owners-section.tsx::PersonRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4ac8767633c646b4cda9d5b236fbda111a06f2b798a8bcff2aa0d68255d9a9e6
status: current
---

# PersonRow

## Purpose

Renders a single row in the boat owners list, displaying a person's avatar, name, and email. It is a stateless presentation component used to list potential co-owners or display currently assigned owners. Use this instead of `SelectedPerson` when building a list of selectable directory members.

## Invariants

- **Input is `DirectoryPerson`** — expects a person object with `first_name`, `last_name`, and `picture_url`.
- **Avatar fallback is initials-based** — if `picture_url` is missing, it generates a two-letter uppercase string from the first and last name.
- **Clickable interaction** — the component is a `<button>` that triggers the `onSelect` callback.

## Gotchas

- **Layout constraints** — per commit `3402684`, ensure the parent container handles full-width stack actions correctly on `<md` screens to prevent layout breakage in mobile views.
- **Empty name handling** — the initials calculation uses optional chaining (`person.first_name?.[0]`) to prevent runtime errors if name fields are null, but a missing name will result in an empty string for the `AvatarFallback`.

## Cross-cutting concerns

- **Auth**: Implicitly tied to the directory-only invite flow; visibility of these rows is governed by the user's ability to view the directory.
- **Side effects**: Used in the "owners settings section" to manage the list of people with access to a boat.

## External consumers

None known.
