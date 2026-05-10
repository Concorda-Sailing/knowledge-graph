---
node_id: concorda-test::pages/directory.page.ts::DirectoryPage.searchFor
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a2f66769b36e72e978709b4bf5b7e49c8c6ff15e3c16465f3b5e77842ba3d84a
status: llm_drafted
---

# DirectoryPage.searchFor

## Purpose

The `searchFor` method performs a text-based search within the member directory. It populates the `searchInput` field with the provided query and waits for the network to reach an idle state to ensure the filtered results are rendered before the test proceeds.

## Invariants

- **Input is a raw string.** The method accepts any string and injects it directly into the search input.
- **Triggers a network-idle wait.** The method explicitly calls `this.page.waitForLoadState('networkidle')` after filling the input to ensure the search results-fetch has completed.
- **Requires `goto()` to be called first.** The method assumes the browser is already at the `/members/directory` path.

## Gotchas

- **Initial scaffolding only.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the reliability of the `networkidle` wait depends on the API response time for the directory search endpoint.

## Cross-cutting concerns

- **Auth**: Requires a session established via `LoginPage.login` (or similar) to access the `/members/directory` route.
- **Side effects**: None.

## External consumers

None known.
