---
node_id: concorda-web::src/app/members/admin/events/import/page.tsx::DateField
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 70b1e6053855be8581572e3b364938efab552824749725e73f4ea4f24a7963ff
status: current
---

# DateField

## Purpose

A specialized input component for the event import workflow that handles the conversion between UTC ISO strings (API format) and local timezone-aware display strings (UI format). It uses `utcIsoToOrgInput` and `orgInputToUtcIso` to ensure that the user-facing `datetime-local` input reflects the organization's specific timezone rather than the browser's local time. Use this instead of a standard `Input` when the field represents a timestamp that must be synchronized with the organization's timezone.

## Invariants

- **Input/Output parity**: The `value` prop is a UTC ISO string; the `onChange` callback returns a UTC ISO string.
- **Timezone-aware conversion**: Uses `tz` to drive both the `datetime-local` display value and the `formatFriendly` output.
- **Display format**: The component renders a small timestamp preview below the input using `formatFriendly` to show the human-readable version of the current value.

## Gotchas

- **Strict timezone requirement**: Per commit `f444b4c`, this component must render backend datetimes in the organization's timezone, never the browser's local time. If the `tz` prop is ignored or a standard `Date` object is used without the `tz` context, the input will show the wrong time to the user.
- **Fallback behavior**: If `value` is empty or invalid, `formatFriendly` returns the raw string or an empty string to prevent "Invalid Date" from appearing in the UI.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: Y (used during the event import process which triggers audit logs)
- **Rate limit**: none
- **Side effects**: Updates the state of the event import form, which is a precursor to creating/updating event records in the database.

## External consumers

None known.
