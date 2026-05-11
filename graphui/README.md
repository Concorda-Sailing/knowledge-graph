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

Part of the [knowledge-graph](https://github.com/Concorda-Sailing/knowledge-graph)
substrate. Install via:

```bash
git clone https://github.com/Concorda-Sailing/knowledge-graph.git
cd knowledge-graph && ./install.sh
```

## Running

```bash
DEPGRAPH_DATA_DIR=/path/to/project/depgraph \
LOGIGRAPH_DATA_DIR=/path/to/project/logigraph \
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8081
```

Or register it as a systemd `--user` service via the umbrella's
installer:

```bash
~/tools/knowledge-graph/install.sh systemd --project /path/to/project --apply
```

## Environment

| Var | Default | What |
|---|---|---|
| `DEPGRAPH_DATA_DIR` | `~/concorda/depgraph` | Where depgraph nodes / dossiers / telemetry live. |
| `LOGIGRAPH_DATA_DIR` | `~/concorda/logigraph` | Where logigraph nodes / dossiers / telemetry live. |
| `DEPGRAPH_BIN` | `~/concorda/depgraph/bin/depgraph` | Path to the depgraph CLI (invoked by the Approve button). |

## License

[MIT](./LICENSE). Copyright (c) 2026 Logan Greenlee.

The software is provided **AS IS**, without warranty of any kind,
express or implied, including but not limited to merchantability,
fitness for a particular purpose, and non-infringement. See the
LICENSE file for the full text.
