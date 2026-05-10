---
node_id: concorda-web::src/components/ui/hero-banner.tsx::HeroBanner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 458f91a6a7c59697f7065480a04e4225c056aab138a5698e7778435f8d7f8aa0
status: llm_drafted
---

# HeroBanner

## Purpose

A presentational component used to display a high-impact header section, typically at the top of a page or view. It combines a background image (or gradient), a title, a subtitle, and an avatar. Use this when a page needs a visual "hero" identity, such as a specific race or event header, rather than a standard page title.

## Invariants

- **`avatar` is required.** It must be a `ReactNode` (typically an `<AvatarUpload />` or an `<img>`) to ensure the circular profile element is always present.
- **`title` is required.** The component expects a string for the primary heading.
- **`bannerUrl` is optional.** If not provided, the component defaults to a `bg-gradient-to-r` from `primary/10` to `muted` to ensure the section is not empty.
- **`bannerOverlay` is a slot for interaction.** It is rendered inside the relative container to allow for badges or control buttons to be overlaid on the image.

## Gotchas

- **Z-index layering.** The `avatar` container uses `absolute -bottom-10` and `left-5` to create a "hanging" effect over the banner edge. If the parent container does not have sufficient bottom padding, the avatar will be clipped by the next element in the DOM.
- **Background color hardcoding.** The title container uses an inline style `backgroundColor: "#ffffff"`. This may cause visual inconsistencies if the site-wide theme moves away from pure white or if used in a dark-mode context.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
