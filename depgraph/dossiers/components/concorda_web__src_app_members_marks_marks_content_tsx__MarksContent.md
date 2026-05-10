---
node_id: concorda-web::src/app/members/marks/marks-content.tsx::MarksContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4b07df074ea420cf00d3b23caa7a1d259c7aecde91314dc11895b834663734e4
status: current
---

# MarksContent

## Purpose

Renders the main content area for the "Marks" section, specifically handling the display of historical performance data and the generation of a PDF report. It manages the state for PDF generation and the visual formatting of the report. This component is the primary consumer of the `intro` text and is responsible for the high-fidelity export of the marks table via `jsPDF`.

## Invariants

- **PDF generation is asynchronous and side-effect heavy.** It uses dynamic imports for `jspdf` and `jspdf-autotable` to keep the initial bundle size small.
- **Logo embedding is non-blocking.** The `fetchLogoDataUrl` helper returns `null` if the fetch fails or the logo is missing, allowing the PDF to still render without the header image.
- **PDF dimensions are fixed.** The document uses `unit: "pt"`, `format: "letter"`, and a hardcoded `headerHeight` of 80.
- **Branding is hardcoded.** The navy color (`[0, 45, 128]`) and the tint (`[243, 246, 252]`) are used for the header background and zebra striping.

## Gotchas

- **Timezone-aware PDF headers.** Per commit `f444b4c`, the date rendered in the PDF header must use the organization's timezone via `useConstants().timezone` rather than the browser's local time to ensure consistency between the web view and the exported document.
- **Logo loading is a potential failure point.** If `logoUrl` is invalid or the fetch fails, the `try/catch` in `fetchLogoDataUrl` prevents the entire PDF generation from crashing, but the header will lack the brand identity.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The PDF generation relies on the `logoUrl` and `timezone` provided by `useConstants()`.

## External consumers

None known.
