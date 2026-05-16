# Hooks

Two scripts, two events:

| Script | Event | Purpose |
|---|---|---|
| `pre_edit_inject.py` | `PreToolUse` (Edit / Write / MultiEdit) | Inject dossier + dependents + warnings into Claude's context before the edit. |
| `post_edit_regen.py` | `Stop` | Re-extract touched files, run reconcile, surface drift signals at end of turn. |

## Wiring

Add to `~/.claude/settings.json` (or per-project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python3 ~/tools/knowledge-graph/depgraph/hooks/pre_edit_inject.py" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/tools/knowledge-graph/depgraph/hooks/post_edit_regen.py" }
        ]
      }
    ]
  }
}
```

## Failure behavior

Both hooks wrap their body in a try/except and emit a visible warning rather than failing silently. Editing without context is worse than knowing context is missing — see DRIFT.md scenario 13.

If you need to disable the hooks temporarily, comment them out in `settings.json` and run `bin/depgraph context <file>` manually for the same content.

## Latency budget

| Hook | Target | Hard cap |
|---|---|---|
| PreToolUse | < 200ms | 2s (then emit warning) |
| Stop | < 5s | 30s (extractors are heavier) |

`pre_edit_inject.py` only reads JSON files and a markdown file, so the budget is comfortable as long as the node count stays under ~5000. If it grows, switch to a single `nodes/index.json` pre-built by reconcile.

`post_edit_regen.py` is the slow path because it spawns extractors. We deliberately scope to *touched files only*; full regens belong to `bin/depgraph regen --all` and run on demand or periodically.
