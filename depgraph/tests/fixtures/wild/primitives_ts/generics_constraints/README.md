# generics_constraints

## What's tested

- A class with 4 type parameters, each with a `extends` constraint
- A generic method on a non-generic class (method-level type param)
- A conditional type alias (`T extends U ? A : B`)

## Why a naive extractor would break

A naive extractor that reads type parameter names without their constraints either:
1. Stores only the raw name (losing the constraint), or
2. Crashes/emits wrong data when it encounters complex constraint expressions like
   `T extends Record<string, unknown>`.

The extractor uses `tp.getName()` which returns just the parameter name (e.g., `"T"`) —
not the constraint expression. This is correct: `attributes.template_parameters` stores names
only. The fixture verifies that all 4 names are captured and the constraint text doesn't leak
into the name array.

For generic methods on non-generic classes: the method's type parameters are NOT captured in
`attributes.template_parameters` (which is always `[]` for function primitives in the current
extractor — the function primitive only captures the class's template params via the class path).
This is a known limitation pinned here as a regression target.
