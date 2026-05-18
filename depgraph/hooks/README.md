# Hooks

Two scripts, two phases:

| Script | Phase | Purpose |
|---|---|---|
| `pre_edit_inject.py` | `pre-edit` (PreToolUse: Edit / Write / MultiEdit) | Inject dossier + dependents + warnings into Claude's context before the edit. |
| `post_edit_regen.py` | `post-edit` (Stop) | Re-extract touched files, run reconcile, surface drift signals at end of turn. |

Both scripts live in this directory and are invoked by the `kg` orchestrator
on behalf of any registered graph. **Don't wire these scripts directly in
`settings.json`** — the canonical wiring goes through `kg hook <phase>`,
which classifies the edited path against `~/.claude/kg-graphs.toml`, picks
the owning graph, and dispatches to that graph's hook script. This lets a
single Claude Code session support multiple registered knowledge graphs
without one project's hooks firing against another project's files.

## Wiring

The recommended setup is `kg install hooks --apply`, which writes the
right block into `~/.claude/settings.json`. That command produces:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "/home/<user>/tools/knowledge-graph/bin/kg hook pre-edit" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "/home/<user>/tools/knowledge-graph/bin/kg hook post-edit" }
        ]
      }
    ]
  }
}
```

`kg hook <phase>` reads `~/.claude/kg-graphs.toml`, finds the registered
graph whose source roots include the edited file, and runs that graph's
`depgraph/hooks/<script>.py`. See `docs/CLI.md` § *Hook dispatcher* for
the full phase list (`pre-edit`, `post-edit`, `pre-irreversible`,
`session-start`, `session-end`).

## Failure behavior

Both hook scripts wrap their body in a try/except and emit a visible
warning rather than failing silently. Editing without context is worse
than knowing context is missing — see `DRIFT.md` scenario 13.

If you need to disable hooks temporarily, comment out the entries in
`settings.json` and run `kg depgraph context <file>` manually for the
same content.

## Latency budget

| Phase | Target | Hard cap |
|---|---|---|
| pre-edit | < 200ms | 2s (then emit warning) |
| post-edit | < 5s | 30s (extractors are heavier) |

`pre_edit_inject.py` only reads JSON files and a markdown file, so the
budget is comfortable as long as the node count stays under ~5000. If it
grows, switch to a single `nodes/index.json` pre-built by reconcile.

`post_edit_regen.py` is the slow path because it spawns extractors. It
deliberately scopes to *touched files only*; full regens belong to
`kg depgraph regen` and run on demand or periodically.
