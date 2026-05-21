# Wild-corpus probe

The DISCOVERY mechanism for extractor bugs that synthetic
designed-to-pass fixtures miss. Per the `[[feedback-wild-means-real-repos]]`
note: synthetic fixtures anchor on a small known set you can game an
implementation to satisfy; real repos surface patterns nobody designed
a fixture for.

## Usage

```bash
# Run all targets
.venv/bin/python tools/wild-probe/probe.py

# Run one
.venv/bin/python tools/wild-probe/probe.py encode-databases

# Keep clones for investigation
.venv/bin/python tools/wild-probe/probe.py --keep-clones
```

Each run writes a JSON report to `tools/wild-probe/results/<timestamp>.json`
with per-target metrics (primitives, edges, edges-by-confidence,
validation-report). The probe also prints anomalies — patterns that
look suspect on real corpora (taxonomy collapse, high unresolved rate,
orphan edges, schema errors, missing edge kinds expected for the
language).

## Adding a target

Edit `targets.toml`. Each `[[target]]` entry needs:

- `name` — unique slug used as the repo key (avoid hyphens if the
  framework's slug helper trips on them, see #?? — TODO once filed)
- `url` — `https://github.com/<owner>/<repo>.git`
- `sha` — pinned commit; falls back to HEAD with an anomaly log if stale
- `language` — `python` or `typescript`
- `patterns` — informational list of what the target exercises
  (`sqlalchemy-orm`, `deep-barrel`, etc.)

## Curation criteria

- Small-to-moderate: under ~200 source files so the probe runs in
  <2 min per target. Large corpora belong in their own benchmark suite.
- MIT / Apache / BSD licensed. Verify before adding.
- Each target should exercise at least one pattern the synthetic
  fixtures don't fully cover — file a comment in the entry calling
  out what the target stresses.
- Pin shas; don't track `main`. Determinism over freshness — when a
  target's HEAD changes the probe should flag the diff explicitly, not
  silently chase upstream.

## Workflow when the probe surfaces a bug

1. **File a GH issue** describing the bug class (not the target — the
   target is the discovery vehicle, not the source of the bug).
2. **Add a synthetic pin fixture** under
   `depgraph/tests/extractors/fixtures/<lang>/` that exercises the
   minimal shape, with a regression test in the corresponding
   `test_<lang>_*.py`. Synthetic pins prevent regression once a real-repo
   bug is found.
3. **Fix the underlying defect.** Run the probe again to verify the
   anomaly is gone.
4. **Optionally** add a new target if a different repo would have
   surfaced the same bug class with a different shape.

The wild probe is the upstream signal; pin fixtures are the downstream
guard.
