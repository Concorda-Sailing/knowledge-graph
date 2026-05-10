---
node_id: concorda-web::src/components/boat/boat-header.tsx::BoatHeader
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ff91ae0e627ce6944751b54024db58ddb8d2e9d90f2677518126ec0112f05034
status: llm_drafted
---

# BoatHeader

## Purpose

The `BoatHeader` provides a standardized visual identity for a boat, combining a title, subtitle, and banner image. It wraps the `HeroBanner` component to ensure consistent layout for boat-specific branding. Use this when you need a high-level header that can optionally accept an `avatar` override (e.g., for an editable upload component) or a `bannerOverlay` (e.g., for owner-only controls).

## Invariants

- **Title fallback logic**: If `boat.name` is missing, the component defaults to displaying the `boat.sail_number` as the primary title.
- **Subtitle fallback logic**: If `boat.name` is present, the `sail_number` is used as the subtitle; otherwise, the subtitle is `undefined`.
- **Avatar fallback**: If no `avatar` prop is provided, it renders the internal `BoatAvatar` component, which displays the `picture_url` or an `Anchor` icon fallback.
- **Banner URL handling**: If `boat.banner_url` is null or undefined, the `bannerUrl` prop passed to `HeroBanner` is `undefined`.

## Gotchas

- **Avatar override requirement**: When building owner-facing views, you must explicitly pass an editable component to the `avatar` prop, otherwise the user will see the static `BoatAvatar` which only displays the `picture_url` or the `Anchor` icon.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

None known.
