---
node_id: concorda-web::src/components/profile/sections/profile-banner-header.tsx::ProfileBannerHeader
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 42b247c951890194790795226c2c7d6487683d62ca680acc62c24b8248670b18
status: llm_drafted
---

# ProfileBannerHeader

## Purpose

Renders the top-level profile banner, including the hero image and an upload/crop interface. It manages the local state for image manipulation (zoom, crop area, and canvas drawing) to ensure the user can precisely select their banner before committing the update to the server.

## Invariants

- **Input is a `Profile` object** containing a `meta.banner_url` string.
- **Uses `onProfileUpdate`** to propagate the new `Profile` state back to the parent component after a successful upload/crop.
- **Local state manages the crop lifecycle**: `imageSrc` holds the DataURL, while `croppedArea` holds the final dimensions for the canvas draw.

## Gotchas

- **Mobile tap-to-reveal logic**: On touch devices, clicking the banner does not immediately open the file picker. Instead, it triggers a temporary "mobile-active" state to show a UI hint (per commit `24131e4`). This prevents accidental triggers during scrolling.
- **Desktop vs. Mobile UX divergence**: The "X" (remove) button behavior and the way the file picker is triggered are differentiated by `isTouchDevice()` to ensure the `bannerInputRef.current?.click()` doesn't interfere with standard mobile navigation gestures (per commit `d0e5040`).
- **Canvas drawing requirement**: The component must manually construct a `canvas` and use `ctx.drawImage` with the `croppedArea` coordinates to generate the final image; simply passing the raw file to the API is not supported by this component's workflow.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to access the `logout` function, though the primary purpose is profile management.
- **Side effects**: Successful updates via `onProfileUpdate` will refresh the user's profile view in the parent component.

## External consumers

None known.
