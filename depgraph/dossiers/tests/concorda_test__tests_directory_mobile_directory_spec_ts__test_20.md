---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@20
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fc67a0abe1d94387ff1aefb637cf76cb1997610a22e91d5f15ae91de21672fb3
status: llm_drafted
---

# view toggle is hidden on mobile

## Purpose

Verifies that the mobile view of the Member Directory correctly implements responsive design constraints. It ensures that UI elements intended for desktop (like the view toggle and alphabet filter) are hidden at a 375px viewport to prevent clutter, and confirms that the layout does not suffer from horizontal overflow. It also validates that the mobile view renders actual member data (via `h3` headings) rather than an empty state or a table.

## Invariants

- **Viewport width is 375px** — The test assumes a mobile-first width to check for horizontal overflow and element visibility.
- **View toggle is absent** — The `grid view` and `list view` buttons must have a count of 0 when the viewport is in mobile mode.
- **Alphabet filter is absent** — The single-letter navigation buttons (e.g., the "M" button) must not be present in the DOM on mobile.
- **CardGrid must contain data** — The test requires that the `div.grid` contains at least one `h3` element representing a member, ensuring the mobile view isn't just a successful render of an empty state.
- **No `<table>` on mobile** — The desktop list-view `<table>` must be absent from the DOM in the mobile viewport.

## Gotchas

- **Selection strategy must use headings** — Per commit `a2aa8e7`, do not rely on `data-slot` attributes to identify member cards; the test must select members by searching for the `h3` heading within the `CardGrid`.
- **Rounding tolerance for overflow** — The `scrollWidth` check allows for a 1px tolerance (`toBeLessThanOrEqual(376)`) to account for potential sub-pixel rendering issues in different browser engines.
- **Desktop regression** — The desktop view (1280px) is a separate test block; changes to the directory's layout logic can easily break the desktop-specific `table` or `view toggle` visibility if not carefully scoped.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: N/A

## External consumers

None known.
