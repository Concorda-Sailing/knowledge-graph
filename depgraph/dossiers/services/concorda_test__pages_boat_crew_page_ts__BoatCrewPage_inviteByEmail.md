---
node_id: concorda-test::pages/boat-crew.page.ts::BoatCrewPage.inviteByEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: da63187cb09cf342faf894bd78357e66506f95f95bdbe9283788c18dd7c825a4
status: current
---

# BoatCrewPage.inviteByEmail

## Purpose

Automates the process of inviting a new crew member via email within the Boat Crew interface. It explicitly handles the transition from the default "Search Members" tab to the "Paste Emails" tab to ensure deterministic behavior during the invite flow. This method is used when a test needs to simulate adding an external user or a new identity to a boat's roster.

## Invariants

- **Explicitly switches to `inviteDialogPasteEmailsTab`** — The dialog defaults to the search tab, so this method must click the paste tab to ensure the email input is reachable.
- **`notes` field is optional** — If `notes` is provided, the method checks for visibility before attempting to fill it to avoid errors on UI states where the field might be hidden.
- **Returns `Promise<void>`** — The method is purely an action-based automation step with no return value.

## Gotchas

- **Deterministic tab switching** — Per the docstring, the dialog defaults to the "Search Members" tab; failing to click `inviteDialogPasteEmailsTab` will cause the `inviteEmailInput.fill` call to fail because the element will not be interactable.
- **External email visibility** — As noted in the `expectRowForEmail` documentation, if the target email is an external address with no existing account, a visible card may not appear in the UI after the invite. Callers must verify success via API or email capture rather than relying on a DOM element.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login`) to access the Boat Crew management interface.
- **Side effects**: Successful execution results in a new invite/member record in the database, which may trigger notifications or update the boat's crew count.

## External consumers

None known.
