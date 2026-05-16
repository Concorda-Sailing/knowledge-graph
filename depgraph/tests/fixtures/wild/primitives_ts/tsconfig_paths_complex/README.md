# tsconfig_paths_complex

## What's tested

A project with multiple overlapping tsconfig `paths` aliases in `tsconfig.json`, and source files
that import from those aliases. Phase 1 captures only primitives; the path-alias edge resolution
is deferred to Phase 3.3.

The fixture verifies:
- Primitives from all source files are emitted correctly regardless of tsconfig.json presence
- The extractor does not crash or misparse when a tsconfig.json with complex paths is present
  in the repo root
- Import statements referencing path aliases appear in the source but generate NO additional
  primitives (imports are Phase 3.3)

## Why a naive extractor would break

A naive extractor that tries to eagerly resolve `@/components/Card` or `~lib/utils` aliases
at extraction time will either crash (alias not resolvable without the build tool) or silently
drop the importing file. The layered-substrate extractor ignores import resolution entirely
at Phase 1 — it extracts only the structural primitives present in each file.
