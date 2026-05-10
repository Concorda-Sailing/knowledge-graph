---
node_id: concorda-web::src/components/profile/sections/use-inline-edit.tsx::useInlineEdit
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ead61dd18b89bd0aaa644ef825640e233976d2703760ed35e154d5c9eb5f6c64
status: llm_drafted
---

# useInlineEdit

## Purpose

Thin React context consumer for inline-edit UX on the profile page. Despite the "hook" name, it owns no state — it reads from `InlineEditContext` (provided by `profile-inline.tsx`) and returns a section-scoped slice: `isEditing`, `saving`, `beginEdit`, `cancelEdit`, `saveEdit`, `registerForm`. State, dirty tracking, and the actual save handler live in the provider; this hook just narrows the context to one section so each section component doesn't have to compare `editing === "racing"` itself. Also exports `InlineEditProvider` and the `EditingSection` union (`"personal" | "crewfinder" | "racing" | "communications" | "security" | null`). Used by 5 profile section components plus the provider itself.

## Invariants

- **Single-edit-at-a-time UX**: parent owns one `editing: EditingSection` value, so opening one section auto-cancels any other. This invariant lives in the provider; the hook just reads it.
- **`EditingSection` is the closed set of editable sections** — adding a section means widening the union and updating the provider's switch in `profile-inline.tsx`.
- **Throws if used outside `InlineEditProvider`** — standard "context or die" pattern. Don't render a section component without the provider in its parent tree.
- **`registerForm(key)` returns a curried `(handle: FormHandle) => void`** matching React's ref-callback shape. Each section's form registers a `FormHandle` (submit/reset/isDirty) by key; the provider's `saveEdit` dispatches into those handles.
- The hook itself is ~12 lines. Section, dirty tracking, and save logic all live in the provider — don't move state in here.

## Gotchas

- **Section keys vs file names diverge.** `sailing-experience-section.tsx` uses key `"crewfinder"`, not `"sailing-experience"` — historical. Renaming the file does NOT rename the union value.
- **Dirty tracking is delegated to each form.** Per-form `FormHandle.isDirty` is the source of truth, not anything in the provider. A form that forgets to register its handle will have its save silently skipped.
- **5 callers, not "all sections in `sections/`".** The four files `agent-access`, `calendar-subscription`, `crewfinder-optin`, `directory-publish`, and `profile-banner-header` do NOT use this hook — they have their own edit affordances or are display-only. Don't assume every sibling under `sections/` is a dependent.
- **Adding a section** widens `EditingSection` AND requires editing the provider's `saveEdit` switch in `profile-inline.tsx` (string-based, not type-checked). TypeScript catches the call-site union check; the provider switch is a runtime trap.

## Cross-cutting concerns

- **Tightly coupled to `profile-inline.tsx`** — provider+hook are a unit. Refactoring one without the other is a ~runtime-throw bug, not a type error.
- **No auth, no network, no audit, no websocket** — pure UI state coordination.

## External consumers

None outside `concorda-web`. Profile-page-only abstraction; not used elsewhere in the web app, not consumed by the iOS app.

## Open questions

- Should dirty tracking move into the provider so all sections share one state machine? Today each form re-implements it.
- Is the section-name string contract worth replacing with typed action keys? Would catch the file-name-vs-key drift but requires a coordinated refactor of the provider.
