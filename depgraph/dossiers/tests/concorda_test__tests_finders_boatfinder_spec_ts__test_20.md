---
node_id: concorda-test::tests/finders/boatfinder.spec.ts::test@20
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fb212f00faa14a605c11f122501a47ca02ddd4621b4a029d91fb8e96709e4364
status: llm_drafted
---

# boat card shows relevant info

## Purpose

Verifies that the boat card UI displays essential metadata (sail number, class, and status) and handles navigation to the detail view. This test ensures that the "Boat Finder" component correctly renders the boat's identity and that the interaction with the "Apply" button triggers the expected messaging dialog.

## Invariants

- **Visibility of metadata**: The boat card must contain at least one of the primary identifiers (e.g., `TEST-001` or `j 105`) to be considered a valid match.
- **Navigation flow**: Clicking a boat card must trigger a state change that renders the detail view (e.g., "about", "positions", or "accepting crew" text).
- **Dialog availability**: The "Apply" or "Contact" button must trigger a dialog containing a message input field.

## Gotchas

- **UI IA Changes**: Per commit `cf4317c`, this spec was recently updated to accommodate the "new sidebar IA + unified finder." Changes to the sidebar or finder navigation structure may break the `boatfinder.goto()` or the visibility of the boat card.
- **Race conditions in dialogs**: The `applyButton` interaction requires a `page.waitForTimeout(1000)` to allow the dialog to mount. Removing this or the `timeout: 3_000` on the `messageInput` check will lead to flaky failures in CI.

## Cross-cutting concerns

- **Auth**: None (assumes the user is already authenticated via the `boatfinder.goto()` setup/fixture).
- **Side effects**: Affects the reliability of the "Boat Finder" UI component; failures here indicate a regression in the boat-to-detail navigation path.

## External consumers

None known.
