---
node_id: concorda-web::src/components/boat/boat-profile-card.tsx::Row
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 87229203da9872c2388012bc665fe4712d6ef3e99dd1fd405139230b206221b2
status: current
---

# Row

## Purpose

A simple layout helper used to display a key-value pair in a horizontal, justified layout. It is used within the `BoatProfileCard` to present metadata (like boat name or registration) where the label is muted and the value is prominent.

## Invariants

- **Layout is justified**: Uses `justify-between` to push the label to the left and the value to the right.
- **Label is muted**: The label is wrapped in a `span` with the `text-muted-foreground` class to provide visual hierarchy.
- **Input types**: The `label` prop accepts `React.ReactNode` to allow for icons or complex text, while `value` is strictly a `string`.

## Gotchas

- **Implicit styling dependency**: Because it relies on `text-muted-foreground`, this component will look broken or invisible if used in a context where the global CSS variables for muted foregrounds are not defined or are overridden.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
