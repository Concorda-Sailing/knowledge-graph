# Verification log: dynamic_import_shim_ts

## Pre-read prediction

Without the fix: `attachCallEdges` walks `await importESM(...)`, the bare
identifier resolves to a variable in `localByPath`, the existing
`!allClassIds.has(targetId)` check passes (variables aren't classes), and a
`calls → fixture::src/consumer.ts::importESM` edge is pushed. The downstream
validator (`depgraph/lib/edges.py::EDGE_KIND_RULES`) rejects it as
`calls.target = variable` (allowed: function). Each call site contributes one
`edge_error` — two errors here.

With the fix: shim-detection pre-pass identifies `importESM`. The bare-id
branch sees a shim match, captures the first arg's literal, builds
`external::npm::<pkg>`, and pushes an `imports` edge on the module primitive
(`fixture::src/consumer.ts`). The `calls` push is suppressed via early
`continue`.

## Prediction vs expected.json

Matches the fix-applied state — two `imports` edges, one per call site, no
`calls` edge, no `edge_errors`.

## Notes

The fixture mirrors the TS-ESM-in-CJS escape hatch — a top-level
`const importESM = new Function('p', 'return import(p)') as <...>` callable
invoked as `await importESM('pkg')`. Without the fix the call site emits a
`calls → variable` edge against the shim binding (taxonomy violation) and
the real `imports → external::npm::<pkg>` semantic is lost.
