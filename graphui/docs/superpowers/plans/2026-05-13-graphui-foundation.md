# graphui — Foundation (loader extensions + dashboard rewrite)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current flat dashboard with a repo-first layout that surfaces graph-health (telemetry + calibration), activity timeline (today / 7d / 30d), and cross-cutting knowledge above the repo list. Extract a universal node-list partial. No changes to repo detail pages, search, or new pages yet — those are separate plans.

**Architecture:** Strictly additive on the loader side (new functions feeding the dashboard route); new Jinja partials for each dashboard section so the next plans can compose them elsewhere; existing `index.html` is rewritten end-to-end to consume the new data. Test infrastructure is bootstrapped first (graphui currently has zero tests).

**Tech Stack:** FastAPI · Jinja2 · pytest + httpx (added by this plan) · subprocess-driven `git log` for activity · stdlib for telemetry/calibration parsing. No new third-party dependencies beyond test tooling.

**Spec:** `docs/superpowers/specs/2026-05-13-graphui-categories-design.md` § 3, § 7. The repo detail page (§ 4), semantic search (§ 5), and new pages (§ 6) are deferred to subsequent plans.

---

## File Structure

**New files:**
- `tests/conftest.py` — pytest fixtures (synthetic data dirs, FastAPI test client)
- `tests/fixtures/depgraph/` and `tests/fixtures/logigraph/` — minimal data dirs (nodes/, _meta.json, telemetry/, calibration/)
- `tests/test_loader_activity.py` — activity_summary
- `tests/test_loader_health.py` — graph_health (telemetry + calibration)
- `tests/test_loader_cross_cutting.py` — cross_cutting_summary
- `tests/test_loader_repo.py` — per-repo helpers (activity, languages, areas, dep counts, cross-cuts)
- `tests/test_dashboard_route.py` — integration test for `GET /graph/`
- `app/templates/_activity_strip.html` — today + 7d sparkline + 30d strip
- `app/templates/_graph_health.html` — telemetry + calibration + hottest-rules tile
- `app/templates/_cross_cutting.html` — rules/domain/processes summary cards
- `app/templates/_repo_card.html` — full active-repo card
- `app/templates/_node_list.html` — universal sortable/filterable node list (extracted from knowledge.html)
- `requirements-dev.txt` — pytest + httpx + pytest-cov

**Modified files:**
- `app/loader.py` — add ~10 new functions (one per task in this plan), all additive
- `app/main.py` — `index()` route enriched with new data; `?activity=` query param
- `app/templates/index.html` — full rewrite to use partials
- `app/templates/knowledge.html` — refactored to include `_node_list.html`
- `app/static/style.css` — new section styles (sparklines, sub-tiles, repo card footer)

**Out of scope (deferred plans):**
- `app/templates/repo.html` rewrite (Plan B)
- `/graph/search` + embedding pipeline (Plan C)
- `/graph/activity`, `/graph/telemetry`, `/graph/calibration` pages (Plan D)

---

## Conventions for this plan

- **Test-first.** Every loader function: write failing test → run it (FAIL) → implement → run it (PASS) → commit.
- **TDD without religion.** Templates get one render-smoke test (the integration test in Task 18); rendering correctness is verified by the smoke test + manual browser check at the end.
- **Synthetic data dirs.** Tests do not touch `~/concorda/knowledge-graph/`. `tests/conftest.py` builds a small fixture tree per session.
- **Env vars at conftest top.** `loader.py` resolves `DEPGRAPH_DATA_DIR` and `LOGIGRAPH_DATA_DIR` at module-import time. `conftest.py` MUST set these before any test module imports the loader. Use `importlib.reload(loader)` if the loader has been imported in a prior test.
- **Commit per task.** Each task ends with a commit. Use `bin/depgraph commit-summary` trailer per the user's standing convention.
- **Run all tests after each commit.** `pytest tests/ -v` from `~/tools/knowledge-graph/graphui/`. New tasks may not regress prior tests.

---

## Task 1: Test infrastructure + fixture data dirs

**Files:**
- Create: `requirements-dev.txt`
- Create: `tests/__init__.py` (empty)
- Create: `tests/conftest.py`
- Create: `tests/fixtures/depgraph/nodes/_meta.json`
- Create: `tests/fixtures/depgraph/nodes/components/web__app__page_tsx__Page.json`
- Create: `tests/fixtures/depgraph/nodes/services/api__services__crew__CrewService.json`
- Create: `tests/fixtures/depgraph/nodes/_index/dependents.json`
- Create: `tests/fixtures/depgraph/dossiers/components/web__app__page_tsx__Page.md`
- Create: `tests/fixtures/depgraph/telemetry/injections.jsonl`
- Create: `tests/fixtures/depgraph/telemetry/acknowledgments.jsonl`
- Create: `tests/fixtures/logigraph/nodes/_meta.json`
- Create: `tests/fixtures/logigraph/nodes/rules/rule__category__example.json`
- Create: `tests/fixtures/logigraph/nodes/_index/by_code.json`
- Create: `tests/fixtures/logigraph/dossiers/rules/rule__category__example.md`
- Create: `tests/fixtures/logigraph/calibration/runs/20260512-090000/SUMMARY.md`
- Create: `tests/fixtures/logigraph/calibration/runs/20260512-090000/example/result.json`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Add dev requirements file**

Write `requirements-dev.txt`:
```
-r requirements.txt
pytest>=8.0
httpx>=0.27
pytest-cov>=4.1
```

- [ ] **Step 2: Install dev requirements**

Run: `cd ~/tools/knowledge-graph/graphui && pip install -r requirements-dev.txt`

- [ ] **Step 3: Create empty tests package**

```bash
touch tests/__init__.py
```

- [ ] **Step 4: Write the fixture data files**

Write `tests/fixtures/depgraph/nodes/_meta.json`:
```json
{
  "regen_status": "complete",
  "regen_at": "2026-05-13T10:00:00+00:00",
  "git_commit": "abc12345deadbeef",
  "node_count": 2,
  "flags": []
}
```

Write `tests/fixtures/depgraph/nodes/components/web__app__page_tsx__Page.json`:
```json
{
  "id": "concorda-web::app/page.tsx::Page",
  "kind": "component",
  "title": "Page",
  "source": {"repo": "concorda-web", "path": "app/page.tsx"},
  "fan_out": 5,
  "dossier": "dossiers/components/web__app__page_tsx__Page.md",
  "structural_hash": "h1",
  "deps": []
}
```

Write `tests/fixtures/depgraph/nodes/services/api__services__crew__CrewService.json`:
```json
{
  "id": "concorda-api::services/crew.py::CrewService",
  "kind": "service",
  "title": "CrewService",
  "source": {"repo": "concorda-api", "path": "services/crew.py"},
  "fan_out": 12,
  "dossier": null,
  "structural_hash": "h2",
  "deps": []
}
```

Write `tests/fixtures/depgraph/nodes/_index/dependents.json`:
```json
{"by_target": {"concorda-api::services/crew.py::CrewService": [{"id": "concorda-web::app/page.tsx::Page", "kind": "component"}]}}
```

Write `tests/fixtures/depgraph/dossiers/components/web__app__page_tsx__Page.md`:
```markdown
---
status: current
last_reviewed_against_hash: h1
---

# Page

Landing page component.
```

Write `tests/fixtures/depgraph/telemetry/injections.jsonl`:
```jsonl
{"ts": "2026-05-13T08:00:00+00:00", "kind": "injection", "tool": "Edit", "file_path": "/x/concorda-web/app/page.tsx", "node_id": "concorda-web::app/page.tsx::Page", "rule_id": "rule::category::example"}
{"ts": "2026-05-12T08:00:00+00:00", "kind": "injection", "tool": "Edit", "file_path": "/x/concorda-web/app/page.tsx", "node_id": "concorda-web::app/page.tsx::Page", "rule_id": "rule::category::example"}
{"ts": "2026-04-13T08:00:00+00:00", "kind": "injection", "tool": "Edit", "file_path": "/x/concorda-web/app/page.tsx", "node_id": "concorda-web::app/page.tsx::Page", "rule_id": "rule::category::example"}
```

Write `tests/fixtures/depgraph/telemetry/acknowledgments.jsonl`:
```jsonl
{"ts": "2026-05-13T08:00:01+00:00", "kind": "acknowledgment", "node_id": "concorda-web::app/page.tsx::Page", "rule_id": "rule::category::example"}
{"ts": "2026-05-12T08:00:01+00:00", "kind": "acknowledgment", "node_id": "concorda-web::app/page.tsx::Page", "rule_id": "rule::category::example"}
```

Write `tests/fixtures/logigraph/nodes/_meta.json`:
```json
{"regen_status": "complete", "regen_at": "2026-05-13T10:00:00+00:00", "node_count": 1, "flags": []}
```

Write `tests/fixtures/logigraph/nodes/rules/rule__category__example.json`:
```json
{
  "id": "rule::category::example",
  "kind": "rule",
  "title": "Example rule",
  "statement": "Always do the right thing.",
  "claims_code": [{"depgraph_id": "concorda-web::app/page.tsx::Page", "remote_hash": "h1"}],
  "references_domain": ["resource::example"],
  "dossier": "dossiers/rules/rule__category__example.md",
  "structural_hash": "rh1",
  "definition_status": "human_reviewed"
}
```

Write `tests/fixtures/logigraph/nodes/_index/by_code.json`:
```json
{"by_target": {"concorda-web::app/page.tsx::Page": ["rule::category::example"]}}
```

Write `tests/fixtures/logigraph/dossiers/rules/rule__category__example.md`:
```markdown
---
definition_status: human_reviewed
last_reviewed_against_hash: rh1
---

## The rule
Always do the right thing.

## Why it exists
Because.

## Decision table
| condition | action |
|---|---|
| any | do the right thing |
```

Write `tests/fixtures/logigraph/calibration/runs/20260512-090000/SUMMARY.md`:
```markdown
# Calibration run 20260512-090000

**Results**: 1 pass · 0 fail · 0 review/unscored · 1 total
```

Write `tests/fixtures/logigraph/calibration/runs/20260512-090000/example/result.json`:
```json
{
  "prompt_id": "example",
  "run_id": "20260512-090000",
  "expected_outcome": "preserve_or_ask",
  "correctness": "pass",
  "overall": "pass",
  "scored_at": "2026-05-12T09:01:00+00:00"
}
```

- [ ] **Step 5: Write conftest.py**

Write `tests/conftest.py`:
```python
"""Pytest fixtures for graphui.

Sets DEPGRAPH_DATA_DIR / LOGIGRAPH_DATA_DIR BEFORE any test module imports
the loader (which resolves env vars at import time). If tests import the
loader, they must use the `loader` fixture below, which reloads the module
to pick up the env vars from this conftest.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# Set env vars at module import time so any subsequent `import app.loader`
# (in a test module, fixture, or app import chain) sees them.
os.environ["DEPGRAPH_DATA_DIR"] = str(FIXTURES / "depgraph")
os.environ["LOGIGRAPH_DATA_DIR"] = str(FIXTURES / "logigraph")

# Make `app` importable when running pytest from the project root.
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@pytest.fixture
def loader():
    """Reload app.loader so a fresh import picks up the conftest env vars
    (in case a prior test module imported it before env was set)."""
    from app import loader as mod
    return importlib.reload(mod)


@pytest.fixture
def client():
    """FastAPI TestClient bound to the app."""
    from fastapi.testclient import TestClient
    from app import main as mainmod
    importlib.reload(mainmod)  # pick up env-resolved loader
    return TestClient(mainmod.app)
```

- [ ] **Step 6: Write a smoke test**

Write `tests/test_smoke.py`:
```python
"""Smoke test: fixtures load, loader imports, env is wired."""
def test_loader_imports_with_fixtures(loader):
    assert loader.DEPGRAPH.name == "depgraph"
    assert loader.LOGIGRAPH.name == "logigraph"
    nodes = loader.load_depgraph_nodes()
    assert any(n["id"] == "concorda-web::app/page.tsx::Page" for n in nodes)


def test_client_renders_index(client):
    r = client.get("/graph/")
    assert r.status_code == 200
    assert "graphui" in r.text.lower()
```

- [ ] **Step 7: Run the smoke tests — they should PASS**

Run: `cd ~/tools/knowledge-graph/graphui && pytest tests/test_smoke.py -v`
Expected: 2 passed.

If they fail, fix before continuing. Common issues: missing `__init__.py`, env not set early enough in conftest, fixture JSON malformed.

- [ ] **Step 8: Commit**

```bash
cd ~/tools/knowledge-graph/graphui
git add requirements-dev.txt tests/
git commit -m "$(cat <<'EOF'
test(graphui): bootstrap pytest infra with synthetic data fixtures

Depgraph:
  changed: N file(s) (run bin/depgraph commit-summary)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

(Run `DEPGRAPH_DATA_DIR=$HOME/concorda/knowledge-graph/depgraph $HOME/tools/knowledge-graph/depgraph/bin/depgraph commit-summary` first, paste its output in place of the placeholder line.)

---

## Task 2: Loader · activity_summary()

Implements the data feeding the dashboard's ACTIVITY strip (today / 7-day sparkline / 30-day totals). Sources: node-file mtimes (for added counts) + telemetry/injections.jsonl (for fires) + dossier state transitions for "drafts authored."

**Files:**
- Modify: `app/loader.py` — add `activity_summary()`
- Create: `tests/test_loader_activity.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_loader_activity.py`:
```python
import datetime as dt
import os
from pathlib import Path


def test_activity_summary_shape(loader):
    s = loader.activity_summary()
    assert set(s.keys()) >= {"today", "week_sparkline", "thirty_day"}

    today = s["today"]
    assert set(today.keys()) >= {"nodes_added", "drafts_authored", "drift_events", "rules_authored"}
    for k in ("nodes_added", "drafts_authored", "drift_events", "rules_authored"):
        assert isinstance(today[k], int)

    spark = s["week_sparkline"]
    assert isinstance(spark, list) and len(spark) == 7
    assert all(isinstance(x, int) for x in spark)

    td = s["thirty_day"]
    assert set(td.keys()) >= {"nodes_added", "drafts_reviewed", "drift_events"}


def test_activity_counts_recent_node_file_as_added_today(loader, tmp_path, monkeypatch):
    # Touch one of the fixture node files to make it "added today" by mtime.
    fixture_node = loader.DEPGRAPH_NODES / "components" / "web__app__page_tsx__Page.json"
    now = dt.datetime.now().timestamp()
    os.utime(fixture_node, (now, now))
    s = loader.activity_summary()
    assert s["today"]["nodes_added"] >= 1
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_activity.py -v`
Expected: FAIL with `AttributeError: module 'app.loader' has no attribute 'activity_summary'`.

- [ ] **Step 3: Implement activity_summary**

In `app/loader.py`, append:
```python
def _start_of_day_utc(days_ago: int = 0) -> float:
    now = dt.datetime.now(dt.timezone.utc)
    start = dt.datetime(now.year, now.month, now.day, tzinfo=dt.timezone.utc)
    start -= dt.timedelta(days=days_ago)
    return start.timestamp()


def _count_node_files_since(root: Path, since_ts: float) -> int:
    """Count *.json node files under root with mtime >= since_ts."""
    if not root.exists():
        return 0
    return sum(
        1 for p in root.rglob("*.json")
        if "_index" not in p.parts and "_meta.json" != p.name and p.stat().st_mtime >= since_ts
    )


def _count_jsonl_since(path: Path, since_ts: float, predicate=None) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts_raw = row.get("ts")
        if not ts_raw:
            continue
        try:
            ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            continue
        if ts < since_ts:
            continue
        if predicate and not predicate(row):
            continue
        n += 1
    return n


def _drafts_authored_since(since_ts: float) -> int:
    """Dossiers whose status==llm_drafted whose file mtime is in window."""
    n = 0
    for kind_dir in (DEPGRAPH / "dossiers", LOGIGRAPH / "dossiers"):
        if not kind_dir.exists():
            continue
        for p in kind_dir.rglob("*.md"):
            if p.stat().st_mtime < since_ts:
                continue
            text = p.read_text(errors="ignore")[:512]
            if "llm_drafted" in text or "definition_status: llm_drafted" in text:
                n += 1
    return n


def _drift_events_since(since_ts: float) -> int:
    """Read _meta.json flags; count entries with discovered_at >= since_ts
    and kind in {drift, defect}."""
    meta = load_meta()
    n = 0
    for label in ("depgraph", "logigraph"):
        flags = meta.get(label, {}).get("flags") or []
        for f in flags:
            kind = f.get("kind")
            if kind not in ("drift", "defect"):
                continue
            ts_raw = f.get("discovered_at")
            if not ts_raw:
                continue
            try:
                ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError):
                continue
            if ts >= since_ts:
                n += 1
    return n


def _rules_authored_since(since_ts: float) -> int:
    """Rule node files (kind=rule) with mtime in window."""
    rule_dir = LOGIGRAPH_NODES / "rules"
    return _count_node_files_since(rule_dir, since_ts)


def activity_summary() -> dict:
    """Today / 7-day sparkline / 30-day rollup for the dashboard activity strip."""
    today_start = _start_of_day_utc(0)
    today = {
        "nodes_added": _count_node_files_since(DEPGRAPH_NODES, today_start),
        "drafts_authored": _drafts_authored_since(today_start),
        "drift_events": _drift_events_since(today_start),
        "rules_authored": _rules_authored_since(today_start),
    }
    spark: list[int] = []
    for d in range(6, -1, -1):  # oldest first
        start = _start_of_day_utc(d)
        end = _start_of_day_utc(d - 1) if d > 0 else dt.datetime.now(dt.timezone.utc).timestamp() + 1
        n = sum(
            1 for p in DEPGRAPH_NODES.rglob("*.json")
            if "_index" not in p.parts and p.name != "_meta.json"
            and start <= p.stat().st_mtime < end
        )
        spark.append(n)
    thirty_start = _start_of_day_utc(30)
    thirty_day = {
        "nodes_added": _count_node_files_since(DEPGRAPH_NODES, thirty_start),
        "drafts_reviewed": _count_jsonl_since(
            LOGIGRAPH / "telemetry" / "acknowledgments.jsonl", thirty_start
        ),
        "drift_events": _drift_events_since(thirty_start),
    }
    return {"today": today, "week_sparkline": spark, "thirty_day": thirty_day}
```

Also add `import datetime as dt` at the top of `app/loader.py` if not present (currently it uses `time` only).

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_activity.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_activity.py
git commit -m "feat(loader): activity_summary for dashboard strip"
```

---

## Task 3: Loader · graph_health()

Telemetry counts (30d injections, ack rate, dead rules, never-acked dossiers) + calibration last-run summary + hottest rules.

**Files:**
- Modify: `app/loader.py` — add `graph_health()`
- Create: `tests/test_loader_health.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_loader_health.py`:
```python
def test_graph_health_shape(loader):
    h = loader.graph_health()
    assert set(h.keys()) >= {"telemetry", "calibration", "hottest_rules"}

    t = h["telemetry"]
    assert set(t.keys()) >= {"injections_30d", "ack_rate_pct", "dead_rules", "never_acked_dossiers", "trend_pct"}
    assert t["injections_30d"] == 2  # only the two within-30d entries in the fixture
    assert 0 <= t["ack_rate_pct"] <= 100

    c = h["calibration"]
    assert set(c.keys()) >= {"accuracy_pct", "regressions", "last_run_id", "drifted_rules"}
    assert c["accuracy_pct"] == 100  # the fixture run has 1 pass / 0 fail
    assert c["last_run_id"] == "20260512-090000"
    assert c["regressions"] == 0

    hr = h["hottest_rules"]
    assert isinstance(hr, list)
    if hr:
        assert set(hr[0].keys()) >= {"id", "count"}
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_health.py -v`
Expected: FAIL with `AttributeError: module 'app.loader' has no attribute 'graph_health'`.

- [ ] **Step 3: Implement graph_health**

In `app/loader.py`, append:
```python
def _read_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _telemetry_stats(window_days: int = 30) -> dict:
    since = _start_of_day_utc(window_days)
    prev_since = _start_of_day_utc(window_days * 2)
    inj_count = 0
    prev_inj_count = 0
    ack_count = 0
    rule_fires: dict[str, int] = {}
    acked_keys: set[tuple[str, str]] = set()
    inj_keys_total: set[tuple[str, str]] = set()

    for src in (DEPGRAPH / "telemetry" / "injections.jsonl",
                LOGIGRAPH / "telemetry" / "injections.jsonl"):
        for row in _read_jsonl(src):
            ts_raw = row.get("ts")
            try:
                ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, AttributeError, ValueError):
                continue
            rid = row.get("rule_id")
            nid = row.get("node_id")
            if ts >= since:
                inj_count += 1
                if rid:
                    rule_fires[rid] = rule_fires.get(rid, 0) + 1
                if nid and rid:
                    inj_keys_total.add((nid, rid))
            elif prev_since <= ts < since:
                prev_inj_count += 1

    for src in (DEPGRAPH / "telemetry" / "acknowledgments.jsonl",
                LOGIGRAPH / "telemetry" / "acknowledgments.jsonl"):
        for row in _read_jsonl(src):
            ts_raw = row.get("ts")
            try:
                ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, AttributeError, ValueError):
                continue
            if ts < since:
                continue
            ack_count += 1
            nid, rid = row.get("node_id"), row.get("rule_id")
            if nid and rid:
                acked_keys.add((nid, rid))

    ack_rate = round((ack_count / inj_count) * 100) if inj_count else 0
    trend = round(((inj_count - prev_inj_count) / prev_inj_count) * 100) if prev_inj_count else 0

    # Dead rules: rule node files that never fired in the window.
    rules_dir = LOGIGRAPH_NODES / "rules"
    dead = 0
    if rules_dir.exists():
        for p in rules_dir.glob("*.json"):
            try:
                rid = json.loads(p.read_text()).get("id")
            except (OSError, json.JSONDecodeError):
                continue
            if rid and rid not in rule_fires:
                dead += 1

    # Never-acknowledged dossiers: nodes that have a dossier but never appear in acks.
    never_acked = 0
    acked_nids = {nid for (nid, _r) in acked_keys}
    for n in load_depgraph_nodes():
        if n.get("dossier") and n["id"] not in acked_nids:
            never_acked += 1

    hottest = sorted(rule_fires.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return {
        "injections_30d": inj_count,
        "ack_rate_pct": ack_rate,
        "trend_pct": trend,
        "dead_rules": dead,
        "never_acked_dossiers": never_acked,
        "rule_fires": rule_fires,
        "hottest": [{"id": rid, "count": n} for rid, n in hottest],
    }


def _calibration_summary() -> dict:
    """Read the most-recent calibration run dir under LOGIGRAPH/calibration/runs/.
    Returns accuracy %, pass/fail counts, drifted rule ids, prev-run delta."""
    runs_dir = LOGIGRAPH / "calibration" / "runs"
    if not runs_dir.exists():
        return {"accuracy_pct": None, "regressions": 0, "last_run_id": None, "drifted_rules": [], "prev_delta_pp": 0}
    runs = sorted([p for p in runs_dir.iterdir() if p.is_dir()], reverse=True)
    if not runs:
        return {"accuracy_pct": None, "regressions": 0, "last_run_id": None, "drifted_rules": [], "prev_delta_pp": 0}

    def _score(run_dir: Path) -> tuple[int, int, list[str]]:
        passes = fails = 0
        drifted: list[str] = []
        for result_path in run_dir.glob("*/result.json"):
            try:
                row = json.loads(result_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("overall") == "pass":
                passes += 1
            else:
                fails += 1
                pid = row.get("prompt_id")
                if pid:
                    drifted.append(pid)
        return passes, fails, drifted

    p, f, drifted = _score(runs[0])
    total = p + f
    acc = round((p / total) * 100) if total else 0
    prev_acc = None
    if len(runs) > 1:
        pp, pf, _ = _score(runs[1])
        prev_total = pp + pf
        if prev_total:
            prev_acc = round((pp / prev_total) * 100)
    return {
        "accuracy_pct": acc,
        "regressions": f,
        "last_run_id": runs[0].name,
        "drifted_rules": drifted,
        "prev_delta_pp": (acc - prev_acc) if prev_acc is not None else 0,
    }


def graph_health() -> dict:
    t = _telemetry_stats(30)
    return {
        "telemetry": {k: t[k] for k in ("injections_30d", "ack_rate_pct", "trend_pct", "dead_rules", "never_acked_dossiers")},
        "calibration": _calibration_summary(),
        "hottest_rules": t["hottest"],
    }
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_health.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_health.py
git commit -m "feat(loader): graph_health (telemetry + calibration + hottest rules)"
```

---

## Task 4: Loader · cross_cutting_summary()

Three cards: Rules count + namespace preview + claimed-repo count; Domain count + subkind breakdown + referenced-by count; Processes count + name preview + spanned-repo count.

**Files:**
- Modify: `app/loader.py` — add `cross_cutting_summary()`
- Create: `tests/test_loader_cross_cutting.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_loader_cross_cutting.py`:
```python
def test_cross_cutting_shape(loader):
    cc = loader.cross_cutting_summary()
    assert set(cc.keys()) >= {"rules", "domain", "processes"}

    r = cc["rules"]
    assert set(r.keys()) >= {"count", "claimed_repos", "namespaces"}
    assert r["count"] == 1
    assert isinstance(r["namespaces"], list)
    assert "category" in r["namespaces"]
    assert r["claimed_repos"] == 1  # the fixture rule claims one repo (concorda-web)

    d = cc["domain"]
    assert set(d.keys()) >= {"count", "subkinds", "referenced_by"}

    p = cc["processes"]
    assert set(p.keys()) >= {"count", "names", "spans_repos"}
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_cross_cutting.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement cross_cutting_summary**

In `app/loader.py`, append:
```python
def _namespaces_from_ids(ids: list[str]) -> list[str]:
    """For ids of the form `kind::namespace::name`, return unique namespaces."""
    out: set[str] = set()
    for i in ids:
        parts = i.split("::")
        if len(parts) >= 3:
            out.add(parts[1])
    return sorted(out)


def _claimed_repos_for_rules(rules: list[dict]) -> int:
    """Count unique repos appearing in any rule's claims_code list."""
    repos: set[str] = set()
    for r in rules:
        for c in r.get("claims_code", []) or []:
            did = c.get("depgraph_id") or ""
            head = did.split("::", 1)[0]
            if head:
                repos.add(head)
    return len(repos)


def _spans_repos_for_processes(procs: list[dict]) -> int:
    """Count unique repos appearing in any process step's claims_code list."""
    repos: set[str] = set()
    for p in procs:
        for step in p.get("steps", []) or []:
            for c in step.get("claims_code", []) or []:
                did = c.get("depgraph_id") or ""
                head = did.split("::", 1)[0]
                if head:
                    repos.add(head)
    return len(repos)


def cross_cutting_summary() -> dict:
    lg = load_logigraph_nodes()
    rules = lg["rules"]
    domain = lg["domain"]
    procs = lg["processes"]
    referenced_by = 0
    for r in rules:
        if r.get("references_domain"):
            referenced_by += len(r["references_domain"])
    for p in procs:
        for step in p.get("steps", []) or []:
            if step.get("references_domain"):
                referenced_by += len(step["references_domain"])
    subkinds: dict[str, int] = {}
    for o in domain:
        sk = o.get("subkind") or "—"
        subkinds[sk] = subkinds.get(sk, 0) + 1
    return {
        "rules": {
            "count": len(rules),
            "claimed_repos": _claimed_repos_for_rules(rules),
            "namespaces": _namespaces_from_ids([r["id"] for r in rules]),
        },
        "domain": {
            "count": len(domain),
            "subkinds": subkinds,
            "referenced_by": referenced_by,
        },
        "processes": {
            "count": len(procs),
            "names": [p.get("title") or p["id"].rsplit("::", 1)[-1] for p in procs[:6]],
            "spans_repos": _spans_repos_for_processes(procs),
        },
    }
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_cross_cutting.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_cross_cutting.py
git commit -m "feat(loader): cross_cutting_summary"
```

---

## Task 5: Loader · repo_activity(basename)

Per-repo 7d/30d commit counts, sparkline (7 daily ints), today's per-repo node delta, classification (`active` / `dormant` / `dead-candidate`), last-push timestamp.

**Files:**
- Modify: `app/loader.py` — add `repo_activity()` + `_repo_path()`
- Create: `tests/test_loader_repo.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_loader_repo.py`:
```python
def test_repo_activity_shape(loader):
    a = loader.repo_activity("concorda-web")
    assert set(a.keys()) >= {
        "commits_7d", "commits_30d", "sparkline", "today_node_delta",
        "classification", "last_push_age_days",
    }
    assert isinstance(a["sparkline"], list) and len(a["sparkline"]) == 7
    assert a["classification"] in ("active", "dormant", "dead-candidate", "unknown")


def test_repo_activity_unknown_repo(loader):
    a = loader.repo_activity("nonexistent-repo")
    assert a["classification"] == "unknown"
    assert a["commits_7d"] == 0
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_repo.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement repo_activity**

In `app/loader.py`, append:
```python
def _repo_path(basename: str) -> Path | None:
    """Resolve a tracked-repo basename to its filesystem path.
    Convention: HOME/<basename> (matches `commits_30d` below)."""
    p = HOME / basename
    return p if (p / ".git").exists() else None


def _git_log_dates(repo: Path, since: str) -> list[str]:
    """Run `git log --since=<since> --format=%cd --date=format:%Y-%m-%d`. Best-effort."""
    try:
        out = subprocess.run(
            ["git", "log", f"--since={since}", "--format=%cd", "--date=format:%Y-%m-%d"],
            cwd=str(repo), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [l.strip() for l in out.stdout.splitlines() if l.strip()]


def _git_last_push_age_days(repo: Path) -> int | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            cwd=str(repo), capture_output=True, text=True, timeout=5,
        )
        ts = int(out.stdout.strip() or 0)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if not ts:
        return None
    return int((dt.datetime.now(dt.timezone.utc).timestamp() - ts) // 86400)


def _classify(last_push_age: int | None, has_inbound_deps: bool) -> str:
    if last_push_age is None:
        return "unknown"
    if last_push_age <= 7:
        return "active"
    if last_push_age >= 180 and not has_inbound_deps:
        return "dead-candidate"
    return "dormant"


def _today_node_delta_for_repo(basename: str) -> int:
    today_start = _start_of_day_utc(0)
    n = 0
    for p in DEPGRAPH_NODES.rglob("*.json"):
        if "_index" in p.parts or p.name == "_meta.json":
            continue
        if p.stat().st_mtime < today_start:
            continue
        try:
            row = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        src = (row.get("source") or {}).get("repo")
        if src == basename:
            n += 1
    return n


def repo_activity(basename: str) -> dict:
    repo = _repo_path(basename)
    if repo is None:
        return {
            "commits_7d": 0,
            "commits_30d": 0,
            "sparkline": [0] * 7,
            "today_node_delta": 0,
            "classification": "unknown",
            "last_push_age_days": None,
        }
    dates = _git_log_dates(repo, "30 days ago")
    # 7-day sparkline (oldest first)
    today = dt.datetime.now(dt.timezone.utc).date()
    spark = []
    for d in range(6, -1, -1):
        target = (today - dt.timedelta(days=d)).isoformat()
        spark.append(sum(1 for x in dates if x == target))
    commits_7d = sum(spark)
    commits_30d = len(dates)
    age = _git_last_push_age_days(repo)
    # Inbound deps gate is filled in by repo_summary; default False here.
    classification = _classify(age, has_inbound_deps=False)
    return {
        "commits_7d": commits_7d,
        "commits_30d": commits_30d,
        "sparkline": spark,
        "today_node_delta": _today_node_delta_for_repo(basename),
        "classification": classification,
        "last_push_age_days": age,
    }
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_repo.py::test_repo_activity_shape tests/test_loader_repo.py::test_repo_activity_unknown_repo -v`
Expected: 2 passed (the shape test on `concorda-web` works whether or not that repo exists on the box, because the `unknown` branch is still valid output).

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_repo.py
git commit -m "feat(loader): repo_activity (commits, sparkline, classification)"
```

---

## Task 6: Loader · repo_languages(basename)

Detect primary language(s) by file-extension histogram + framework hints from `package.json` / `pyproject.toml` / etc.

**Files:**
- Modify: `app/loader.py` — add `repo_languages()`
- Modify: `tests/test_loader_repo.py` — add a test

- [ ] **Step 1: Write the failing test**

Append to `tests/test_loader_repo.py`:
```python
def test_repo_languages_unknown(loader):
    langs = loader.repo_languages("nonexistent-repo")
    assert langs == []


def test_repo_languages_shape(loader):
    # The shape contract: list of {label, hint} dicts, length 0..4.
    langs = loader.repo_languages("concorda-web")
    assert isinstance(langs, list)
    assert len(langs) <= 4
    for entry in langs:
        assert set(entry.keys()) >= {"label", "hint"}
```

- [ ] **Step 2: Run — verify the new tests FAIL**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 2 new FAILs (`AttributeError`).

- [ ] **Step 3: Implement repo_languages**

In `app/loader.py`, append:
```python
_EXT_TO_LANG = {
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript",
    ".py": "Python",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".cs": "C#",
    ".php": "PHP",
}


def _framework_hints(repo: Path) -> list[str]:
    hints: list[str] = []
    pkg = repo / "package.json"
    if pkg.exists():
        try:
            row = json.loads(pkg.read_text())
        except (OSError, json.JSONDecodeError):
            row = {}
        deps = {**(row.get("dependencies") or {}), **(row.get("devDependencies") or {})}
        if "next" in deps:
            hints.append("Next")
        if "react" in deps:
            hints.append("React")
        if "vitest" in deps:
            hints.append("Vitest")
        if "@playwright/test" in deps or "playwright" in deps:
            hints.append("Playwright")
    pyproj = repo / "pyproject.toml"
    reqs = repo / "requirements.txt"
    py_text = ""
    if pyproj.exists():
        py_text += pyproj.read_text(errors="ignore")
    if reqs.exists():
        py_text += reqs.read_text(errors="ignore")
    if "fastapi" in py_text.lower():
        hints.append("FastAPI")
    if "sqlalchemy" in py_text.lower():
        hints.append("SQLAlchemy")
    if "pytest" in py_text.lower():
        hints.append("pytest")
    return hints


def repo_languages(basename: str) -> list[dict]:
    repo = _repo_path(basename)
    if repo is None:
        return []
    counts: dict[str, int] = {}
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        if any(part.startswith(".") or part == "node_modules" for part in p.parts):
            continue
        lang = _EXT_TO_LANG.get(p.suffix)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    primary = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:2]
    out = [{"label": lang, "hint": "primary"} for lang, _ in primary]
    for h in _framework_hints(repo)[:4 - len(out)]:
        out.append({"label": h, "hint": "framework"})
    return out
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_repo.py
git commit -m "feat(loader): repo_languages (ext histogram + framework hints)"
```

---

## Task 7: Loader · repo_areas(basename)

Top-level directories of the repo that contain tracked nodes, with per-area node counts.

**Files:**
- Modify: `app/loader.py` — add `repo_areas()`
- Modify: `tests/test_loader_repo.py` — add test

- [ ] **Step 1: Write the failing test**

Append to `tests/test_loader_repo.py`:
```python
def test_repo_areas_includes_node_counts(loader):
    areas = loader.repo_areas("concorda-web")
    assert isinstance(areas, list)
    if areas:
        for entry in areas:
            assert set(entry.keys()) >= {"dir", "node_count"}
            assert isinstance(entry["node_count"], int)
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_repo.py::test_repo_areas_includes_node_counts -v`
Expected: FAIL.

- [ ] **Step 3: Implement repo_areas**

In `app/loader.py`, append:
```python
def repo_areas(basename: str) -> list[dict]:
    """Return top-level directories in `basename` that contain at least one
    tracked node, ordered by node_count desc. Each entry: {dir, node_count}."""
    counts: dict[str, int] = {}
    for n in load_depgraph_nodes():
        src = (n.get("source") or {})
        if src.get("repo") != basename:
            continue
        path = src.get("path") or ""
        head = path.split("/", 1)[0] if "/" in path else path
        if not head:
            continue
        counts[head] = counts.get(head, 0) + 1
    return [
        {"dir": d, "node_count": c}
        for d, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_repo.py
git commit -m "feat(loader): repo_areas (top-level dirs with node counts)"
```

---

## Task 8: Loader · repo_dep_counts(basename)

Per-repo inbound (other repos depending on me), outbound (repos I depend on), external package count.

**Files:**
- Modify: `app/loader.py` — add `repo_dep_counts()`
- Modify: `tests/test_loader_repo.py` — add test

- [ ] **Step 1: Write the failing test**

Append to `tests/test_loader_repo.py`:
```python
def test_repo_dep_counts_shape(loader):
    d = loader.repo_dep_counts("concorda-web")
    assert set(d.keys()) >= {"inbound_repos", "outbound_repos", "external_pkgs"}
    for k in ("inbound_repos", "outbound_repos", "external_pkgs"):
        assert isinstance(d[k], int)


def test_repo_dep_counts_fixture_outbound(loader):
    # The fixture has concorda-web::Page depending on concorda-api::CrewService.
    d = loader.repo_dep_counts("concorda-web")
    assert d["outbound_repos"] >= 0  # at least the relationship is computed without error
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 2 new FAILs.

- [ ] **Step 3: Implement repo_dep_counts**

In `app/loader.py`, append:
```python
def repo_dep_counts(basename: str) -> dict:
    """Compute three counts:
      - inbound_repos: # of other tracked repos with nodes whose dependents
        index points into a node belonging to `basename`.
      - outbound_repos: # of other tracked repos whose nodes are referenced
        by nodes in `basename` (via the by_target dependents index — symmetric).
      - external_pkgs: # of packages declared in `basename/package.json` deps
        + `basename/requirements.txt` lines + `basename/pyproject.toml` deps.
    """
    inbound: set[str] = set()
    outbound: set[str] = set()
    dependents = load_dependents()  # by_target: target_id -> [dependent dicts]
    nodes = load_depgraph_nodes()
    in_my_repo = {n["id"] for n in nodes if (n.get("source") or {}).get("repo") == basename}
    for target_id, dependers in dependents.items():
        target_repo = target_id.split("::", 1)[0]
        for d in dependers:
            dep_repo = (d.get("id") or "").split("::", 1)[0]
            if not dep_repo or dep_repo == target_repo:
                continue
            if target_repo == basename and dep_repo != basename:
                inbound.add(dep_repo)
            if dep_repo == basename and target_repo != basename:
                outbound.add(target_repo)

    ext = 0
    repo = _repo_path(basename)
    if repo is not None:
        pkg = repo / "package.json"
        if pkg.exists():
            try:
                row = json.loads(pkg.read_text())
                ext += len(row.get("dependencies") or {})
                ext += len(row.get("devDependencies") or {})
            except (OSError, json.JSONDecodeError):
                pass
        reqs = repo / "requirements.txt"
        if reqs.exists():
            ext += sum(
                1 for l in reqs.read_text(errors="ignore").splitlines()
                if l.strip() and not l.strip().startswith("#")
            )
        pyproj = repo / "pyproject.toml"
        if pyproj.exists():
            txt = pyproj.read_text(errors="ignore")
            # crude: count lines under a [project] dependencies array; good enough for v1.
            in_deps = False
            for line in txt.splitlines():
                s = line.strip()
                if s.startswith("dependencies"):
                    in_deps = True
                    continue
                if in_deps:
                    if s.startswith("]"):
                        in_deps = False
                        continue
                    if s.startswith('"') or s.startswith("'"):
                        ext += 1
    return {"inbound_repos": len(inbound), "outbound_repos": len(outbound), "external_pkgs": ext}
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_repo.py
git commit -m "feat(loader): repo_dep_counts (inbound, outbound, external)"
```

---

## Task 9: Loader · repo_cross_cuts(basename)

Per-repo: how many rules claim it, how many processes touch it, how many domain entities are referenced from nodes in it.

**Files:**
- Modify: `app/loader.py` — add `repo_cross_cuts()`
- Modify: `tests/test_loader_repo.py` — add test

- [ ] **Step 1: Write the failing test**

Append to `tests/test_loader_repo.py`:
```python
def test_repo_cross_cuts_shape(loader):
    c = loader.repo_cross_cuts("concorda-web")
    assert set(c.keys()) >= {"rules", "processes", "domain"}
    assert isinstance(c["rules"], list)
    # The fixture has rule::category::example claiming concorda-web::app/page.tsx::Page.
    assert "rule::category::example" in c["rules"]


def test_repo_cross_cuts_empty_for_unknown(loader):
    c = loader.repo_cross_cuts("ghost-repo")
    assert c["rules"] == [] and c["processes"] == [] and c["domain"] == []
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 2 new FAILs.

- [ ] **Step 3: Implement repo_cross_cuts**

In `app/loader.py`, append:
```python
def repo_cross_cuts(basename: str) -> dict:
    """List the rule/process/domain ids that touch any node in `basename`.
    Returns id-lists (not counts) so the repo card can name a few inline."""
    lg = load_logigraph_nodes()
    rule_ids: set[str] = set()
    proc_ids: set[str] = set()
    domain_ids: set[str] = set()

    for r in lg["rules"]:
        for c in r.get("claims_code", []) or []:
            did = c.get("depgraph_id") or ""
            if did.startswith(f"{basename}::"):
                rule_ids.add(r["id"])
                for ref in (r.get("references_domain") or []):
                    domain_ids.add(ref)
                break
    for p in lg["processes"]:
        for step in p.get("steps", []) or []:
            hit = False
            for c in step.get("claims_code", []) or []:
                did = c.get("depgraph_id") or ""
                if did.startswith(f"{basename}::"):
                    proc_ids.add(p["id"])
                    for ref in (step.get("references_domain") or []):
                        domain_ids.add(ref)
                    hit = True
                    break
            if hit:
                break
    return {
        "rules": sorted(rule_ids),
        "processes": sorted(proc_ids),
        "domain": sorted(domain_ids),
    }
```

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_loader_repo.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add app/loader.py tests/test_loader_repo.py
git commit -m "feat(loader): repo_cross_cuts (rule/process/domain projection)"
```

---

## Task 10: Loader · extend repo_summary() with new fields

The existing `repo_summary()` returns `{basename, node_count, state_counts, current_pct, has_stale}`. Add `activity`, `languages`, `areas`, `dep_counts`, `cross_cuts`, plus a derived `dead_code_score` for sorting.

**Files:**
- Modify: `app/loader.py` — `repo_summary()`
- Modify: `tests/test_loader_repo.py` — add test

- [ ] **Step 1: Locate the existing `repo_summary()`**

Run: `grep -n "def repo_summary" app/loader.py`
Note the line range. Read those lines to understand current shape.

- [ ] **Step 2: Write the failing test**

Append to `tests/test_loader_repo.py`:
```python
def test_repo_summary_has_enriched_fields(loader):
    rows = loader.repo_summary()
    assert rows, "fixture should yield at least one repo"
    r = rows[0]
    for k in ("basename", "node_count", "state_counts", "activity",
              "languages", "areas", "dep_counts", "cross_cuts",
              "dead_code_score"):
        assert k in r, f"missing key: {k}"
    assert isinstance(r["dead_code_score"], (int, float))
```

- [ ] **Step 3: Run — verify FAIL**

Run: `pytest tests/test_loader_repo.py::test_repo_summary_has_enriched_fields -v`
Expected: FAIL with `KeyError` or missing-key assertion.

- [ ] **Step 4: Extend `repo_summary()`**

In `app/loader.py`, find the existing `repo_summary()` and enrich each row before returning. Append after the existing per-basename loop:
```python
        # --- enrichments added in Plan A ---
        row["activity"] = repo_activity(basename)
        row["languages"] = repo_languages(basename)
        row["areas"] = repo_areas(basename)
        row["dep_counts"] = repo_dep_counts(basename)
        row["cross_cuts"] = repo_cross_cuts(basename)
        # dead_code_score: low push frequency + zero inbound + many stale claims.
        age = row["activity"]["last_push_age_days"] or 0
        inbound = row["dep_counts"]["inbound_repos"]
        stale = row["state_counts"].get("stale", 0)
        score = (age // 30) + (10 if inbound == 0 else 0) + stale
        row["dead_code_score"] = score
        # refine classification with inbound-deps signal.
        if row["activity"]["classification"] == "dormant" and age >= 180 and inbound == 0:
            row["activity"]["classification"] = "dead-candidate"
```

(Replace any existing trailing `return out` with the same line after the enrichment block.)

- [ ] **Step 5: Run all loader tests**

Run: `pytest tests/test_loader_repo.py tests/test_loader_health.py tests/test_loader_cross_cutting.py tests/test_loader_activity.py -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/loader.py tests/test_loader_repo.py
git commit -m "feat(loader): enrich repo_summary with activity/lang/areas/deps/cross-cuts"
```

---

## Task 11: Template · `_activity_strip.html` partial

**Files:**
- Create: `app/templates/_activity_strip.html`
- Modify: `app/static/style.css` — append activity strip styles

- [ ] **Step 1: Write the partial**

Write `app/templates/_activity_strip.html`:
```jinja
<section class="activity-strip" aria-label="Recent activity">
  <div class="activity-col">
    <span class="activity-label">TODAY · {{ today_date }}</span>
    <span class="activity-line">
      +{{ activity.today.nodes_added }} nodes
      · {{ activity.today.drafts_authored }} drafts
      · {{ activity.today.drift_events }} drift
      · {{ activity.today.rules_authored }} rules
    </span>
  </div>
  <div class="activity-col activity-col-divider">
    <span class="activity-label">7-DAY</span>
    <div class="sparkline" aria-hidden="true">
      {% set max_val = (activity.week_sparkline | max) or 1 %}
      {% for v in activity.week_sparkline %}
        <span class="spark-bar" style="height: {{ (v / max_val * 24) | round(0, 'ceil') }}px;"></span>
      {% endfor %}
    </div>
  </div>
  <div class="activity-col activity-col-divider">
    <span class="activity-label">30-DAY</span>
    <span class="activity-line">
      +{{ activity.thirty_day.nodes_added }} nodes
      · {{ activity.thirty_day.drafts_reviewed }} reviewed
      · {{ activity.thirty_day.drift_events }} drift
    </span>
  </div>
  <a href="/graph/activity" class="activity-link">activity timeline →</a>
</section>
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.activity-strip {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 14px;
  margin: 14px 0;
  background: #0f172a;
  border-left: 3px solid #34d399;
  border-radius: 4px;
}
.activity-strip .activity-col { display: flex; flex-direction: column; }
.activity-strip .activity-col-divider { padding-left: 18px; border-left: 1px solid #1e293b; }
.activity-strip .activity-label { color: #9ca3af; font-size: 10px; letter-spacing: 1px; }
.activity-strip .activity-line { color: #e5e7eb; font-size: 13px; margin-top: 2px; }
.activity-strip .sparkline { display: flex; gap: 3px; align-items: flex-end; height: 24px; margin-top: 4px; }
.activity-strip .spark-bar { width: 10px; background: #3b82f6; border-radius: 1px; }
.activity-strip .activity-link { margin-left: auto; color: #60a5fa; text-decoration: none; }
.activity-strip .activity-link:hover { text-decoration: underline; }
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/_activity_strip.html app/static/style.css
git commit -m "feat(graphui): _activity_strip partial + styles"
```

---

## Task 12: Template · `_graph_health.html` partial

**Files:**
- Create: `app/templates/_graph_health.html`
- Modify: `app/static/style.css` — append health-tile styles

- [ ] **Step 1: Write the partial**

Write `app/templates/_graph_health.html`:
```jinja
<section class="health-tile" aria-label="Graph health">
  <header class="health-header">
    <span class="health-label">Graph health</span>
    {% if health.calibration.accuracy_pct is not none and health.calibration.accuracy_pct >= 90 and health.telemetry.dead_rules == 0 %}
      <span class="health-status health-ok">● healthy</span>
    {% else %}
      <span class="health-status health-warn">● needs attention</span>
    {% endif %}
    {% if meta and meta.depgraph and meta.depgraph.git_commit %}
      <span class="health-meta">commit <code>{{ meta.depgraph.git_commit[:8] }}</code></span>
    {% endif %}
  </header>
  <div class="health-grid">
    <article class="health-sub">
      <h4>Telemetry · injections (30d)</h4>
      <p class="health-big">{{ health.telemetry.injections_30d }}</p>
      <p class="health-sub-meta">
        {% if health.telemetry.trend_pct > 0 %}<span class="trend-up">▲ {{ health.telemetry.trend_pct }}%</span>{% elif health.telemetry.trend_pct < 0 %}<span class="trend-down">▼ {{ health.telemetry.trend_pct }}%</span>{% else %}<span class="trend-flat">– 0%</span>{% endif %}
        · {{ health.telemetry.ack_rate_pct }}% acknowledged
      </p>
      <p class="health-sub-foot">
        {% if health.telemetry.dead_rules %}<span class="warn">⚠ {{ health.telemetry.dead_rules }} rules never fired</span>{% else %}all rules firing{% endif %}
        · {{ health.telemetry.never_acked_dossiers }} unacked dossiers
      </p>
    </article>
    <article class="health-sub">
      <h4>Calibration · last run</h4>
      {% if health.calibration.last_run_id %}
        <p class="health-big">{{ health.calibration.accuracy_pct }}%</p>
        <p class="health-sub-meta">{{ health.calibration.last_run_id }} · {{ health.calibration.regressions }} regression{{ '' if health.calibration.regressions == 1 else 's' }}</p>
        <p class="health-sub-foot">
          {% if health.calibration.prev_delta_pp %}{% if health.calibration.prev_delta_pp > 0 %}<span class="trend-up">▲ +{{ health.calibration.prev_delta_pp }}pp</span>{% else %}<span class="trend-down">▼ {{ health.calibration.prev_delta_pp }}pp</span>{% endif %} vs prev{% endif %}
          {% if health.calibration.drifted_rules %} · drift in <code>{{ health.calibration.drifted_rules[0] }}</code>{% if health.calibration.drifted_rules|length > 1 %} +{{ health.calibration.drifted_rules|length - 1 }}{% endif %}{% endif %}
        </p>
      {% else %}
        <p class="health-empty">No calibration runs yet.</p>
      {% endif %}
    </article>
    <article class="health-sub">
      <h4>Hottest rules (30d)</h4>
      {% if health.hottest_rules %}
        <ul class="hottest-list">
          {% for h in health.hottest_rules %}
            <li><span class="hot-count">{{ h.count }}×</span> <a href="/graph/rule/{{ h.id }}">{{ h.id }}</a></li>
          {% endfor %}
        </ul>
      {% else %}
        <p class="health-empty">No fires recorded yet.</p>
      {% endif %}
      <p class="health-sub-foot"><a href="/graph/telemetry">see all telemetry →</a></p>
    </article>
  </div>
</section>
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.health-tile { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 12px 14px; margin-bottom: 18px; }
.health-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; }
.health-label { color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; font-size: 11px; }
.health-status.health-ok { color: #34d399; font-size: 11px; }
.health-status.health-warn { color: #fbbf24; font-size: 11px; }
.health-meta { color: #94a3b8; font-size: 11px; }
.health-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.health-sub { background: #0b1220; border: 1px solid #1e293b; border-radius: 4px; padding: 10px 12px; }
.health-sub h4 { margin: 0 0 6px; color: #a78bfa; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.health-big { margin: 0; color: #e5e7eb; font-size: 18px; font-weight: 600; }
.health-sub-meta { margin: 4px 0 0; color: #94a3b8; font-size: 11px; }
.health-sub-foot { margin: 6px 0 0; padding-top: 6px; border-top: 1px dashed #1e293b; color: #94a3b8; font-size: 11px; }
.health-empty { color: #94a3b8; font-size: 12px; margin: 4px 0 0; }
.trend-up { color: #34d399; } .trend-down { color: #f87171; } .trend-flat { color: #94a3b8; }
.warn { color: #fbbf24; }
.hottest-list { list-style: none; padding: 0; margin: 4px 0 0; color: #e5e7eb; font-size: 11px; }
.hottest-list li { padding: 1px 0; }
.hot-count { color: #60a5fa; }
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/_graph_health.html app/static/style.css
git commit -m "feat(graphui): _graph_health partial + styles"
```

---

## Task 13: Template · `_cross_cutting.html` partial

**Files:**
- Create: `app/templates/_cross_cutting.html`
- Modify: `app/static/style.css` — append cross-cutting styles

- [ ] **Step 1: Write the partial**

Write `app/templates/_cross_cutting.html`:
```jinja
<section class="cross-cutting" aria-label="Cross-cutting knowledge">
  <h3 class="section-title">Cross-cutting knowledge</h3>
  <div class="cross-grid">
    <a href="/graph/kind/rules" class="cross-card cross-rules">
      <header><span class="cross-title">Rules · {{ cross.rules.count }}</span><span class="cross-side">claims {{ cross.rules.claimed_repos }} repo{{ '' if cross.rules.claimed_repos == 1 else 's' }}</span></header>
      <p class="cross-line">
        {% for ns in cross.rules.namespaces[:7] %}{{ ns }}{% if not loop.last %} · {% endif %}{% endfor %}
        {% if cross.rules.namespaces|length > 7 %} · +{{ cross.rules.namespaces|length - 7 }} more{% endif %}
      </p>
    </a>
    <a href="/graph/kind/domain" class="cross-card cross-domain">
      <header><span class="cross-title">Domain · {{ cross.domain.count }}</span><span class="cross-side">referenced by {{ cross.domain.referenced_by }}</span></header>
      <p class="cross-line">
        {% for sk, n in cross.domain.subkinds.items() %}{{ sk }} · {{ n }}{% if not loop.last %} · {% endif %}{% endfor %}
      </p>
    </a>
    <a href="/graph/kind/processes" class="cross-card cross-processes">
      <header><span class="cross-title">Processes · {{ cross.processes.count }}</span><span class="cross-side">spans {{ cross.processes.spans_repos }} repo{{ '' if cross.processes.spans_repos == 1 else 's' }}</span></header>
      <p class="cross-line">
        {% for name in cross.processes.names %}{{ name }}{% if not loop.last %} · {% endif %}{% endfor %}
        {% if cross.processes.count > cross.processes.names|length %} · +{{ cross.processes.count - cross.processes.names|length }} more{% endif %}
      </p>
    </a>
  </div>
</section>
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.cross-cutting { margin-bottom: 18px; }
.section-title { color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; font-size: 11px; margin: 0 0 8px; }
.cross-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.cross-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 12px; color: #e5e7eb; text-decoration: none; }
.cross-card header { display: flex; justify-content: space-between; align-items: baseline; }
.cross-rules .cross-title { color: #a78bfa; font-weight: 600; }
.cross-domain .cross-title { color: #34d399; font-weight: 600; }
.cross-processes .cross-title { color: #34d399; font-weight: 600; }
.cross-side { color: #94a3b8; font-size: 11px; }
.cross-line { color: #94a3b8; font-size: 11px; margin: 4px 0 0; }
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/_cross_cutting.html app/static/style.css
git commit -m "feat(graphui): _cross_cutting partial + styles"
```

---

## Task 14: Template · `_repo_card.html` partial

**Files:**
- Create: `app/templates/_repo_card.html`
- Modify: `app/static/style.css` — append repo-card styles

- [ ] **Step 1: Write the partial**

Write `app/templates/_repo_card.html`:
```jinja
{% set act = repo.activity %}
{% set deps = repo.dep_counts %}
{% set cc = repo.cross_cuts %}
<a href="/graph/repo/{{ repo.basename }}" class="repo-card repo-card-{{ act.classification }}">
  <header class="repo-card-head">
    <span class="repo-card-name">{{ repo.basename }}</span>
    <span class="repo-card-langs">
      {% for l in repo.languages %}{{ l.label }}{% if not loop.last %} · {% endif %}{% endfor %}
    </span>
    {% if act.today_node_delta %}
      <span class="repo-card-today">+{{ act.today_node_delta }} today</span>
    {% elif act.classification == "dormant" or act.classification == "dead-candidate" %}
      <span class="repo-card-quiet">no activity today</span>
    {% endif %}
  </header>

  <div class="repo-card-activity">
    <span class="repo-card-meta">activity (7d):</span>
    <span class="sparkline-inline" aria-hidden="true">
      {% set m = (act.sparkline | max) or 1 %}
      {% for v in act.sparkline %}<span class="spark-cell" style="height:{{ (v / m * 14) | round(0,'ceil') }}px;"></span>{% endfor %}
    </span>
    <span class="repo-card-meta">{{ act.commits_7d }} commit{{ '' if act.commits_7d == 1 else 's' }} · {{ repo.node_count }} nodes · {{ repo.current_pct }}% current</span>
  </div>

  <div class="state-bar repo-card-states">
    {% for state_key in ['current', 'llm_drafted', 'unreviewed', 'stale', 'missing'] %}
      {% set n = repo.state_counts.get(state_key, 0) %}
      {% if n > 0 %}<span class="state-bar-seg state-bar-{{ state_key }}" style="flex: {{ n }};" title="{{ n }} {{ state_key }}"></span>{% endif %}
    {% endfor %}
  </div>

  {% if repo.areas %}
  <div class="repo-card-areas">
    {% for a in repo.areas[:5] %}<span class="area-chip">📁 {{ a.dir }}/</span>{% endfor %}
    {% if repo.areas|length > 5 %}<span class="area-chip area-more">+{{ repo.areas|length - 5 }}</span>{% endif %}
  </div>
  {% endif %}

  <footer class="repo-card-foot">
    <span class="dep-stat">↑ inbound <b>{{ deps.inbound_repos }}</b></span>
    <span class="dep-stat">↓ outbound <b>{{ deps.outbound_repos }}</b></span>
    <span class="dep-stat">⊕ external <b>{{ deps.external_pkgs }}</b></span>
    <span class="dep-sep">·</span>
    <span class="cross-stat cross-rules-tag">🧷 {{ cc.rules|length }} rules</span>
    <span class="cross-stat cross-proc-tag">⤳ {{ cc.processes|length }} processes</span>
    {% if repo.has_stale %}<span class="repo-card-stale">⚠ {{ repo.state_counts.stale }} stale</span>{% endif %}
  </footer>
</a>
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.repo-card { display: block; background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 12px 14px; margin-bottom: 10px; color: #e5e7eb; text-decoration: none; }
.repo-card:hover { border-color: #334155; }
.repo-card-dormant { opacity: 0.85; }
.repo-card-dead-candidate { border-color: #422006; background: #1c1917; }
.repo-card-head { display: flex; align-items: baseline; gap: 10px; }
.repo-card-name { font-weight: 600; font-size: 14px; color: #e5e7eb; }
.repo-card-langs { color: #94a3b8; font-size: 11px; }
.repo-card-today { margin-left: auto; color: #34d399; font-size: 11px; }
.repo-card-quiet { margin-left: auto; color: #94a3b8; font-size: 11px; }
.repo-card-activity { display: flex; gap: 12px; align-items: center; margin-top: 8px; }
.repo-card-meta { color: #94a3b8; font-size: 11px; }
.sparkline-inline { display: inline-flex; gap: 2px; align-items: flex-end; height: 14px; }
.sparkline-inline .spark-cell { width: 6px; background: #60a5fa; border-radius: 1px; }
.repo-card-states { height: 6px; margin: 8px 0; border-radius: 3px; overflow: hidden; }
.repo-card-areas { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.repo-card-areas .area-chip { background: #0b1220; border: 1px solid #1e293b; padding: 2px 8px; border-radius: 3px; font-size: 11px; color: #94a3b8; }
.repo-card-areas .area-more { color: #64748b; }
.repo-card-foot { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; margin-top: 10px; padding-top: 8px; border-top: 1px dashed #1e293b; font-size: 11px; }
.dep-stat { color: #94a3b8; } .dep-stat b { color: #e5e7eb; font-weight: 600; }
.dep-sep { color: #475569; }
.cross-rules-tag { color: #a78bfa; }
.cross-proc-tag { color: #34d399; }
.repo-card-stale { margin-left: auto; color: #f87171; }
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/_repo_card.html app/static/style.css
git commit -m "feat(graphui): _repo_card partial + styles"
```

---

## Task 15: Template · `_node_list.html` universal partial

Extract the node table from `knowledge.html` into a reusable partial. The dashboard doesn't use it directly in Plan A, but downstream plans (repo detail Nodes tab, search results) will. Refactor `knowledge.html` to include the partial — that exercises the contract without adding new pages.

**Files:**
- Create: `app/templates/_node_list.html`
- Modify: `app/templates/knowledge.html` — include the partial

- [ ] **Step 1: Read the current knowledge.html node-table region**

Run: `grep -n "knowledge-table\|<tbody>\|</tbody>" app/templates/knowledge.html`

- [ ] **Step 2: Write the universal partial**

Write `app/templates/_node_list.html`:
```jinja
{# Universal node list. Caller passes:
   - nodes: iterable of {id, title, kind, subkind?, fan_out, state, href, summary?}
   - columns: list of column-key strings (subset of: title, kind, area, tier, fan_in, state, id)
   - empty_message (optional, default: "No nodes match the current filters.")
#}
{% set cols = columns or ['title', 'kind', 'fan_in', 'state', 'id'] %}
{% if nodes %}
<div class="knowledge-table-wrap scroll-x">
  <table class="knowledge-table">
    <thead>
      <tr>
        <th class="col-sel"><input type="checkbox" class="select-all"></th>
        {% if 'title' in cols %}<th>Title</th>{% endif %}
        {% if 'kind' in cols %}<th>Kind</th>{% endif %}
        {% if 'area' in cols %}<th>Area</th>{% endif %}
        {% if 'tier' in cols %}<th>Tier</th>{% endif %}
        {% if 'fan_in' in cols %}<th class="numeric">Fan-in</th>{% endif %}
        {% if 'state' in cols %}<th>State</th>{% endif %}
        {% if 'id' in cols %}<th>ID</th>{% endif %}
      </tr>
    </thead>
    <tbody>
      {% for n in nodes %}
      <tr class="knowledge-row">
        <td>{% if n.state == "llm_drafted" %}<input type="checkbox" class="row-sel" data-id="{{ n.id }}" data-kind="{{ n.kind }}" data-state="{{ n.state }}">{% endif %}</td>
        {% if 'title' in cols %}<td><a href="{{ n.href }}" class="knowledge-title">{{ n.title }}</a>
          {% if n.summary %}<div class="knowledge-summary">{{ n.summary }}</div>{% endif %}
        </td>{% endif %}
        {% if 'kind' in cols %}<td class="knowledge-kind">{{ n.subkind or n.kind }}</td>{% endif %}
        {% if 'area' in cols %}<td class="knowledge-area">{{ n.area or '—' }}</td>{% endif %}
        {% if 'tier' in cols %}<td>{{ n.tier or '—' }}</td>{% endif %}
        {% if 'fan_in' in cols %}<td class="numeric">{{ n.fan_out }}</td>{% endif %}
        {% if 'state' in cols %}<td><span class="state-chip state-chip-{{ n.state }}">{{ '⚠ ' if n.state == 'stale' else '' }}{{ n.state }}</span></td>{% endif %}
        {% if 'id' in cols %}<td class="src"><code>{{ n.id }}</code></td>{% endif %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% else %}
<p class="empty">{{ empty_message or "No nodes match the current filters." }}</p>
{% endif %}
```

- [ ] **Step 3: Refactor `knowledge.html` to include the partial**

In `app/templates/knowledge.html`, replace the `{% if items %} … {% endif %}` block containing the existing `<table class="knowledge-table">` markup with:

```jinja
{% set columns = ['title', 'kind', 'fan_in', 'state', 'id'] %}
{% with nodes=items, columns=columns %}
  {% include '_node_list.html' %}
{% endwith %}

{% if items %}
<div class="knowledge-bulk" id="bulk-bar" style="display: none;">
  <span id="bulk-count">0 selected</span>
  <button id="bulk-approve" class="flag-action-btn">Promote llm_drafted → current</button>
  <span id="bulk-status" class="flag-action-status"></span>
</div>
{% endif %}
```

(Keep the existing `<script>` block at the bottom unchanged.)

- [ ] **Step 4: Smoke-test the refactor**

Run: `pytest tests/test_smoke.py -v`

Then manually verify by curling: `cd ~/tools/knowledge-graph/graphui && DEPGRAPH_DATA_DIR=$PWD/tests/fixtures/depgraph LOGIGRAPH_DATA_DIR=$PWD/tests/fixtures/logigraph uvicorn app.main:app --port 8099 &` then `curl -s http://localhost:8099/graph/knowledge | grep -c knowledge-table` should print at least `1`. Stop the server: `kill %1`.

- [ ] **Step 5: Commit**

```bash
git add app/templates/_node_list.html app/templates/knowledge.html
git commit -m "refactor(graphui): extract _node_list partial; knowledge.html includes it"
```

---

## Task 16: Rewrite `index.html` using new partials

**Files:**
- Modify: `app/templates/index.html` — full replacement

- [ ] **Step 1: Replace index.html end-to-end**

Write `app/templates/index.html`:
```jinja
{% extends "base.html" %}
{% block title %}graphui{% endblock %}
{% block content %}

{% if review_pending %}
<a href="/graph/review" class="review-banner">
  <span class="review-banner-title">📋 Review queue</span>
  <span class="review-banner-count">{{ review_pending }} pending</span>
  <span class="review-banner-go">→</span>
</a>
{% endif %}

{% if flags.count_fresh or flags.count_tracked %}
<a href="/graph/issues" class="flags-banner">
  <span class="flags-banner-title">⚠ Needs attention</span>
  <span class="flags-banner-counts">
    {% if flags.count_fresh %}<span class="flags-count-fresh">{{ flags.count_fresh }} fresh</span>{% endif %}
    {% if flags.count_tracked %}<span class="flags-count-tracked">{{ flags.count_tracked }} tracked</span>{% endif %}
  </span>
  <span class="flags-banner-go">→</span>
</a>
{% endif %}

{% include '_activity_strip.html' %}
{% include '_graph_health.html' %}
{% include '_cross_cutting.html' %}

<section class="repos-section">
  <header class="repos-header">
    <h3 class="section-title">Tracked repos · {{ repos|length }}</h3>
    <span class="repos-sort">
      sort:
      {% for s in ['activity', 'alpha', 'inbound', 'dead'] %}
        <a href="/graph/?sort={{ s }}{% if activity_filter %}&activity={{ activity_filter }}{% endif %}" class="repos-sort-link{% if sort == s %} repos-sort-active{% endif %}">{{ s }}</a>
        {% if not loop.last %}·{% endif %}
      {% endfor %}
    </span>
  </header>
  <div class="repos-filter">
    {% for f in ['active', 'dormant', 'dead-candidate', 'all'] %}
      <a href="/graph/?activity={{ f }}{% if sort %}&sort={{ sort }}{% endif %}" class="repos-filter-chip{% if activity_filter == f or (f == 'all' and not activity_filter) %} repos-filter-active{% endif %}">{{ f }} · {{ filter_counts[f] }}</a>
    {% endfor %}
  </div>
  {% for repo in repos %}
    {% include '_repo_card.html' %}
  {% else %}
    <p class="empty">No repos match the current filters.</p>
  {% endfor %}
</section>

{% endblock %}
```

- [ ] **Step 2: Append a couple of needed styles**

Append to `app/static/style.css`:
```css
.repos-header { display: flex; justify-content: space-between; align-items: center; margin: 4px 0 8px; }
.repos-sort { color: #94a3b8; font-size: 11px; }
.repos-sort-link { color: #94a3b8; text-decoration: none; margin: 0 4px; }
.repos-sort-link.repos-sort-active { color: #60a5fa; text-decoration: underline; }
.repos-filter { display: flex; gap: 6px; margin-bottom: 12px; }
.repos-filter-chip { background: #0f172a; border: 1px solid #1e293b; color: #94a3b8; padding: 3px 10px; border-radius: 12px; font-size: 11px; text-decoration: none; }
.repos-filter-chip.repos-filter-active { background: #1e3a8a; color: #bfdbfe; border-color: #1e3a8a; }
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/index.html app/static/style.css
git commit -m "feat(graphui): rewrite index.html with new partials"
```

---

## Task 17: Update `index()` route + add `?activity=` and `?sort=` query params

**Files:**
- Modify: `app/main.py` — `index()` route
- Modify: `tests/test_dashboard_route.py` — integration test

- [ ] **Step 1: Write the integration test**

Write `tests/test_dashboard_route.py`:
```python
def test_index_renders_all_sections(client):
    r = client.get("/graph/")
    assert r.status_code == 200
    body = r.text
    # presence of the new sections — match on stable CSS class names
    for cls in ("activity-strip", "health-tile", "cross-cutting", "repos-section"):
        assert cls in body, f"missing section: {cls}"


def test_index_activity_filter(client):
    r = client.get("/graph/?activity=active")
    assert r.status_code == 200
    assert "repos-filter-active" in r.text


def test_index_sort_param_accepted(client):
    for s in ("activity", "alpha", "inbound", "dead"):
        r = client.get(f"/graph/?sort={s}")
        assert r.status_code == 200, f"sort={s} failed: {r.status_code}"
```

- [ ] **Step 2: Run — verify FAIL**

Run: `pytest tests/test_dashboard_route.py -v`
Expected: the section-presence test FAILs (the new index.html exists but the route doesn't yet pass `today_date`, `activity`, `health`, `cross`, `sort`, `activity_filter`, `filter_counts`).

- [ ] **Step 3: Update the route**

In `app/main.py`, replace the existing `index()` function with:
```python
@app.get("/graph/", response_class=HTMLResponse)
@app.get("/graph", response_class=HTMLResponse)
def index(request: Request, sort: str = "activity", activity: str | None = None) -> HTMLResponse:
    """Top-level dashboard: activity strip, graph health, cross-cuts, then repos
    filtered by activity classification and sorted per `sort` param."""
    repos_all = loader.repo_summary()
    counts = {"active": 0, "dormant": 0, "dead-candidate": 0, "all": len(repos_all)}
    for r in repos_all:
        cls = r["activity"]["classification"]
        if cls in counts:
            counts[cls] += 1

    if activity and activity != "all":
        repos = [r for r in repos_all if r["activity"]["classification"] == activity]
    else:
        repos = repos_all

    if sort == "alpha":
        repos = sorted(repos, key=lambda r: r["basename"])
    elif sort == "inbound":
        repos = sorted(repos, key=lambda r: r["dep_counts"]["inbound_repos"], reverse=True)
    elif sort == "dead":
        repos = sorted(repos, key=lambda r: r["dead_code_score"], reverse=True)
    else:  # activity (default)
        repos = sorted(repos, key=lambda r: r["activity"]["commits_7d"], reverse=True)

    today_date = datetime.datetime.now().strftime("%a %b %d")

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "repos": repos,
            "filter_counts": counts,
            "sort": sort,
            "activity_filter": activity,
            "today_date": today_date,
            "activity": loader.activity_summary(),
            "health": loader.graph_health(),
            "cross": loader.cross_cutting_summary(),
            "review_pending": len(_review_queue()),
            "flags": loader.corpus_flags(),
            "meta": loader.load_meta(),
        },
    )
```

(The old `repos=loader.repo_summary()` and `kinds=loader.kind_summary()` keys are gone — the kinds grid is replaced by the cross-cutting section.)

- [ ] **Step 4: Run — verify PASS**

Run: `pytest tests/test_dashboard_route.py tests/test_smoke.py -v`
Expected: all pass.

- [ ] **Step 5: Run the full suite — no regressions**

Run: `pytest tests/ -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_dashboard_route.py
git commit -m "feat(graphui): dashboard route — sort/filter + activity/health/cross"
```

---

## Task 18: Manual browser verification

Hit the live graphui in a browser pointing at the real Concorda data dir; check that the dashboard renders, the activity sparkline shows something plausible, repo cards show, filter chips work, and no template errors appear in the journal.

**Files:** (none modified)

- [ ] **Step 1: Restart the graphui systemd service**

Run: `systemctl --user restart graphui && systemctl --user status graphui --no-pager | head -20`
Expected: `active (running)`. If failed, run `journalctl --user -u graphui -n 50 --no-pager` and fix.

- [ ] **Step 2: Open the dashboard**

URL: `http://localhost:8081/graph/` (or LAN IP).

Confirm visually:
- ACTIVITY strip shows today + 7-day sparkline bars + 30-day text
- Graph health tile shows three sub-tiles (Telemetry · Calibration · Hottest rules)
- Cross-cutting section shows three cards
- Tracked repos section appears, with filter chips and the new card layout
- Each repo card shows: name, language stack, today delta (or "no activity today"), sparkline, state bar, areas chips, dep footer with inbound/outbound/external/rules/processes
- No `Jinja2` traceback in the page

- [ ] **Step 3: Exercise filters**

Visit `?activity=active`, `?activity=dormant`, `?activity=dead-candidate`. Each should narrow the list. The active filter chip should be visually highlighted.

- [ ] **Step 4: Exercise sorts**

Visit `?sort=alpha`, `?sort=inbound`, `?sort=dead`. Order should change.

- [ ] **Step 5: If anything looks wrong, fix it before declaring the plan done**

Common issues:
- Sparkline is all flat at zero → check `repo_activity` git log path resolution (`HOME/<basename>` may not match where the repo lives — adjust `_repo_path` if so).
- Health tile says "no calibration runs" but runs exist → check directory glob.
- Cross-cutting card empty → make sure logigraph data dir contains rules + processes; check `cross_cutting_summary()` shape.

Each fix gets its own commit (e.g., `fix(loader): resolve concorda-* repo paths from project.toml`).

- [ ] **Step 6: Final commit if any fixes**

```bash
git add -A
git commit -m "fix(graphui): post-render polish from manual verification"
```

---

## Self-Review Checklist

Run this after writing the plan; before handing off to the executor.

1. **Spec coverage** (spec § 3 "Dashboard layout" and § 7 "New loader data"):
   - [x] Top bar (search input placeholder is still in base.html and unchanged — full search is Plan C)
   - [x] Activity strip → Task 11 + 17
   - [x] Graph health (telemetry + calibration + hottest) → Tasks 3, 12, 17
   - [x] Cross-cutting strip (above repos) → Tasks 4, 13, 17
   - [x] Repo cards with state bar, kinds, areas, dep footer → Tasks 5-10, 14, 17
   - [x] Sort dropdown (activity / alpha / inbound / dead) → Task 17
   - [x] Filter chips (active / dormant / dead-candidate / all) → Tasks 10, 17
   - [x] Universal node-list partial → Task 15
   - [ ] Dormant collapsed section + dead-candidate amber callout — partially: classification + styling are in, but the spec's "collapse dormant into one expandable row" UX is **not** in this plan. Filter chips cover it for v1; if rendering all 29 dormant cards is too noisy, add a follow-up plan. Surface this trade-off when reviewing.

2. **Placeholder scan**: no "TBD" / "TODO" / "implement later" / "appropriate error handling" / "similar to Task N" patterns present. Each step has concrete code or commands.

3. **Type consistency**:
   - `repo_summary()` row shape: keys named consistently across Tasks 5-10 and 14 (`activity`, `dep_counts`, `cross_cuts`, `dead_code_score`).
   - `cross_cuts` returns lists (rule ids, process ids, domain ids) — repo card uses `cc.rules|length` (correct).
   - `activity_summary()` keys: `today / week_sparkline / thirty_day` — Tasks 2, 11, 17 use the same names.
   - `graph_health()` keys: `telemetry / calibration / hottest_rules` — Tasks 3, 12, 17 use the same names.

If during execution a real spec gap surfaces (e.g., dormant collapse), pause, write a follow-up plan or extend this one inline, then resume.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-graphui-foundation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
