---
node_id: concorda-web::src/components/boat/boat-resume-view.tsx::Field
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8c952ebe4d37870e3e89a1fcc117a7dc329c1418fdb760636c8b6b6df3c47056
status: llm_drafted
---

# Field

## Purpose

A low-level layout component used to render labeled data points within the `BoatResumeView`. It standardizes the vertical stacking of a small-text label (muted foreground) and the actual data content (medium font weight). It is a structural helper used to ensure consistent spacing and typography for the boat's profile details.

## Invariants

- **Label is a string.** The `label` prop is required and is rendered as a small, muted-foreground text element.
- **Children are a ReactNode.** The component is agnostic to the content type, allowing for strings, `<p>` tags, or `<Chips />` components.
- **Layout is vertical.** The component returns a `div` containing a `span` and a `div`, creating a vertical stack of label over value.

## Gotchas

- **Implicit "Not set" handling.** While `Field` itself is a pure layout component, its primary consumer in this file (`BoatResumeView`) relies on the `Empty` component to render `"Not set"` when data is missing. If a developer replaces `Empty` with a null check that returns `null`, the label will still render, but the value area will be empty.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: Used by `BoatResumeView` to display boat-specific metadata (ethos, drinking policy, etc.) which is part of the boat profile view.

## External consumers

None known.
