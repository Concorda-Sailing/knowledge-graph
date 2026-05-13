# Generic extractors

This directory holds framework-shipped extractors that any project can use
without writing their own. Each subdirectory is one language / framework:

- `typescript/` — JS/TS source-walking extractors (uses the TypeScript Compiler API)
- (more to come)

## Using a generic extractor from `project.toml`

Reference the file via the `{framework_dir}` substitution that
`lib/config.render_extractor` resolves to the depgraph repo root:

```toml
[repos.web]
path = "~/concorda-web"
extractor = ["npx", "tsx",
             "{framework_dir}/extractors/generic/typescript/route-calls.ts",
             "--scan", "{path}/src", "--repo-key", "concorda-web"]
```

Each extractor declares `__extractor_version__ = "1.0.0"` (or the
TypeScript equivalent — a top-level `export const EXTRACTOR_VERSION = "1.0.0"`).
The graphui Settings page reads this and shows it in the inventory.

## Conventions

- Project-custom extractors stay the escape hatch. If a generic extractor
  can't express your project's analysis, hand-write one under
  `<data_dir>/extractors/` and reference it via `{data_dir}/...`.
- Generic extractors should be deterministic and side-effect-free: read,
  emit JSON to stdout (one node per line), don't touch the filesystem.
- They MUST be runnable headless from the framework root — no project-
  specific assumptions in code, only via CLI args.
