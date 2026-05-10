---
node_id: concorda-web::src/components/event-qr-code.tsx::EventQRCode
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 61c46349d2d8b611de4b5708c72fade2312fb0c08fe5652773626614b11c51dc
status: llm_drafted
---

# EventQRCode

## Purpose

Renders a high-error-correction QR code containing a specific URL, used for event check-ins or registration. It automatically overlays the organization's logo (sourced via `useConstants`) to provide a branded, professional appearance. Use this component when you need to present a scannable link that is visually tied to the organization's identity.

## Invariants

- **Error correction level is fixed at "H"** — This ensures the QR code remains scannable even if the logo-driven "excavation" obscures part of the data or if the print/screen quality is suboptimal.
- **Logo scaling is proportional** — The `logoSize` is always calculated as 20% of the total `size` prop to prevent the logo from overwhelming the QR pattern.
- **Input must be a valid URL string** — The `url` prop is passed directly to `QRCodeSVG`.

## Gotchas

- **Logo source must be absolute** — Per commit `bf3b491`, the `logoUrl` must be sourced from the `/api/constants` endpoint via `useConstants`. If a relative path or a broken URL is passed, the QR code may fail to render the logo or break the component.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
