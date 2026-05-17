# dynamic_import_shim_ts

The TS-ESM-in-CJS escape hatch: a variable initialized to
`new Function('p', 'return import(p)')` is invoked with a string literal to
dynamically import an npm ESM package without tsc rewriting it to `require()`.

## Pattern

- `const importESM = new Function('specifier', 'return import(specifier)') as ...`
- Call sites: `await importESM('@some-scope/some-pkg')` /
  `await importESM('plain-pkg')`.

## Why tricky

The naive extractor walks the call expression, finds `importESM` resolves to a
`variable` primitive, and emits `calls → importESM`. That violates the edge
taxonomy (`calls.target = function`) AND loses the real semantic — the
function depends on the *package being imported*, not on the local shim.

## v0 behavior

A pre-pass in `attachCallEdges` detects the shim shape (NewExpression of
`Function` with two string-literal args where the body matches
`/^\s*return\s+import\s*\(\s*<paramname>\s*\)\s*;?\s*$/`). At each call site
to a known shim, the variable-targeted `calls` edge is suppressed and an
`imports` edge is emitted on the enclosing module with
`via: "dynamic_import_shim"`, `confidence: "fuzzy"`. Target id matches static
named-import fallback: `external::npm::<pkgName>` where `pkgName` is the
specifier's leading segment with any `@` scope prefix stripped.
