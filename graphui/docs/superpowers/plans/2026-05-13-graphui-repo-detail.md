# graphui — Repo Detail Page

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `/graph/repo/{basename}` to match the design: header + stat row + left rail (areas / kinds / cross-cuts) + tabbed main pane (Nodes · Dead code · Dependencies · Telemetry · Activity). Reuses the universal `_node_list.html` partial built in Plan A.

**Architecture:** Strictly additive on the loader (new helpers for inbound/outbound dep details, external package names, dead-code candidates, and a flat node-for-repo iterator). The template is rewritten end-to-end; route gains a `?tab=` query param. Telemetry and Activity tabs are inline stubs that point to the global `/graph/telemetry` and `/graph/activity` pages (already stubbed in Plan A) so the affordance is honest without scope-creeping the per-page work.

**Tech Stack:** FastAPI · Jinja2 · pytest. No new third-party dependencies.

**Spec:** `docs/superpowers/specs/2026-05-13-graphui-categories-design.md` § 4. The Plan A foundation (loader enrichments, universal node-list partial) is a prerequisite — `repo_summary()` already returns the per-repo `activity`, `languages`, `areas`, `dep_counts`, `cross_cuts` fields this page needs at the header / stat-row / left-rail level.

---

## File Structure

**New files:**
- `app/templates/_repo_left_rail.html` — areas tree + kinds breakdown + cross-cuts list
- `app/templates/_repo_tabs.html` — tab strip with active highlighting
- `tests/test_loader_dep_details.py` — inbound + outbound + external-pkgs detail helpers
- `tests/test_loader_dead_code.py` — dead-code candidate helper
- `tests/test_loader_nodes_for_repo.py` — flat node iterator
- `tests/test_repo_route.py` — integration test for the rewritten route

**Modified files:**
- `app/loader.py` — add `nodes_for_repo()` (flat), `repo_inbound_deps_detail()`, `repo_outbound_deps_detail()`, `repo_external_pkgs()`, `repo_dead_code()`
- `app/main.py` — `repo_detail()` route gains `tab`, `area`, `tier` query params + new context
- `app/templates/repo.html` — full rewrite
- `app/static/style.css` — append styles for left rail, tab strip, dependency table, stat row

**Existing files this plan leans on (no edits):**
- `app/templates/_node_list.html` — universal list partial, reused for the Nodes tab
- `app/templates/_repo_card.html` — not used here, but the styles for stat chips and sparkline-inline are picked up from the same stylesheet

**Out of scope (future plans):**
- Replacing the Telemetry/Activity tab stubs with full per-repo views — comes with Plan D when the dedicated pages ship
- Per-symbol click-through from a dependency row to the consuming file in the other repo — link only to node-detail pages for now
- "Eviction plan" UI for dead-code rows — list only, no plan generator

---

## Conventions for this plan

- **Test-first** for every loader helper.
- **Template renders** are verified by an integration test asserting stable CSS class names + tab presence — no snapshot tests.
- **All commits via `.venv/bin/pytest`** — the system pytest is 7.4.4 and doesn't satisfy our pin.
- **Pure-additive loader** — do not touch existing functions. The legacy `nodes_for_repo_grouped` stays for any other caller that still uses it.
- **Each task ends with a commit.** Use the standard `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer.

---

## Task 1: Loader · `nodes_for_repo(basename, …)` (flat)

A flat list of nodes for a repo, with filter and sort controls — the data the Nodes tab needs. Distinct from the existing `nodes_for_repo_grouped` which groups by file path.

**Files:**
- Modify: `app/loader.py`
- Create: `tests/test_loader_nodes_for_repo.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_loader_nodes_for_repo.py`:
```python
def test_nodes_for_repo_returns_flat_list(loader):
    rows = loader.nodes_for_repo("concorda-web")
    assert isinstance(rows, list)
    assert rows, "fixture should yield at least one node"
    r = rows[0]
    # Universal node-list shape: title, kind, fan_out, state, href, id, area
    for k in ("id", "title", "kind", "fan_out", "state", "href", "area"):
        assert k in r, f"missing key: {k}"


def test_nodes_for_repo_filters_kind(loader):
    rows = loader.nodes_for_repo("concorda-web", kind="component")
    assert all(r["kind"] == "component" for r in rows)


def test_nodes_for_repo_filters_area(loader):
    # The fixture node is under "app/page.tsx" → area "app"
    rows = loader.nodes_for_repo("concorda-web", area="app")
    assert all(r["area"] == "app" for r in rows)


def test_nodes_for_repo_filters_tier(loader):
    rows = loader.nodes_for_repo("concorda-web", tier="C")  # fan_out=5 → tier B; expect 0 of C in fixture
    # Just verify the filter is applied; do not pin a count.
    assert all(r.get("tier") == "C" for r in rows)


def test_nodes_for_repo_sorts_by_fan_out_desc_by_default(loader):
    rows = loader.nodes_for_repo("concorda-web")
    fan_outs = [r["fan_out"] for r in rows]
    assert fan_outs == sorted(fan_outs, reverse=True)


def test_nodes_for_repo_unknown_repo_returns_empty(loader):
    assert loader.nodes_for_repo("ghost-repo") == []
```

- [ ] **Step 2: Verify FAIL**

`.venv/bin/pytest tests/test_loader_nodes_for_repo.py -v`
Expected: AttributeError or 6 failures (no `nodes_for_repo` yet).

- [ ] **Step 3: Implement `nodes_for_repo`**

Append to `app/loader.py`:
```python
def nodes_for_repo(
    basename: str,
    kind: str | None = None,
    area: str | None = None,
    tier: str | None = None,
    state: str | None = None,
    sort: str = "fan_out",
) -> list[dict]:
    """Flat node list for a repo, ready to feed the universal `_node_list.html`
    partial. Each row carries the keys the partial reads (`id`, `title`, `kind`,
    `fan_out`, `state`, `href`, `id`, plus `area` and `tier`)."""
    out: list[dict] = []
    for n in load_depgraph_nodes():
        src = n.get("source") or {}
        if src.get("repo") != basename:
            continue
        path = src.get("path") or ""
        area_val = path.split("/", 1)[0] if "/" in path else path
        if kind and n.get("kind") != kind:
            continue
        if area and area_val != area:
            continue
        if tier and n.get("tier") != tier:
            continue
        if state and n.get("dossier_state") != state:
            continue
        out.append({
            "id": n["id"],
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "kind": n.get("kind", "—"),
            "subkind": n.get("subkind"),
            "fan_out": n.get("fan_out", 0),
            "state": n["dossier_state"],
            "tier": n.get("tier"),
            "area": area_val,
            "href": f"/graph/node/{n['id']}",
        })
    if sort == "title":
        out.sort(key=lambda r: r["title"].lower())
    elif sort == "state":
        out.sort(key=lambda r: r["state"])
    else:  # fan_out (default)
        out.sort(key=lambda r: r["fan_out"], reverse=True)
    return out
```

- [ ] **Step 4: Verify PASS**

`.venv/bin/pytest tests/test_loader_nodes_for_repo.py -v`
Expected: 6 passed.

- [ ] **Step 5: Full suite check**

`.venv/bin/pytest tests/ -v`
Expected: 25 passed (19 prior + 6 new).

- [ ] **Step 6: Commit**

```
git add app/loader.py tests/test_loader_nodes_for_repo.py
git commit -m "feat(loader): nodes_for_repo flat iterator with area/tier/kind/state filters

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Loader · inbound/outbound dep details

Counts already exist in `repo_dep_counts`. We need symbol-level rows for the Dependencies tab: each row is `{from_repo, from_id, from_title, to_id, to_title}`.

**Files:**
- Modify: `app/loader.py`
- Create: `tests/test_loader_dep_details.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_loader_dep_details.py`:
```python
def test_inbound_deps_detail_shape(loader):
    rows = loader.repo_inbound_deps_detail("concorda-api")
    # The fixture has concorda-web::Page → concorda-api::CrewService.
    assert isinstance(rows, list)
    if rows:
        r = rows[0]
        for k in ("from_repo", "from_id", "to_id"):
            assert k in r, f"missing key: {k}"


def test_inbound_deps_detail_for_unknown_repo_is_empty(loader):
    assert loader.repo_inbound_deps_detail("ghost") == []


def test_outbound_deps_detail_shape(loader):
    rows = loader.repo_outbound_deps_detail("concorda-web")
    assert isinstance(rows, list)
    if rows:
        r = rows[0]
        for k in ("to_repo", "from_id", "to_id"):
            assert k in r, f"missing key: {k}"


def test_dep_detail_skips_self_references(loader):
    inbound = loader.repo_inbound_deps_detail("concorda-web")
    # No row should have from_repo == basename
    assert all(r["from_repo"] != "concorda-web" for r in inbound)
    outbound = loader.repo_outbound_deps_detail("concorda-web")
    assert all(r["to_repo"] != "concorda-web" for r in outbound)
```

- [ ] **Step 2: Verify FAIL**

`.venv/bin/pytest tests/test_loader_dep_details.py -v`
Expected: 4 failures (functions don't exist).

- [ ] **Step 3: Implement**

Append to `app/loader.py`:
```python
def _titles_by_id() -> dict[str, str]:
    """One-pass title lookup. Computed per-call, not cached."""
    titles: dict[str, str] = {}
    for n in load_depgraph_nodes():
        nid = n.get("id")
        if nid:
            titles[nid] = n.get("title") or nid.rsplit("::", 1)[-1]
    return titles


def repo_inbound_deps_detail(basename: str) -> list[dict]:
    """Rows of {from_repo, from_id, from_title, to_id, to_title} — one per
    cross-repo dependent edge pointing INTO a node in `basename`."""
    out: list[dict] = []
    titles = _titles_by_id()
    for target_id, dependers in load_dependents().items():
        target_repo = target_id.split("::", 1)[0]
        if target_repo != basename:
            continue
        for d in dependers:
            dep_id = d.get("id") or ""
            dep_repo = dep_id.split("::", 1)[0]
            if not dep_repo or dep_repo == basename:
                continue
            out.append({
                "from_repo": dep_repo,
                "from_id": dep_id,
                "from_title": titles.get(dep_id, dep_id.rsplit("::", 1)[-1]),
                "to_id": target_id,
                "to_title": titles.get(target_id, target_id.rsplit("::", 1)[-1]),
            })
    out.sort(key=lambda r: (r["from_repo"], r["from_id"]))
    return out


def repo_outbound_deps_detail(basename: str) -> list[dict]:
    """Rows of {to_repo, from_id, from_title, to_id, to_title} — one per
    cross-repo dependent edge pointing OUT of a node in `basename`."""
    out: list[dict] = []
    titles = _titles_by_id()
    for target_id, dependers in load_dependents().items():
        target_repo = target_id.split("::", 1)[0]
        for d in dependers:
            dep_id = d.get("id") or ""
            dep_repo = dep_id.split("::", 1)[0]
            if dep_repo != basename or target_repo == basename:
                continue
            out.append({
                "to_repo": target_repo,
                "from_id": dep_id,
                "from_title": titles.get(dep_id, dep_id.rsplit("::", 1)[-1]),
                "to_id": target_id,
                "to_title": titles.get(target_id, target_id.rsplit("::", 1)[-1]),
            })
    out.sort(key=lambda r: (r["to_repo"], r["to_id"]))
    return out
```

- [ ] **Step 4: Verify PASS**

`.venv/bin/pytest tests/test_loader_dep_details.py -v`
Expected: 4 passed.

- [ ] **Step 5: Full suite**

`.venv/bin/pytest tests/ -v` → 29 passed.

- [ ] **Step 6: Commit**

```
git add app/loader.py tests/test_loader_dep_details.py
git commit -m "feat(loader): repo_{inbound,outbound}_deps_detail (symbol-level rows)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Loader · `repo_external_pkgs(basename)`

Counts already exist via `repo_dep_counts`. For the Dependencies tab we need the *names* — package.json deps + devDeps, plus pyproject/requirements lines.

**Files:**
- Modify: `app/loader.py`
- Modify: `tests/test_loader_dep_details.py` (append)

- [ ] **Step 1: Append test**

Append to `tests/test_loader_dep_details.py`:
```python
def test_repo_external_pkgs_shape(loader):
    pkgs = loader.repo_external_pkgs("concorda-web")
    assert isinstance(pkgs, list)
    for entry in pkgs:
        assert set(entry.keys()) >= {"name", "source"}
        assert entry["source"] in ("npm", "python")


def test_repo_external_pkgs_unknown_is_empty(loader):
    assert loader.repo_external_pkgs("ghost") == []
```

- [ ] **Step 2: Verify FAIL**

`.venv/bin/pytest tests/test_loader_dep_details.py -v`
Expected: 2 new failures.

- [ ] **Step 3: Implement**

Append to `app/loader.py`:
```python
def repo_external_pkgs(basename: str) -> list[dict]:
    """List external packages declared by `basename`. Each row:
    {name, source} where source is 'npm' or 'python'. Sorted by name."""
    repo = _repo_path(basename)
    if repo is None:
        return []
    out: list[dict] = []
    pkg = repo / "package.json"
    if pkg.exists():
        try:
            row = json.loads(pkg.read_text())
            for name in (row.get("dependencies") or {}):
                out.append({"name": name, "source": "npm"})
            for name in (row.get("devDependencies") or {}):
                out.append({"name": name, "source": "npm"})
        except (OSError, json.JSONDecodeError):
            pass
    reqs = repo / "requirements.txt"
    if reqs.exists():
        for line in reqs.read_text(errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            # strip pin syntax: package>=1.0,<2 → package
            name = s.split("=", 1)[0].split("<", 1)[0].split(">", 1)[0].split("[", 1)[0].strip()
            if name:
                out.append({"name": name, "source": "python"})
    pyproj = repo / "pyproject.toml"
    if pyproj.exists():
        txt = pyproj.read_text(errors="ignore")
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
                    name = s.strip("\"',").split("=", 1)[0].split("<", 1)[0].split(">", 1)[0].split("[", 1)[0].strip()
                    if name:
                        out.append({"name": name, "source": "python"})
    out.sort(key=lambda r: r["name"].lower())
    return out
```

- [ ] **Step 4: PASS + full**

`.venv/bin/pytest tests/test_loader_dep_details.py -v` → 6 passed.
`.venv/bin/pytest tests/ -v` → 31 passed.

- [ ] **Step 5: Commit**

```
git add app/loader.py tests/test_loader_dep_details.py
git commit -m "feat(loader): repo_external_pkgs (names + source npm/python)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Loader · `repo_dead_code(basename)`

Nodes in this repo with zero inbound deps. Drives the Dead code tab. Each row: `{id, title, kind, area, fan_out_in (=0), out_count, href, state, last_edit_age_days?}`.

**Files:**
- Modify: `app/loader.py`
- Create: `tests/test_loader_dead_code.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_loader_dead_code.py`:
```python
def test_dead_code_returns_list_of_dicts(loader):
    rows = loader.repo_dead_code("concorda-web")
    assert isinstance(rows, list)
    for r in rows:
        for k in ("id", "title", "kind", "area", "href", "state"):
            assert k in r, f"missing key: {k}"


def test_dead_code_unknown_repo_empty(loader):
    assert loader.repo_dead_code("ghost") == []


def test_dead_code_excludes_nodes_with_inbound(loader):
    """The fixture has concorda-api::CrewService with 1 inbound dep.
    repo_dead_code on concorda-api must NOT include CrewService."""
    rows = loader.repo_dead_code("concorda-api")
    ids = [r["id"] for r in rows]
    assert "concorda-api::services/crew.py::CrewService" not in ids
```

- [ ] **Step 2: FAIL**

`.venv/bin/pytest tests/test_loader_dead_code.py -v`
Expected: 3 failures.

- [ ] **Step 3: Implement**

Append to `app/loader.py`:
```python
def repo_dead_code(basename: str) -> list[dict]:
    """Nodes belonging to `basename` with zero inbound dep references.
    Sorted by fan_out asc (least-connected first)."""
    dependents = load_dependents()
    incoming_count: dict[str, int] = {tid: len(d) for tid, d in dependents.items()}
    out: list[dict] = []
    for n in load_depgraph_nodes():
        src = n.get("source") or {}
        if src.get("repo") != basename:
            continue
        nid = n["id"]
        if incoming_count.get(nid, 0) > 0:
            continue
        path = src.get("path") or ""
        area = path.split("/", 1)[0] if "/" in path else path
        out.append({
            "id": nid,
            "title": n.get("title") or nid.rsplit("::", 1)[-1],
            "kind": n.get("kind", "—"),
            "area": area,
            "fan_out": n.get("fan_out", 0),
            "state": n["dossier_state"],
            "href": f"/graph/node/{nid}",
        })
    out.sort(key=lambda r: (r["fan_out"], r["area"], r["title"].lower()))
    return out
```

- [ ] **Step 4: PASS**

`.venv/bin/pytest tests/test_loader_dead_code.py -v` → 3 passed.
`.venv/bin/pytest tests/ -v` → 34 passed.

- [ ] **Step 5: Commit**

```
git add app/loader.py tests/test_loader_dead_code.py
git commit -m "feat(loader): repo_dead_code (zero-inbound nodes per repo)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Template partial · `_repo_left_rail.html`

The 30%-width left rail with Areas, Kinds + Tier, and Cross-cuts. Consumes `repo` (one row from `repo_summary()`) — all the data is already enriched there.

**Files:**
- Create: `app/templates/_repo_left_rail.html`
- Modify: `app/static/style.css` — append rail styles

- [ ] **Step 1: Write the partial**

Create `app/templates/_repo_left_rail.html`:
```jinja
<aside class="repo-rail">

  <div class="rail-card">
    <h4 class="rail-title">Areas</h4>
    {% if repo.areas %}
      <ul class="rail-list">
        {% for a in repo.areas %}
          <li>
            <a href="/graph/repo/{{ repo.basename }}?tab=nodes&area={{ a.dir }}"
               class="rail-row{% if area_filter == a.dir %} rail-row-active{% endif %}">
              <span class="rail-row-label">📁 {{ a.dir }}/</span>
              <span class="rail-row-count">{{ a.node_count }}</span>
            </a>
          </li>
        {% endfor %}
      </ul>
    {% else %}
      <p class="rail-empty">No tracked areas.</p>
    {% endif %}
  </div>

  <div class="rail-card">
    <h4 class="rail-title">Kinds</h4>
    {% if repo.kinds %}
      <ul class="rail-list">
        {% for k in repo.kinds %}
          <li>
            <a href="/graph/repo/{{ repo.basename }}?tab=nodes&kind={{ k.kind }}"
               class="rail-row{% if kind_filter == k.kind %} rail-row-active{% endif %}">
              <span class="rail-row-label">{{ k.kind }}</span>
              <span class="rail-row-count">{{ k.count }}</span>
            </a>
          </li>
        {% endfor %}
      </ul>
    {% else %}
      <p class="rail-empty">No tracked kinds.</p>
    {% endif %}
    {% if tier_counts %}
      <div class="rail-subtitle">Tier</div>
      <div class="rail-tier-row">
        {% for t in ['A', 'B', 'C'] %}
          {% set n = tier_counts.get(t, 0) %}
          <a href="/graph/repo/{{ repo.basename }}?tab=nodes&tier={{ t }}"
             class="rail-tier-chip{% if tier_filter == t %} rail-tier-chip-active{% endif %}">{{ t }} · {{ n }}</a>
        {% endfor %}
      </div>
    {% endif %}
  </div>

  <div class="rail-card">
    <h4 class="rail-title">Cross-cuts</h4>
    {% if repo.cross_cuts.rules %}
      <div class="rail-cross-head rail-cross-rules">🧷 {{ repo.cross_cuts.rules|length }} rule{{ '' if repo.cross_cuts.rules|length == 1 else 's' }}</div>
      <ul class="rail-list rail-list-tight">
        {% for rid in repo.cross_cuts.rules[:8] %}
          <li><a href="/graph/rule/{{ rid }}" class="rail-row-link">{{ rid.split('::')[-1] }}</a></li>
        {% endfor %}
        {% if repo.cross_cuts.rules|length > 8 %}<li class="rail-row-more">+{{ repo.cross_cuts.rules|length - 8 }} more</li>{% endif %}
      </ul>
    {% endif %}
    {% if repo.cross_cuts.processes %}
      <div class="rail-cross-head rail-cross-procs">⤳ {{ repo.cross_cuts.processes|length }} process{{ '' if repo.cross_cuts.processes|length == 1 else 'es' }}</div>
      <ul class="rail-list rail-list-tight">
        {% for pid in repo.cross_cuts.processes[:6] %}
          <li><a href="/graph/process/{{ pid }}" class="rail-row-link">{{ pid.split('::')[-1] }}</a></li>
        {% endfor %}
        {% if repo.cross_cuts.processes|length > 6 %}<li class="rail-row-more">+{{ repo.cross_cuts.processes|length - 6 }} more</li>{% endif %}
      </ul>
    {% endif %}
    {% if repo.cross_cuts.domain %}
      <div class="rail-cross-head rail-cross-domain">⊙ {{ repo.cross_cuts.domain|length }} domain entit{{ 'y' if repo.cross_cuts.domain|length == 1 else 'ies' }} referenced</div>
      <ul class="rail-list rail-list-tight">
        {% for did in repo.cross_cuts.domain[:6] %}
          <li><a href="/graph/domain/{{ did }}" class="rail-row-link">{{ did.split('::')[-1] }}</a></li>
        {% endfor %}
        {% if repo.cross_cuts.domain|length > 6 %}<li class="rail-row-more">+{{ repo.cross_cuts.domain|length - 6 }} more</li>{% endif %}
      </ul>
    {% endif %}
    {% if not (repo.cross_cuts.rules or repo.cross_cuts.processes or repo.cross_cuts.domain) %}
      <p class="rail-empty">No rules, processes, or domain entities reference this repo.</p>
    {% endif %}
  </div>

</aside>
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.repo-rail { display: flex; flex-direction: column; gap: 10px; }
.rail-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 12px; }
.rail-title { margin: 0 0 6px; color: #9ca3af; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.rail-subtitle { color: #9ca3af; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin: 8px 0 4px; }
.rail-list { list-style: none; padding: 0; margin: 0; }
.rail-list-tight li { padding: 1px 0; font-size: 11px; }
.rail-row { display: flex; justify-content: space-between; padding: 2px 4px; color: #e5e7eb; font-size: 11px; text-decoration: none; border-radius: 3px; }
.rail-row:hover { background: #1e293b; }
.rail-row-active { background: #1e3a8a; color: #bfdbfe; }
.rail-row-label { }
.rail-row-count { color: #94a3b8; }
.rail-row-link { color: #94a3b8; text-decoration: none; }
.rail-row-link:hover { color: #e5e7eb; }
.rail-row-more { color: #64748b; font-size: 11px; padding-left: 4px; }
.rail-empty { color: #94a3b8; font-size: 11px; margin: 4px 0 0; }
.rail-tier-row { display: flex; gap: 4px; }
.rail-tier-chip { background: #1e293b; color: #e5e7eb; padding: 2px 8px; border-radius: 3px; font-size: 11px; text-decoration: none; }
.rail-tier-chip-active { background: #1e3a8a; color: #bfdbfe; }
.rail-cross-head { font-size: 11px; margin-top: 6px; font-weight: 600; }
.rail-cross-rules { color: #a78bfa; }
.rail-cross-procs { color: #34d399; }
.rail-cross-domain { color: #34d399; }
```

- [ ] **Step 3: Commit**

```
git add app/templates/_repo_left_rail.html app/static/style.css
git commit -m "feat(graphui): _repo_left_rail partial + styles

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Template partial · `_repo_tabs.html`

A tab strip that highlights the active tab and links to the route with `?tab=`.

**Files:**
- Create: `app/templates/_repo_tabs.html`
- Modify: `app/static/style.css` — append tab styles

- [ ] **Step 1: Write the partial**

Create `app/templates/_repo_tabs.html`:
```jinja
{# Caller passes:
   - basename: repo basename (string)
   - active_tab: one of 'nodes', 'dead', 'deps', 'telemetry', 'activity'
   - tab_counts: {nodes: int, dead: int, deps: int}  (telemetry/activity uncountable here)
#}
<nav class="repo-tabs" aria-label="Repo detail tabs">
  <a href="/graph/repo/{{ basename }}?tab=nodes" class="repo-tab{% if active_tab == 'nodes' %} repo-tab-active{% endif %}">
    Nodes <span class="repo-tab-count">{{ tab_counts.nodes }}</span>
  </a>
  <a href="/graph/repo/{{ basename }}?tab=deps" class="repo-tab{% if active_tab == 'deps' %} repo-tab-active{% endif %}">
    Dependencies <span class="repo-tab-count">{{ tab_counts.deps }}</span>
  </a>
  <a href="/graph/repo/{{ basename }}?tab=dead" class="repo-tab{% if active_tab == 'dead' %} repo-tab-active repo-tab-warn{% elif tab_counts.dead > 0 %} repo-tab-warn{% endif %}">
    Dead code <span class="repo-tab-count">{{ tab_counts.dead }}</span>
  </a>
  <a href="/graph/repo/{{ basename }}?tab=telemetry" class="repo-tab{% if active_tab == 'telemetry' %} repo-tab-active{% endif %}">
    Telemetry
  </a>
  <a href="/graph/repo/{{ basename }}?tab=activity" class="repo-tab{% if active_tab == 'activity' %} repo-tab-active{% endif %}">
    Activity
  </a>
</nav>
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.repo-tabs { display: flex; gap: 4px; border-bottom: 1px solid #1e293b; margin-bottom: 12px; }
.repo-tab { padding: 6px 12px; color: #94a3b8; text-decoration: none; border-radius: 3px 3px 0 0; font-size: 12px; }
.repo-tab:hover { color: #e5e7eb; }
.repo-tab-active { background: #1e3a8a; color: #bfdbfe; }
.repo-tab-count { color: inherit; opacity: 0.7; margin-left: 4px; }
.repo-tab-warn { color: #fbbf24; }
.repo-tab-warn.repo-tab-active { background: #422006; color: #fde68a; }
```

- [ ] **Step 3: Commit**

```
git add app/templates/_repo_tabs.html app/static/style.css
git commit -m "feat(graphui): _repo_tabs partial + styles

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Rewrite `app/templates/repo.html`

Header + stat row + two-column body (left rail + tabbed main pane).

**Files:**
- Modify: `app/templates/repo.html` — full replacement
- Modify: `app/static/style.css` — append final styles

- [ ] **Step 1: Replace the template**

Write `app/templates/repo.html`:
```jinja
{% extends "base.html" %}
{% block title %}{{ repo.basename }}{% endblock %}
{% block content %}

<div class="repo-detail-breadcrumb">
  <a href="/graph/">graphui</a> &nbsp;/&nbsp; <a href="/graph/">repos</a> &nbsp;/&nbsp; <span>{{ repo.basename }}</span>
</div>

<section class="repo-detail-header">
  <div class="repo-detail-title-row">
    <h1 class="repo-detail-name">{{ repo.basename }}</h1>
    <span class="repo-detail-langs">
      {% for l in repo.languages %}{{ l.label }}{% if not loop.last %} · {% endif %}{% endfor %}
    </span>
    {% if repo.activity.today_node_delta %}
      <span class="repo-detail-today">+{{ repo.activity.today_node_delta }} today</span>
    {% endif %}
    <span class="repo-detail-sparkline" aria-hidden="true">
      {% set m = (repo.activity.sparkline | max) or 1 %}
      {% for v in repo.activity.sparkline %}<span class="spark-cell" style="height:{{ (v / m * 14) | round(0,'ceil') }}px;"></span>{% endfor %}
    </span>
    <span class="repo-detail-meta">
      {{ repo.activity.commits_7d }} commits / 7d
      {% if repo.activity.last_push_age_days is not none %} · last push {{ repo.activity.last_push_age_days }}d ago{% endif %}
    </span>
  </div>

  <div class="repo-detail-stats">
    <span class="stat-chip">{{ repo.node_count }} nodes</span>
    <span class="stat-chip">{{ repo.current_pct }}% current</span>
    <span class="stat-chip">↑ {{ repo.dep_counts.inbound_repos }} inbound</span>
    <span class="stat-chip">↓ {{ repo.dep_counts.outbound_repos }} outbound</span>
    <span class="stat-chip">⊕ {{ repo.dep_counts.external_pkgs }} ext pkgs</span>
    {% if tab_counts.dead %}<span class="stat-chip stat-chip-warn">⚠ {{ tab_counts.dead }} dead-code</span>{% endif %}
    <span class="stat-chip stat-chip-cross">🧷 {{ repo.cross_cuts.rules|length }} rules · {{ repo.cross_cuts.processes|length }} processes</span>
  </div>
</section>

<div class="repo-detail-body">

  {% include '_repo_left_rail.html' %}

  <main class="repo-detail-main">

    {% include '_repo_tabs.html' %}

    {% if active_tab == 'nodes' %}
      <div class="filter-row">
        <span class="filter-label">State</span>
        <a href="/graph/repo/{{ repo.basename }}?tab=nodes{% if kind_filter %}&kind={{ kind_filter }}{% endif %}{% if area_filter %}&area={{ area_filter }}{% endif %}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}" class="chip{% if not state_filter %} chip-active{% endif %}">all</a>
        {% for st in ['current', 'llm_drafted', 'unreviewed', 'stale', 'missing'] %}
          {% set n = repo.state_counts.get(st, 0) %}
          {% if n > 0 %}
          <a href="/graph/repo/{{ repo.basename }}?tab=nodes&state={{ st }}{% if kind_filter %}&kind={{ kind_filter }}{% endif %}{% if area_filter %}&area={{ area_filter }}{% endif %}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}" class="chip chip-state-{{ st }}{% if state_filter == st %} chip-active{% endif %}">{{ st }} <span class="chip-count">{{ n }}</span></a>
          {% endif %}
        {% endfor %}
      </div>
      {% set columns = ['title', 'area', 'kind', 'tier', 'fan_in', 'state'] %}
      {% with nodes=nodes, columns=columns %}
        {% include '_node_list.html' %}
      {% endwith %}

    {% elif active_tab == 'deps' %}
      <div class="deps-section">
        <h3 class="deps-h">Inbound · {{ inbound_deps|length }}</h3>
        {% if inbound_deps %}
        <table class="deps-table">
          <thead><tr><th>From repo</th><th>From symbol</th><th>To symbol (in {{ repo.basename }})</th></tr></thead>
          <tbody>
            {% for r in inbound_deps %}
            <tr>
              <td><a href="/graph/repo/{{ r.from_repo }}">{{ r.from_repo }}</a></td>
              <td><a href="/graph/node/{{ r.from_id }}">{{ r.from_title }}</a></td>
              <td><a href="/graph/node/{{ r.to_id }}">{{ r.to_title }}</a></td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
        <p class="empty">No inbound dependencies from other tracked repos.</p>
        {% endif %}

        <h3 class="deps-h">Outbound · {{ outbound_deps|length }}</h3>
        {% if outbound_deps %}
        <table class="deps-table">
          <thead><tr><th>From symbol (in {{ repo.basename }})</th><th>To repo</th><th>To symbol</th></tr></thead>
          <tbody>
            {% for r in outbound_deps %}
            <tr>
              <td><a href="/graph/node/{{ r.from_id }}">{{ r.from_title }}</a></td>
              <td><a href="/graph/repo/{{ r.to_repo }}">{{ r.to_repo }}</a></td>
              <td><a href="/graph/node/{{ r.to_id }}">{{ r.to_title }}</a></td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
        <p class="empty">This repo references no other tracked repos.</p>
        {% endif %}

        <h3 class="deps-h">External · {{ external_pkgs|length }}</h3>
        {% if external_pkgs %}
        <div class="deps-pkgs">
          {% for pkg in external_pkgs %}
            <span class="dep-pkg dep-pkg-{{ pkg.source }}">{{ pkg.name }}</span>
          {% endfor %}
        </div>
        {% else %}
        <p class="empty">No external package declarations found.</p>
        {% endif %}
      </div>

    {% elif active_tab == 'dead' %}
      {% if dead_code %}
        <p class="repo-detail-note">Nodes in <code>{{ repo.basename }}</code> with zero inbound references. Sorted by fan-out asc.</p>
        {% set columns = ['title', 'area', 'kind', 'fan_in', 'state'] %}
        {% with nodes=dead_code, columns=columns %}
          {% include '_node_list.html' %}
        {% endwith %}
      {% else %}
        <p class="empty">No dead-code candidates in this repo — every node has at least one inbound reference.</p>
      {% endif %}

    {% elif active_tab == 'telemetry' %}
      <p class="repo-detail-note">Per-repo telemetry will land in a follow-up plan. For now, see the <a href="/graph/telemetry">global telemetry rollup</a>.</p>

    {% elif active_tab == 'activity' %}
      <p class="repo-detail-note">Per-repo activity timeline will land in a follow-up plan. For now, see the <a href="/graph/activity">global activity rollup</a>.</p>
    {% endif %}

  </main>
</div>

{% endblock %}
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.repo-detail-breadcrumb { color: #94a3b8; font-size: 11px; margin-bottom: 8px; }
.repo-detail-breadcrumb a { color: #60a5fa; text-decoration: none; }
.repo-detail-header { margin-bottom: 14px; }
.repo-detail-title-row { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.repo-detail-name { margin: 0; font-size: 22px; color: #e5e7eb; }
.repo-detail-langs { color: #94a3b8; font-size: 11px; }
.repo-detail-today { color: #34d399; font-size: 11px; }
.repo-detail-sparkline { display: inline-flex; gap: 2px; align-items: flex-end; height: 14px; }
.repo-detail-sparkline .spark-cell { width: 6px; background: #60a5fa; border-radius: 1px; }
.repo-detail-meta { color: #94a3b8; font-size: 11px; margin-left: auto; }
.repo-detail-stats { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; font-size: 11px; }
.stat-chip { background: #0f172a; border: 1px solid #1e293b; padding: 3px 10px; border-radius: 3px; color: #e5e7eb; }
.stat-chip-warn { border-color: #422006; color: #fbbf24; }
.stat-chip-cross { color: #a78bfa; }
.repo-detail-body { display: grid; grid-template-columns: 30% 1fr; gap: 14px; }
.repo-detail-main { min-width: 0; }
.repo-detail-note { color: #94a3b8; font-size: 12px; margin: 8px 0 12px; }
.deps-section h3.deps-h { color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-size: 11px; margin: 14px 0 6px; }
.deps-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.deps-table th { text-align: left; padding: 6px 8px; background: #1e293b; color: #94a3b8; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
.deps-table td { padding: 4px 8px; border-bottom: 1px solid #1e293b; color: #e5e7eb; }
.deps-table a { color: #60a5fa; text-decoration: none; }
.deps-pkgs { display: flex; flex-wrap: wrap; gap: 4px; }
.dep-pkg { background: #1e293b; color: #e5e7eb; padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.dep-pkg-npm { border-left: 2px solid #fb923c; }
.dep-pkg-python { border-left: 2px solid #60a5fa; }
@media (max-width: 900px) {
  .repo-detail-body { grid-template-columns: 1fr; }
}
```

- [ ] **Step 3: Commit**

```
git add app/templates/repo.html app/static/style.css
git commit -m "feat(graphui): rewrite repo.html with header + rail + tabs

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Update `repo_detail` route + integration tests

The route gains `tab`, `area`, `tier` params and passes tab-specific context.

**Files:**
- Modify: `app/main.py`
- Create: `tests/test_repo_route.py`

- [ ] **Step 1: Write the failing integration tests**

Create `tests/test_repo_route.py`:
```python
def test_repo_detail_renders_known_repo(client):
    r = client.get("/graph/repo/concorda-web")
    assert r.status_code == 200
    body = r.text
    for cls in ("repo-detail-header", "repo-tabs", "repo-rail"):
        assert cls in body, f"missing section: {cls}"


def test_repo_detail_404_for_unknown(client):
    r = client.get("/graph/repo/ghost-repo")
    assert r.status_code == 404


def test_repo_detail_tab_param_accepted(client):
    for t in ("nodes", "dead", "deps", "telemetry", "activity"):
        r = client.get(f"/graph/repo/concorda-web?tab={t}")
        assert r.status_code == 200, f"tab={t} failed: {r.status_code}"


def test_repo_detail_dead_tab_lists_known_dead_node(client):
    r = client.get("/graph/repo/concorda-web?tab=dead")
    assert r.status_code == 200
    # The fixture's Page node IS referenced by no other tracked node into it,
    # so it should appear on the dead-code tab of concorda-web.
    assert "concorda-web::app/page.tsx::Page" in r.text or "Page" in r.text
```

- [ ] **Step 2: Verify FAIL**

`.venv/bin/pytest tests/test_repo_route.py -v`
Expected: section-presence test fails because route still uses old template variables (`summary`, `groups`).

- [ ] **Step 3: Update the route**

Replace the existing `repo_detail` function in `app/main.py` with:

```python
@app.get("/graph/repo/{basename}", response_class=HTMLResponse)
def repo_detail(
    request: Request,
    basename: str,
    tab: str = "nodes",
    kind: str | None = None,
    area: str | None = None,
    tier: str | None = None,
    state: str | None = None,
) -> HTMLResponse:
    """One source repo with header + left rail + tabbed main pane."""
    repo = next(
        (r for r in loader.repo_summary() if r["basename"] == basename),
        None,
    )
    if repo is None:
        raise HTTPException(404, f"repo not found in any tracked node: {basename}")

    nodes = loader.nodes_for_repo(basename, kind=kind, area=area, tier=tier, state=state)
    dead_code = loader.repo_dead_code(basename)
    inbound = loader.repo_inbound_deps_detail(basename)
    outbound = loader.repo_outbound_deps_detail(basename)
    external = loader.repo_external_pkgs(basename)

    # Tier breakdown for the left rail (across all nodes in this repo, no filters).
    tier_counts: dict[str, int] = {}
    for n in loader.nodes_for_repo(basename):
        t = n.get("tier")
        if t:
            tier_counts[t] = tier_counts.get(t, 0) + 1

    tab_counts = {
        "nodes": repo["node_count"],
        "dead": len(dead_code),
        "deps": len(inbound) + len(outbound) + len(external),
    }

    if tab not in ("nodes", "dead", "deps", "telemetry", "activity"):
        tab = "nodes"

    return TEMPLATES.TemplateResponse(
        request,
        "repo.html",
        {
            "repo": repo,
            "active_tab": tab,
            "nodes": nodes,
            "dead_code": dead_code,
            "inbound_deps": inbound,
            "outbound_deps": outbound,
            "external_pkgs": external,
            "tab_counts": tab_counts,
            "tier_counts": tier_counts,
            "kind_filter": kind,
            "area_filter": area,
            "tier_filter": tier,
            "state_filter": state,
            "meta": loader.load_meta(),
        },
    )
```

- [ ] **Step 4: PASS**

`.venv/bin/pytest tests/test_repo_route.py -v` → 4 passed.

- [ ] **Step 5: Full suite — no regressions**

`.venv/bin/pytest tests/ -v` → 38 passed (34 from prior tasks + 4 new).

- [ ] **Step 6: Commit**

```
git add app/main.py tests/test_repo_route.py
git commit -m "feat(graphui): repo_detail route — tabs/filters + new context

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Manual browser verification

**Files:** (none modified)

- [ ] **Step 1: Restart graphui**

Run: `systemctl --user restart graphui`
Then: `systemctl --user status graphui --no-pager | head -10`
Confirm `active (running)`.

- [ ] **Step 2: Open the dashboard, click a repo**

Visit `http://localhost:8081/graph/` and click any repo card. Confirm the new repo detail page renders:
- Breadcrumb (graphui / repos / repo-name)
- Header with name, language stack, today delta (if any), 7-day sparkline, last-push age, "47 commits / 7d"
- Stat chips row: nodes / current% / inbound / outbound / external pkgs / dead-code / rules+processes
- Left rail (30% width on wide screens, full width below 900px): Areas, Kinds + Tier chips, Cross-cuts (rules, processes, domain)
- Tab strip: Nodes · Dependencies · Dead code · Telemetry · Activity. Default is Nodes.

- [ ] **Step 3: Exercise the tabs**

- `?tab=nodes` (default): universal node list with title/area/kind/tier/fan-in/state columns
- `?tab=deps`: three sections — Inbound (table), Outbound (table), External (pill list with `dep-pkg-npm` orange-border, `dep-pkg-python` blue-border)
- `?tab=dead`: zero-inbound nodes for this repo
- `?tab=telemetry`: stub message with link to `/graph/telemetry`
- `?tab=activity`: stub message with link to `/graph/activity`

- [ ] **Step 4: Exercise the left-rail click-throughs**

Click an Area row in the left rail → URL should become `?tab=nodes&area=<dir>`, the list narrows, the chip highlights.
Click a Kind row → `?tab=nodes&kind=<kind>`, narrows.
Click a Tier chip (A/B/C) → `?tab=nodes&tier=<T>`, narrows.

- [ ] **Step 5: Cross-cut click-throughs**

Click any rule name in the left rail → navigates to `/graph/rule/<id>` (no 404).
Click any process name → `/graph/process/<id>`.
Click any domain name → `/graph/domain/<id>`.

- [ ] **Step 6: If anything looks wrong, fix it before declaring the plan done**

Common issues:
- Stat-chip wrapping is ugly on narrow screens → add `flex-wrap: wrap` (already in plan).
- Tier chips in the rail don't visually align with Kinds list — verify `.rail-tier-row` styles.
- Empty repos throw an exception when `repo.areas` is empty — the partial already guards with `{% if repo.areas %}`; check if the guard is reached.

Each fix gets its own commit.

- [ ] **Step 7: Final commit if any fixes**

```
git add -A
git commit -m "fix(graphui): post-render polish for repo detail"
```

---

## Self-Review Checklist

Run before handing off:

1. **Spec coverage** (spec § 4):
   - [x] URL `/graph/repo/{basename}` — Task 8
   - [x] Breadcrumb + name + lang stack + today delta + 7d sparkline + last-push — Task 7
   - [x] Stat row (nodes / current% / ↑inbound / ↓outbound / ⊕external / dead-code / rules·processes) — Task 7
   - [x] Left rail: Areas / Kinds + Tier / Cross-cuts — Task 5
   - [x] Tabs: Nodes (default), Dead code, Dependencies, Telemetry stub, Activity stub — Tasks 6, 7, 8
   - [x] In-repo search box — **NOT in this plan.** The header sketch in the mockup showed an in-repo search input; the underlying scoped-search functionality belongs to Plan C (semantic search). Listed as out-of-scope above; surface this when reviewing.

2. **Placeholder scan:** No TBD / TODO / "appropriate error handling" / "similar to Task N" in any task.

3. **Type consistency:**
   - `nodes_for_repo` rows include `area` and `tier`. `_node_list.html` reads both. ✓
   - `repo_dead_code` rows include `fan_out` (the partial uses `fan_in` column header but reads `n.fan_out`). The header label says Fan-in for the universal list because both inbound and "fan-out" connotations land here — this is a known label/key mismatch carried from Plan A. Don't fix it as a side effect of this plan.
   - `tab_counts` shape matches what `_repo_tabs.html` reads (`tab_counts.nodes`, `.deps`, `.dead`). ✓
   - `inbound_deps` rows: `{from_repo, from_id, from_title, to_id, to_title}`. Outbound: `{to_repo, from_id, from_title, to_id, to_title}`. Template uses these keys exactly. ✓

If during execution a real spec gap surfaces, pause and extend the plan inline rather than papering over.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-graphui-repo-detail.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review, fast iteration.
**2. Inline Execution** — execute here with checkpoints.

Which approach?
