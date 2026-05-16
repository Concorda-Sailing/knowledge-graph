# Verification log: validators

**Last reviewed:** 2026-05-16 by Claude (haiku subagent under Opus controller)
**Components:** validate_primitive, validate_edge
**Source:** depgraph/lib/primitives.py, depgraph/lib/edges.py

## Inputs exercised

For each input below, the "Predicted" column was filled in BEFORE running.
Discrepancies between Predicted and Observed (if any) are noted at the bottom.

| Input | Predicted | Observed |
|---|---|---|
| `validate_primitive(minimal_valid)` — all required fields present and correct | `[]` | `[]` |
| `validate_primitive(d)` with `schema_version` deleted | error mentioning `schema_version` | `["missing fields: ['schema_version']"]` |
| `validate_primitive(d)` with `primitive="function"`, `name="Cls.meth"`, `owner=None` | error mentioning owner | `["function with \`.\` in name must have owner set: 'Cls.meth'"]` |
| `validate_primitive(d)` with `primitive="function"`, `name="Cls.meth"`, `owner="Cls"` | `[]` (owner set, so valid) | `[]` |
| `validate_primitive(d)` with `schema_version=1` | error mentioning version mismatch | `['schema_version must be 2, got 1']` |
| `validate_primitive(d)` with `primitive="unknown_type"` | error listing valid primitives | `["primitive must be one of ['class', 'function', 'module', 'package', 'variable'], got 'unknown_type'"]` |
| `validate_primitive(d)` with `edges_out=[{..., "confidence": "probably"}]` | error mentioning confidence | `["edge confidence must be one of ['exact', 'fuzzy', 'unresolved'], got 'probably'"]` |
| `validate_primitive({"schema_version": 2, "primitive": "function"})` (8 fields missing) | single error listing all missing fields; short-circuit after missing check | `["missing fields: ['attributes', 'edges_out', 'extractor', 'id', 'kind', 'name', 'owner', 'signature', 'source', 'structural_hash']"]` |
| `validate_edge({"kind": "calls", "source_kind": "function", "target_kind": "function", "confidence": "exact"})` | `[]` | `[]` |
| `validate_edge({"kind": "extends", "source_kind": "function", "target_kind": "class", "confidence": "exact"})` | error mentioning source kind | `["edge 'extends' disallows source kind 'function'; allowed: ['class']"]` |
| `validate_edge({"kind": "calls", "source_kind": "function", "target_kind": "function", "confidence": "probably"})` | error mentioning confidence | `["confidence must be exact\|fuzzy\|unresolved, got 'probably'"]` |
| `validate_edge({"kind": "not_a_real_kind", ...})` | error mentioning unknown edge kind | `["unknown edge kind: 'not_a_real_kind'"]` |
| `validate_edge({"kind": "references", "source_kind": "module", "target_kind": "class", "confidence": "fuzzy"})` | `[]` — references allows any→any | `[]` |
| `validate_edge({"kind": "tests", "source_kind": "function", "target_kind": "variable", "confidence": "unresolved"})` | `[]` — tests allows function→variable | `[]` |
| `validate_edge({"kind": "calls", "confidence": "exact"})` — no source_kind/target_kind | Predicted an error or empty — uncertain; the check is `if sk := edge.get("source_kind")` which short-circuits on falsy | `[]` — **prediction was uncertain; confirmed empty**: omitting source_kind/target_kind entirely skips the kind-compatibility checks |
| `validate_edge({"kind": "calls", "source_kind": "class", "target_kind": "function", "confidence": "exact"})` | error: calls disallows class source | `["edge 'calls' disallows source kind 'class'; allowed: ['function']"]` |

## Observations

**Finding 1 — Missing-field check short-circuits; other errors are not reported:**
When any required field is missing from a primitive dict, `validate_primitive` returns immediately
with only the missing-field error. A caller cannot tell from one call whether a dict has a missing
field AND an invalid `schema_version` — they must fix missing fields and re-validate to surface the
rest. This is documented by the short-circuit comment in the source (`# short-circuit; rest of
validation assumes presence`). Callers building primitives programmatically should be aware.

**Finding 2 — `validate_edge` source_kind/target_kind are optional:**
The walrus-operator guard `if (sk := edge.get("source_kind")) and ...` means an edge dict with no
`source_kind` key passes the source-kind check unconditionally. This is intentional (per the
docstring: "caller-supplied; edges on disk don't carry them since the source is known from context")
but means `validate_edge` cannot catch a missing source_kind as a structural error — it simply
skips the compatibility check. Any tool that calls `validate_edge` without supplying these fields
gets a false-clean result on the kind rules. Fine for on-disk edges; potentially surprising in test
fixtures that forget to include them.

**Finding 3 — `validate_primitive` validates edge confidence but not edge kind:**
`validate_primitive` iterates `edges_out` and checks each edge's `confidence` value, but does NOT
call `validate_edge` or check `edge["kind"]` against `ALL_EDGE_KINDS`. A primitive with
`edges_out=[{"kind": "invented_kind", "confidence": "exact"}]` passes `validate_primitive` cleanly.
Full edge validation requires calling `validate_edge` separately. Worth noting for any caller that
only runs `validate_primitive` and assumes edges are fully validated.

## Status
✓ verified — all predictions matched (one prediction was marked uncertain and the observed behavior confirmed the expected walrus-guard short-circuit). Three structural observations recorded above.
