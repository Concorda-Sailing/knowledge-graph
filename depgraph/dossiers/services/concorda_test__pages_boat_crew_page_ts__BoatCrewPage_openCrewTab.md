---
node_id: concorda-test::pages/boat-crew.page.ts::BoatCrewPage.openCrewTab
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4cdbb0cb1288fb61129639238d526faac4b58e16e05c2d51357f026fa27994b4
status: llm_drafted
---

# BoatCrewPage.openCrewTab

## Purpose

A specialized Page Object Model (POM) method used to navigate to or interact with the crew management section of a boat. It provides a back-compat shim for the "crew" subtab, which is functionally redundant in the current UI but necessary for maintaining legacy test flows. Use this when a test needs to verify crew membership, invite new members via email, or assert the presence of specific crew members by name or email.

## Invariants

- **`openCrewTab` is a shim.** It checks for the visibility of `this.myCrewTab` before attempting a click to prevent errors in environments where the tab structure has changed.
- **`inviteByEmail` requires explicit tab switching.** The method must click `inviteDialogPasteEmailsTab` to ensure the input fields are reachable, as the dialog defaults to "Search Members".
- **`expectRowForEmail` relies on text-based filtering.** It searches for a `div`, `li`, or `tr` containing the email string to identify a crew member's card.
- **`expectRowForName` is case-insensitive.** It uses a `RegExp` with the `'i'` flag to find name fragments, making it robust against varying name formats.

## Gotchas

- **Back-compat shim requirement.** Per commit `91ad400`, this method exists because the real UI does not have a separate "crew" subtab; `openCrewTab` is a fallback to ensure the test state is correct.
- **External email visibility.** As noted in the docstring for `expectRowForEmail`, if an invite is sent to an external email with no existing account, the row will not be visible in the UI; tests must verify these via API/email capture rather than this POM.
- **Selector fragility.** `expectRowForName` uses a broad locator (`a, div, li, tr`) to handle the split first-name/last-name rendering in `CrewCard`.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the boat detail page and the invite dialog.
- **Side effects**: Successful execution of `inviteByEmail` will trigger a change in the boat's crew list, which may affect any UI components or API calls tracking active crew counts.

## External consumers

None known.
