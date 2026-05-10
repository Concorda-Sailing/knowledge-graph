---
node_id: concorda-test::tests/admin/system-settings.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6e8d441f5bef6efbdcfb1351379fb588f5a6af89b223b9e48224a91ca112a65d
status: llm_drafted
---

# org name field is visible

## Purpose

Verifies the visibility and editability of the organization's name within the Admin System Settings page. It ensures that the name field is not only present but also functional, allowing for a round-trip update (clearing, filling, and reverting) to prevent regression in the organization's identity management.

## Invariants

- **Requires `AdminSystemPage`** — Uses the `AdminSystemPage` POM to navigate to the system settings and interact with the save button.
- **Field visibility check** — The test uses a conditional `if (await nameField.first().isVisible())` block, meaning the test passes if the field is missing rather than failing, provided the field is expected to be present.
- **Reversion logic** — When editing the name, the test captures the `original` value and attempts to restore it to ensure the test is idempotent and doesn't leave the environment in a mutated state for subsequent tests.

## Gotchas

- **Implicit success on missing field** — Because the test wraps the interaction in an `if (await nameField.first().isVisible())` check, it will not throw an error if the organization name field fails to render; it will simply skip the assertion.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (likely established via `ApiClient.login` or similar setup in the parent spec).
- **Side effects**: Mutates the organization name in the test database; relies on the `original` value restoration to prevent breaking other admin-related tests.

## External consumers

None known.
