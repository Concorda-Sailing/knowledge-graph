---
node_id: concorda-web::src/components/ui/avatar-upload.tsx::cropImage
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf101eddb65906f0d71b39f781b5573392f1eeccf53cfa9dcb6d6a8678f8de3b
status: current
---

# cropImage

## Purpose

The `cropImage` helper performs the client-side heavy lifting for generating a cropped `File` object from a source image. It uses an off-screen canvas to draw a specific sub-section of the image and converts the result into a JPEG blob. This is a private utility used by the `AvatarUpload` component to prepare the final image for upload.

## Invariants

- **Returns a `Promise<File>`** containing the cropped image data.
- **Hardcodes output format to `image/jpeg`** with a quality setting of `0.95`.
- **Requires a valid `imageSrc` and `crop` area** (x, y, width, height) to function; failure to provide a valid `imageSrc` will result in an empty canvas or a broken promise.
- **The resulting File is named `"avatar.jpg"`** by default.

## Gotchas

- **Tailwind JIT issues:** Per commit `aa16d9e`, do not use template literals for dynamic sizing in the component that calls this (e.g., `size-${size}`). The base `AvatarUpload` component uses inline styles for base size because Tailwind classes do not JIT-expand for dynamic values.
- **Responsive sizing mismatch:** Per commit `f068687`, the visual size of the avatar (e.g., 96px vs 140px) is controlled by the `className` passed to the parent component, not by the `cropImage` logic itself.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: The resulting `File` is passed to `onUpload`, which typically triggers a multipart/form-data POST to the user profile endpoint.

## External consumers

None known.
