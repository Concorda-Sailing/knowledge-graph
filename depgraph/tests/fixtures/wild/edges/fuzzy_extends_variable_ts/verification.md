# Verification log: fuzzy_extends_variable_ts

## Pre-read prediction

Without the fix: `attachInheritanceEdges` resolves `Factory` via
`buildLocalSymbolIndex` to the variable primitive id and emits
`extends -> fixture::src/consumer.ts::Factory` at `confidence: "exact"`.
The reconcile validator (`validate_edge`) rejects it because
`EDGE_KIND_RULES["extends"].target = ["class"]` — `target_kind = "variable"`
is disallowed.

With the fix: `attachInheritanceEdges` looks up the resolved target's
primitive kind in the side index. Because `Factory` is a `variable`, the
edge is emitted at `confidence: "fuzzy"`. `EDGE_KIND_RULES["extends"]` now
includes `variable` in its target whitelist, and a confidence gate in
`validate_edge` requires `extends -> variable` to be `fuzzy` (so exact
`extends -> variable` would still fail, catching extractor regressions).

## Prediction vs expected.json

Matches the fix-applied state: one `extends` edge at fuzzy confidence
pointing at the variable primitive; no taxonomy violations in the
fixture's all-edges-validate sweep.

## Notes

This is the symmetric case to `callable_variable_ts` — that fixture pins
the calls/instantiates target-kind gate (commit 21ee469). #86 extends the
same posture to inheritance edges, but uses fuzzy emission rather than
suppression because the inheritance arrow itself is real and useful for
graph queries; only the static taxonomy is imprecise.
