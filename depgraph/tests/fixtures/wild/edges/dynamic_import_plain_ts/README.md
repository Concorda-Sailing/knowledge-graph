# dynamic_import_plain_ts

Plain `await import('...')` calls — no Function-constructor shim. This is the
runtime form authors use when the surrounding module can ship ESM (`type:
"module"` package, `.mjs`, or a bundler that preserves `import()` calls).

## Pattern

- `await import("./helper")` — relative spec; target is a sibling module file.
- `await import("some-pkg")` — bare specifier; target is an external npm pkg.
- `await import("@some-scope/some-pkg")` — scoped pkg; the `@scope` prefix is
  stripped so the target is `external::npm::some-scope`.
- `` await import(`./${name}`) `` — template-string spec with interpolation;
  statically unresolvable, no edge emitted.

## Why tracked

Without this pass, dynamic imports vanish from the corpus: `kg depgraph
dependents <module>` shows no incoming edge from a file that loads it via
`import()`, and impact analysis under-reports. Static `import` declarations
already attribute to the enclosing module via `via: "import_decl"`; this pass
mirrors that for dynamic-import call expressions via `via: "dynamic_import"`.

## v0 behavior

In `attachImportsEdges`, after the static-import + re-export loops, the
extractor walks every CallExpression whose `expression.kind === ImportKeyword`.
For each call with a string-literal first argument:

- Relative spec (`./` or `../`): resolved against the current file's dir,
  trying `<base>{.ts,.tsx,.js,.jsx,.mjs,.cjs}` and `<base>/index{...}`. The
  first candidate present in the module map wins → `imports` edge with
  `confidence: "exact"`, target = `<repoKey>::<resolved-rel-path>`.
- Unresolvable relative spec: `external::unresolved::<spec>`, confidence
  `unresolved`.
- Bare specifier: `external::npm::<pkg>` where `<pkg>` is the spec's leading
  segment with any `@` scope prefix stripped, confidence `fuzzy`.

Non-literal specs (template strings with interpolation, identifier args, etc.)
are skipped — emitting a wrong edge is worse than emitting none.

Shim-form dynamic imports (`new Function('p','return import(p)')` callable
invoked as `shim('pkg')`) are handled by a separate pre-pass in
`attachCallEdges`; see `dynamic_import_shim_ts/`.
