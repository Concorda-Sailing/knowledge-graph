---
node_id: concorda-test::tests/admin/email-config.spec.ts::test@5
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ffb6edcd654f7b92d313275dcf6750c2779a4c04fa2954d76884af24cac3c994
status: current
---

# email config page loads

## Purpose

Verifies that the Admin Email Configuration page is accessible and that its core UI elements (SMTP/Email settings and configuration forms) are visible. This test ensures that administrators can reach the settings required to manage the system's outbound email identity and templates.

## Invariants

- **URL pattern** — The page must be accessible at the `/members/admin/email` path.
- **Visibility of configuration markers** — The page must display text related to `email`, `smtp`, `template`, or `configuration` to be considered loaded.
- **Presence of Save action** — If the configuration content is detected, a "save" button must be visible to allow for state changes.

## Gotchas

- **Selector fragility** — Per commit `f552929`, selectors for the email configuration fields required alignment with the actual UI to ensure a "green run" (passing test). Avoid using overly generic text selectors if the UI text is subject to frequent localization changes.
- **Race conditions on load** — The test uses `page.waitForLoadState('networkidle')` and explicit timeouts (up to 10,000ms) to account for the asynchronous loading of the configuration form.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely via `AdminSystemPage` setup).
- **Side effects**: Verifying the "Save" button visibility is a precursor to testing state changes that would affect the system's ability to send outbound emails.

## External consumers

None known.
