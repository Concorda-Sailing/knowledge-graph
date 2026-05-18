# graphui

FastAPI + Jinja2 viewer for the knowledge-graph substrate. Reads
`depgraph` and `logigraph` data directly from disk (paths via env
vars) and renders:

- **Index** — coverage matrix per kind+tier, full node table with
  filter/sort.
- **Node detail** — dossier, applicable rules, direct + transitive
  dependents, commit history with model attribution, telemetry.
- **Rule detail** — statement, claims, references, telemetry.
- **Domain detail** — for entities and relationships. Relationships
  show a structured `from / predicate / to / mediated_by /
  cardinality / lifecycle` grid plus a **mediation-collision
  banner** when distinct relationships share storage (the design-
  defect signal logigraph regen flags).
- **Mobile-friendly** layout with horizontal-scroll wrappers around
  wide tables and an auto-collapsed sidebar.

Part of the knowledge-graph substrate. Install via:

```bash
git clone https://github.com/<owner>/knowledge-graph.git
cd knowledge-graph && ./install.sh
```

## Running

```bash
DEPGRAPH_DATA_DIR=/path/to/project/depgraph \
LOGIGRAPH_DATA_DIR=/path/to/project/logigraph \
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8081
```

Or register it as a systemd `--user` service via the kg installer.
Two flag styles are supported:

```bash
# Resolve from a project bundle (supports both the nested
# <project>/knowledge-graph/ and sibling-with-hyphen
# <project>-knowledge-graph/ layouts):
kg install systemd --project /path/to/project-knowledge-graph --apply

# Or set the data dirs explicitly (skips the bundle-layout resolver):
kg install systemd \
  --depgraph-data-dir /path/to/project/depgraph \
  --logigraph-data-dir /path/to/project/logigraph \
  --apply
```

## Environment

| Var | Required? | What |
|---|---|---|
| `DEPGRAPH_DATA_DIR` | required | Path to the project's depgraph data dir (the dir containing `project.toml` + `nodes/`). |
| `LOGIGRAPH_DATA_DIR` | required | Path to the project's logigraph data dir. |
| `DEPGRAPH_BIN` | optional (default: `<bundle>/depgraph/bin/depgraph`, where `<bundle>` is the tools dir) | Path to the depgraph CLI (invoked by the Approve button). |
| `LOGIGRAPH_BIN` | optional (default: `<bundle>/logigraph/bin/logigraph`) | Path to the logigraph CLI (invoked by the Approve button for rule / domain nodes). |

Graphui fails loud at startup if the required data-dir env vars are unset.
The systemd unit written by `kg install systemd --apply` sets all four.

## License

[MIT](./LICENSE). Copyright (c) 2026 Logan Greenlee.

The software is provided **AS IS**, without warranty of any kind,
express or implied, including but not limited to merchantability,
fitness for a particular purpose, and non-infringement. See the
LICENSE file for the full text.
