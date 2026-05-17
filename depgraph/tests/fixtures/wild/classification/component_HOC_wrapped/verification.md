## Prediction (written before running classifier)

Source pattern: `const Card = memo(forwardRef(({ children }, ref) => <div/>))`.

The extractor would emit two primitives for this pattern:
1. `Card` — a `variable` primitive (the outer const binding).
2. `CardInner` — a `function` primitive (the inner arrow, if the extractor
   gives it a synthesised name; otherwise it may be anonymous and not emitted).

The component classifier checks:
- `primitive == "function"` (Card is a variable → skipped)
- `name[0].isupper()` (CardInner starts with C → passes)
- `signature.returns_jsx == True` (CardInner has returns_jsx → passes)

Prediction:
- `Card` (variable): `kind = None` — classifier never examines variables.
- `CardInner` (function, PascalCase, returns_jsx): `kind = component`.

## Actual result (after running)

`Card = None`, `CardInner = component`. Matches prediction.

## v0 limitation — HOC-wrapped outer binding is invisible

The top-level `Card` variable is the public API name that downstream code
imports. But the component classifier cannot reach it because it only
considers `function` primitives. The inner arrow function (`CardInner` in
the corpus) is the one that carries `returns_jsx` and a PascalCase name.

In practice, real extractors may:
- Emit only the outer variable (no inner synthesised name) → nothing classifies.
- Emit both (as in this fixture) → inner classifies, outer stays None.
- Synthesise the outer variable's kind from its value_text heuristics → future work.

This fixture pins option 2 (both emitted). The expected behaviour for option 1
(outer only) is `kind = None` for everything — the classifier has no hook into
variable value_text analysis. That case is not tested here but is a known gap.
