# Migration — pre-config to per-repo `project.toml`

If your project's depgraph data dir was wired to the old framework (pre-config-driven, with hardcoded repo names and dispatch), you need the changes below to keep working with the current `~/tools/depgraph/`.

The framework is no longer project-coupled. Everything project-specific is read from `<DEPGRAPH_DATA_DIR>/project.toml`.

## 1. Rewrite `project.toml` to per-repo tables

**Before** (flat name → directory map):

```toml
[repos]
api = "concorda-api"
web = "concorda-web"
test = "concorda-test"
```

**After** (one table per repo, carrying path + extractor command):

```toml
[project]
name = "<project>"
primary_repo = "api"   # whose git HEAD stamps corpus-meta git_commit

[repos.api]
path = "~/<project>-api"
extractor = ["python3", "{data_dir}/extractors/extract_api.py"]
files_arg = "--only"   # if the extractor accepts repeated --only <file> args

[repos.web]
path = "~/<project>-web"
extractor = ["npx", "tsx", "{data_dir}/extractors/extract_web.ts"]

# Optional — only if you want `bin/depgraph context` to surface logigraph
# rules claiming a depgraph node.
[logigraph]
data_dir = "~/<project>/logigraph"

# Optional — only if you use `bin/depgraph memory-sync` to mirror Claude
# memories. Path is relative to $HOME.
[memory]
mirror = "<project>/memory"
```

Substitutions available in `extractor` tokens:
- `{data_dir}` — the depgraph data dir containing `project.toml`.
- `{path}` — the repo's resolved `path` value.

## 2. Set `DEPGRAPH_DATA_DIR` explicitly

The previous default of `~/concorda/depgraph` is gone. Two options:

- **Recommended**: every Claude Code hook in `.claude/settings.json` should already prefix its command with `DEPGRAPH_DATA_DIR=/path/to/<project>/depgraph`. Verify that's still true.
- **CLI usage**: either export `DEPGRAPH_DATA_DIR` in your shell rc, or `cd` into a directory containing `project.toml + nodes/` before running `bin/depgraph`. The framework walks cwd-ancestors to find it; otherwise it fails loudly with a helpful message.

The legacy env var `CONCORDA_DEPGRAPH_PATH` is gone — use `DEPGRAPH_DATA_DIR`.

## 3. Relocate project-specific assets out of the framework repo

If you had real-data examples checked in under `~/tools/depgraph/examples/`, move them to your project's `<DEPGRAPH_DATA_DIR>/examples/`. The framework's `examples/` now holds only generic format pointers.

## 4. Verify extractor commands

The `if repo == "concorda-api"` dispatch in `hooks/post_edit_regen.py` is gone. Each repo's extractor command lives in its `[repos.<key>].extractor` entry. If you had a custom extractor not present in the old dispatch table, this is now a config edit rather than a code patch.

## 5. Smoke-test

```bash
DEPGRAPH_DATA_DIR=/path/to/<project>/depgraph bin/depgraph regen
DEPGRAPH_DATA_DIR=/path/to/<project>/depgraph bin/depgraph self-check
DEPGRAPH_DATA_DIR=/path/to/<project>/depgraph bin/depgraph validate
```

`self-check` now synthesizes its fake file path from your first configured `[repos.*]` table, so the hook smoke-test does not depend on any specific source file existing.

## What didn't change

- Node JSON shape, dossier markdown shape, schema files.
- Reverse-edge / dependents index layout.
- The PreToolUse / Stop hook contract.
- The `bin/depgraph` subcommand surface.

Your existing nodes, dossiers, and indexes all keep working — this migration is purely about how the framework finds and dispatches over your project's repos.
