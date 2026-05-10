---
node_id: concorda-test::pages/setup-wizard.page.ts::SetupWizardPage.togglePosition
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 584ade8c66f6c733c5426871b13973dd42e4693777afc85ab9e1714f034cd982
status: current
---

# SetupWizardPage.togglePosition

## Purpose

A helper method to toggle a specific sailing position (e.g., "Trimmer", "Bowman") within the Setup Wizard. It uses a text-based locator to find the first occurrence of the provided `name` and performs a click. This is used to manipulate the position badges during the profile creation flow.

## Invariants

- **Input is an exact string match.** The method uses `{ exact: true }` on the text locator, so the input must match the UI label precisely (e.g., "Bowman" not "Bowman ").
- **Selects the first match.** If multiple elements share the text, it only interacts with the `.first()` element found in the DOM.
- **Requires visibility.** The click will fail if the element is not reachable or visible in the viewport.

## Gotchas

- **Race condition with the sailing-question gate.** Per commit `cd62e08`, this method (and the broader wizard flow) must be carefully sequenced against the "sailing-question" gate to ensure the position elements are actually present and interactable in the DOM before the click is attempted.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to complete the profile/resume mutation.
- **Side effects**: Changes to positions are part of the `sailing-resume` payload; successful toggles are verified by the `waitForAutoSave` method watching for a `PUT /profile/sailing-resume` request.

## External consumers

None known.
