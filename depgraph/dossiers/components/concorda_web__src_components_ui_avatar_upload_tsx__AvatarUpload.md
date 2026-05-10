---
node_id: concorda-web::src/components/ui/avatar-upload.tsx::AvatarUpload
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 87228476692a3cb8b14e04fd9914e1850026fcab74fe18e6f0d0c64c607b6b5e
status: llm_drafted
---

# AvatarUpload

## Purpose

Provides a client-side image cropping and upload interface for user avatars. It manages the local state for image selection, cropping (x, y, and zoom), and the conversion of the cropped area into a `File` object via `cropImage`. Use this component when a user needs to update their profile picture, as it handles the complex transition from a raw file selection to a processed, cropped `File` ready for API submission.

## Invariants

- **Input is a URL string.** `imageUrl` is used to display the current avatar; if null or empty, the component should handle the fallback (implied by `imageSrc` state).
- **`onUpload` receives a `File` object.** The component is responsible for calling `cropImage` to transform the `imageSrc` and `croppedArea` into a valid `File` before passing it to the parent.
- **`onRemove` is triggered by `handleRemove`.** This function calls `e.stopPropagation()` to prevent event bubbling if the avatar is nested within clickable elements (like a profile card).
- **`size` prop controls the visual footprint.** The component uses the `size` prop to manage the dimensions of the upload area.

## Gotchas

- **Avoid template literals for base size classes.** Per commit `aa16d9e`, using template-literal Tailwind classes for the base size prevents JIT expansion; use inline styles or static classes for the core dimensions.
- **Responsive sizing via `className`.** Per commit `f068687`, the component relies on the `className` prop to handle responsive scaling (e.g., 96px on mobile vs 140px on desktop). Do not hardcode responsive logic inside the component; pass it in via `className`.
- **`e.target.value = ""` in `handleFileSelect`.** This is required to allow the user to select the same file twice in a row (e.g., if they cancel the crop mid-way).

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers profile/user identity updates when `onUpload` is successfully resolved by the parent component.

## External consumers

None known.
