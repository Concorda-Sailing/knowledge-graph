# default_export_resolution_ts

A consumer does `import Widget from './lib'`; `lib.ts` does `export default Widget` where `Widget` is a named class defined in the same file.

## Pattern

- `lib.ts` defines and exports `Widget` as a named class, then re-exposes it as the file's default with `export default Widget`.
- `consumer.ts` does `import Widget from './lib'` and uses it via `new Widget()`.

## Why tricky

The default-import branch in `attachImportsEdges` (extract.ts) emits a target of `${repoKey}::${targetRel}::default`. There is no primitive with that id — `Widget` is extracted under its real name. So the import edge is an orphan, and the `instantiates` resolution (which consults the local imports table) lands on the placeholder rather than the class.

## v0 behavior

When the target file has an `ExportAssignment` whose expression is an identifier naming a top-level symbol, the default-import target resolves to that symbol's id (confidence `fuzzy` to signal the resolution went through the default alias rather than landing directly on a primitive). Anonymous-expression default exports (`export default function(){}`, `export default {...}`) fall back to the synthetic placeholder as before — they have no named symbol to point at.
