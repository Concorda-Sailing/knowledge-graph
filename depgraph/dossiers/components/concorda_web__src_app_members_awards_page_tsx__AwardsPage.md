---
node_id: concorda-web::src/app/members/awards/page.tsx::AwardsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b2b306ff33909ad876eead6ccfb791e5728e825953db95ea2ce70347778a2ed9
status: llm_drafted
---

# AwardsPage

## Purpose

The top-level page component for the Awards section of the Yearbook. It acts as a content orchestrator that reads raw markdown/text from the `readContent` utility, splits the content into an introductory section and an honoraria section, and passes the processed strings to `AwardsContent`. Use this component when you need to adjust the high-level layout or the way the "awards" content block is parsed before being handed off to the display components.

## Invariants

- **Content splitting relies on a specific delimiter.** The raw content must be split using the regex `/^---\s*$/m` to separate the `intro` from the `honoraria`.
- **`intro` must be stripped of the H1.** The component passes the `intro` through `stripLeadingH1` to ensure the header doesn't double-render inside the `YearbookHeader` or the content body.
- **`AwardsContent` is the primary consumer.** This page is a thin wrapper; all actual rendering logic for specific award categories resides in `AwardsContent`.

## Gotchas

- **Content structure is brittle.** The split between `intro` and `honoraria` depends entirely on the presence of the `---` delimiter in the source file. If the delimiter is missing or malformed, `intro` and `honoraria` will be incorrectly assigned, as seen in the pattern established by commit `d647124` for yearbook content pages.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
