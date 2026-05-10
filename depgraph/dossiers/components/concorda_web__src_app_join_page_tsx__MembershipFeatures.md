---
node_id: concorda-web::src/app/join/page.tsx::MembershipFeatures
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ddee91b0c7ef3eb49ddf1f70c444bb960d6f6cf4deec0d943aafdabdbaf4aa2e
status: llm_drafted
---

# MembershipFeatures

## Purpose

Renders a checklist of features included in a specific membership tier. It maps boolean grant flags from a `TemporalProductPublic` object to a list of human-readable labels with visual indicators (checkmarks and strike-throughs). This is a pure presentational component used within the `JoinPage` to display the value proposition of different membership levels.

## Invariants

- **Input is `TemporalProductPublic`** — The component expects a product object containing specific boolean grant flags (e.g., `grants_crewfinder`, `grants_event_discount`).
- **Hardcoded feature set** — The list of features (Crew Finder, Event Discounts, etc.) is defined locally within the component and is not passed in as props.
- **Visual state is binary** — If a feature is not included, the label receives a `line-through` class and the icon uses a muted color.

## Gotchas

- **Feature list is static** — Adding a new grant type to the backend/API requires a manual update to the `features` array in this component to make it visible to users.
- **Recent UI redesign** — Per commit `f43a5f4`, this component was part of a redesign to treat membership cards as pricing cards; ensure any new feature grants added to the API are also reflected here to avoid "missing" features in the UI.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

None known.
