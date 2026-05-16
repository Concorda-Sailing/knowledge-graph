# Verification log: jsx_corners

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The source file `src/components.tsx` contains:
- `const MemoCard = React.memo(...)` — CallExpression initializer (not ArrowFunction/FunctionExpression)
- `function CardList(...)` — named function declaration returning JSX array
- `function MaybeCard(...)` — named function declaration with conditional null return
- `function sideEffectRender(...)` — named function declaration with JSX in body but void return

The extractor paths:
- `MemoCard`: initializer is a CallExpression → NOT picked up by extractFunctions (which requires
  ArrowFunction or FunctionExpression initializer). Skipped by extractVariables too? No — 
  extractVariables skips arrow/function/object initializers but NOT call expressions. So MemoCard
  emits as a **variable** primitive. Its JSX is inside the memo callback, invisible to the extractor.
- `CardList`: top-level function with body → function primitive, bodyHasJsx scans descendants
  of the body and finds `<li>` elements → returns_jsx=true
- `MaybeCard`: top-level function with body → function primitive, bodyHasJsx finds `<div>` →
  returns_jsx=true (even though one branch returns null)
- `sideEffectRender`: top-level function with body → function primitive, bodyHasJsx finds `<span>`
  in the variable initializer expression → returns_jsx=true (pinned behavior — JSX anywhere in
  body counts, not just in return expressions)

Expected primitives:
- `fixture::src` (primitive=package, owner=null)
- `fixture::src/components.tsx` (primitive=module, owner=null)
- `fixture::src/components.tsx::MemoCard` (primitive=variable, owner=null) — memo-wrapped
- `fixture::src/components.tsx::CardList` (primitive=function, owner=null, returns_jsx=true)
- `fixture::src/components.tsx::MaybeCard` (primitive=function, owner=null, returns_jsx=true)
- `fixture::src/components.tsx::sideEffectRender` (primitive=function, owner=null, returns_jsx=true)

Expected edges: none

## Prediction vs expected.json
- Matches: 6 of 6 — prediction exactly matched expected.json
- Discrepancies: none

## Expected vs actual (from running the extractor)
- Matches: 6 of 6 — all expected primitives present, no extras
- Discrepancies: none
- Key verifications:
  - `MemoCard` emitted as variable (not function) — memo() wrapper not unwrapped, as predicted
  - `CardList.returns_jsx=true` — JSX array elements found by bodyHasJsx descendant scan
  - `MaybeCard.returns_jsx=true` — JSX in non-null branch found despite null in other branch
  - `sideEffectRender.returns_jsx=true` — JSX in body variable initializer found even though
    function returns void (pinned: bodyHasJsx counts JSX anywhere in body, not just returns)

## Notes
- `MemoCard` emits as variable (not function) because `React.memo(...)` is a CallExpression —
  the extractor does not unwrap HOC call arguments.
- `bodyHasJsx` scans ALL descendants, not just return expressions. So JSX in a variable
  initializer inside the function body still sets returns_jsx=true. This is pinned behavior.
- The `import React from "react"` line does not generate any primitive (imports are not extracted
  in Phase 1).
