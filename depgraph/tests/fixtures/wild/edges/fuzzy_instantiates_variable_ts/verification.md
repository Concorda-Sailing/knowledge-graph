# Verification log: fuzzy_instantiates_variable_ts

## Pre-read prediction

Without the fix: `attachCallAndVarAccessEdges` resolves `Factory` via
`localNames` to the variable primitive id and gates emission on
`allClassIds.has(targetId)`. In this fixture (no interface or class with
the same name) the variable id is NOT in `allClassIds`, so the edge is
dropped silently — fixture is green but the gap is invisible. The wild
case where the bug fires has a name-collision (interface `ZodObject` plus
`const ZodObject`) that puts the id into BOTH `allClassIds` and reconcile's
`by_id` as the variable — the gate passes, confidence=exact, validator
rejects.

With the fix: the gate switches from `allClassIds.has(targetId)` to a
kind lookup against the per-primitive side index. The emitted edge's
confidence reflects the resolved target's primitive kind:

- target.kind == "class"    -> confidence: "exact"
- target.kind == "variable" -> confidence: "fuzzy"
- target.kind == "function" -> confidence: "fuzzy"
- target external/unresolved/other -> dropped

`EDGE_KIND_RULES["instantiates"]` now lists `variable` and `function` in
its target whitelist, and `_TARGET_KIND_CONFIDENCE_GATES` requires those
combinations to be at fuzzy confidence — so exact `instantiates -> variable`
remains a taxonomy error.

## Prediction vs expected.json

Matches the fix-applied state: `makeOne` emits one `instantiates` edge at
fuzzy confidence pointing at the `Factory` variable. No exact taxonomy
violations.

## Notes

This is the symmetric case to `fuzzy_extends_variable_ts` (commit a03479d,
#86). #88 extends the same posture from inheritance edges (extends /
implements) to construction edges (instantiates). Wild-probe on
colinhacks/zod confirmed all 71 `instantiates -> variable` edge_errors
clear after the fix lands.
