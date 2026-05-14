# graphui — Settings Page

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only `/graph/settings` page that surfaces what's currently invisible — project.toml contents, per-repo git remotes, and the extractor file inventory with sizes/mtimes/content hashes. First step toward the larger "extractor library + versioning" arc.

**Architecture:** Three loader helpers read project.toml via stdlib `tomllib`, resolve git remotes via the existing `git_remote_url()` helper, and walk the project's `<data_dir>/extractors/` directory (plus the framework's `~/tools/knowledge-graph/depgraph/extractors/` for the future generic library). One Jinja template renders three sections. One new route + nav link. No new third-party dependencies.

**Tech Stack:** FastAPI · Jinja2 · stdlib (`tomllib`, `hashlib`) · pytest.

**Spec context:** Out of band — the user asked for a settings surface that distinguishes project-custom vs generic extractors, with versions. v1 ships the read-only inventory; explicit `__extractor_version__` and a generic library are deferred to follow-up plans.

---

## File Structure

**New files:**
- `app/templates/settings.html` — three sections (Project · Tracked repos · Extractor inventory)
- `tests/test_loader_settings.py` — covers all three new loader helpers
- `tests/test_settings_route.py` — integration test for `GET /graph/settings`
- `tests/fixtures/depgraph/project.toml` — minimal config so the loader test has something to read
- `tests/fixtures/depgraph/extractors/example.py` — one file so the extractor inventory has something to enumerate

**Modified files:**
- `app/loader.py` — add `read_project_toml()`, `tracked_repos_settings()`, `extractor_inventory()`
- `app/main.py` — add `/graph/settings` route
- `app/templates/base.html` — add "Settings" link to the topbar nav
- `app/static/style.css` — append settings-page styles

**Out of scope (later plans):**
- Declaring `__extractor_version__` constants in each extractor (Layer 2 of the brainstorm)
- A generic extractor library under `~/tools/knowledge-graph/depgraph/extractors/generic/` (Layer 3)
- A "Reload project.toml" or "Edit extractor" action — read-only for v1
- Git-SHA-of-last-touch on extractor files — adds repo-root resolution complexity; defer

---

## Conventions for this plan

- **Test-first** for every loader helper.
- **`tomllib` is stdlib in Python 3.11+** — the box runs 3.12.3, so no `tomli` shim needed.
- **All commits via `.venv/bin/pytest`.**
- **Pure-additive loader** — do not modify existing functions.
- Use the standard `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer on every commit.

---

## Task 1: Loader · project.toml + tracked-repo settings + extractor inventory

Three helpers fed by one parse pass over project.toml. Bundled in one task because they share a single source-of-truth read and one new test file.

**Files:**
- Modify: `app/loader.py` — append
- Create: `tests/test_loader_settings.py`
- Modify: `tests/fixtures/depgraph/project.toml` (create — does not exist yet)
- Create: `tests/fixtures/depgraph/extractors/example.py`

- [ ] **Step 1: Add the project.toml fixture**

Create `tests/fixtures/depgraph/project.toml`:
```toml
[project]
name = "fixture-project"
primary_repo = "web"

[logigraph]
data_dir = "~/fixture/logigraph"

[repos.web]
path = "~/concorda-web"
extractor = ["npx", "tsx", "{data_dir}/extractors/example.py"]

[repos.api]
path = "~/concorda-api"
extractor = ["python3", "{data_dir}/extractors/example.py"]
files_arg = "--only"

[memory]
mirror = "fixture/memory"
```

- [ ] **Step 2: Add an extractor file fixture**

Create `tests/fixtures/depgraph/extractors/example.py`:
```python
#!/usr/bin/env python3
"""Fixture extractor — emits one synthetic node."""
__extractor_version__ = "0.1.0"

def main():
    print('{"id": "fixture::demo", "kind": "model"}')


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write the failing tests**

Create `tests/test_loader_settings.py`:
```python
def test_read_project_toml_returns_dict(loader):
    cfg = loader.read_project_toml()
    assert isinstance(cfg, dict)
    assert cfg["project"]["name"] == "fixture-project"
    assert cfg["project"]["primary_repo"] == "web"
    assert set(cfg["repos"].keys()) >= {"web", "api"}


def test_tracked_repos_settings_shape(loader):
    rows = loader.tracked_repos_settings()
    assert isinstance(rows, list) and len(rows) >= 2
    r = rows[0]
    for k in ("key", "basename", "path", "git_remote", "extractor_cmd",
             "extractor_file", "files_arg"):
        assert k in r, f"missing key: {k}"
    # extractor_cmd is the literal list from project.toml.
    assert isinstance(r["extractor_cmd"], list)
    # files_arg is None for repos without one, a string when set.
    web = next(x for x in rows if x["key"] == "web")
    api = next(x for x in rows if x["key"] == "api")
    assert web["files_arg"] is None
    assert api["files_arg"] == "--only"


def test_extractor_inventory_shape(loader):
    inv = loader.extractor_inventory()
    assert isinstance(inv, list)
    # Should include the fixture's example.py.
    files = [e["filename"] for e in inv]
    assert "example.py" in files
    ex = next(e for e in inv if e["filename"] == "example.py")
    for k in ("filename", "path", "size_bytes", "mtime_iso",
             "sha256_prefix", "scope", "declared_version"):
        assert k in ex, f"missing key: {k}"
    assert ex["scope"] == "project"
    assert ex["declared_version"] == "0.1.0"  # parsed from __extractor_version__
    assert len(ex["sha256_prefix"]) == 12  # short hex
```

- [ ] **Step 4: Verify FAIL**

`.venv/bin/pytest tests/test_loader_settings.py -v`
Expected: 3 failures (AttributeError on the new functions).

- [ ] **Step 5: Implement the three helpers**

Append to `app/loader.py`:
```python
import tomllib  # stdlib 3.11+
import hashlib


def read_project_toml() -> dict:
    """Parse the depgraph project.toml. Returns the raw dict; callers
    interpret `repos.*`, `[project]`, etc."""
    path = DEPGRAPH / "project.toml"
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def tracked_repos_settings() -> list[dict]:
    """One row per [repos.*] in project.toml. Each row carries enough
    detail for the Settings page: key, basename, resolved filesystem path,
    git remote URL, extractor command, extractor file (resolved abs), and
    files_arg if any."""
    cfg = read_project_toml()
    repos = cfg.get("repos") or {}
    out: list[dict] = []
    for key, info in repos.items():
        raw_path = info.get("path") or ""
        path = Path(raw_path).expanduser() if raw_path else None
        extractor_cmd = list(info.get("extractor") or [])
        # Resolve {data_dir} in the extractor command to locate the file.
        extractor_file = None
        for part in extractor_cmd:
            if isinstance(part, str) and "{data_dir}" in part:
                resolved = part.replace("{data_dir}", str(DEPGRAPH))
                if Path(resolved).exists():
                    extractor_file = resolved
                    break
        git_remote = git_remote_url(path) if path and (path / ".git").exists() else None
        out.append({
            "key": key,
            "basename": path.name if path else "—",
            "path": str(path) if path else "—",
            "path_exists": bool(path and path.exists()),
            "git_remote": git_remote,
            "extractor_cmd": extractor_cmd,
            "extractor_file": extractor_file,
            "files_arg": info.get("files_arg"),
        })
    return out


_EXTRACTOR_VERSION_RE = re.compile(r"""__extractor_version__\s*=\s*["']([^"']+)["']""")


def _scan_extractor_file(path: Path, scope: str) -> dict:
    """Build the per-file row for the inventory."""
    raw = path.read_bytes() if path.exists() else b""
    text = ""
    try:
        text = raw.decode("utf-8", errors="ignore")
    except UnicodeDecodeError:
        pass
    m = _EXTRACTOR_VERSION_RE.search(text)
    return {
        "filename": path.name,
        "path": str(path),
        "size_bytes": len(raw),
        "mtime_iso": dt.datetime.fromtimestamp(
            path.stat().st_mtime, dt.timezone.utc
        ).isoformat(timespec="seconds") if path.exists() else None,
        "sha256_prefix": hashlib.sha256(raw).hexdigest()[:12],
        "scope": scope,
        "declared_version": m.group(1) if m else None,
    }


def extractor_inventory() -> list[dict]:
    """Walk the project-custom extractor dir AND the framework-generic
    extractor dir. Returns one row per file with size, mtime, sha256
    prefix, and scope (`project` or `generic`)."""
    out: list[dict] = []
    project_dir = DEPGRAPH / "extractors"
    if project_dir.exists():
        for p in sorted(project_dir.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                out.append(_scan_extractor_file(p, "project"))
    # Framework-generic location — empty for now, will populate when Layer 3 ships.
    framework_dir = _DEPGRAPH_TOOL_ROOT / "extractors" / "generic"
    if framework_dir.exists():
        for p in sorted(framework_dir.rglob("*.py")):
            out.append(_scan_extractor_file(p, "generic"))
        for p in sorted(framework_dir.rglob("*.ts")):
            out.append(_scan_extractor_file(p, "generic"))
    return out
```

- [ ] **Step 6: Verify PASS**

`.venv/bin/pytest tests/test_loader_settings.py -v` → 3 passed.

- [ ] **Step 7: Full suite**

`.venv/bin/pytest tests/ -v` → 41 passed (38 prior + 3 new).

- [ ] **Step 8: Commit**

```
git add app/loader.py tests/test_loader_settings.py tests/fixtures/depgraph/project.toml tests/fixtures/depgraph/extractors/example.py
git commit -m "feat(loader): read_project_toml + tracked_repos_settings + extractor_inventory

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Template · `settings.html`

Three sections (Project · Tracked repos · Extractor inventory) consuming the loader helpers from Task 1.

**Files:**
- Create: `app/templates/settings.html`
- Modify: `app/static/style.css` — append settings styles

- [ ] **Step 1: Write the template**

Create `app/templates/settings.html`:
```jinja
{% extends "base.html" %}
{% block title %}settings{% endblock %}
{% block content %}

<div class="settings-header">
  <div class="repo-detail-breadcrumb">
    <a href="/graph/">graphui</a> &nbsp;/&nbsp; <span>settings</span>
  </div>
  <h1>Settings</h1>
  <p class="settings-note">Read-only view of <code>project.toml</code>, tracked repos, and the extractor inventory. Editing happens in the file directly; restart the graphui systemd unit after changes.</p>
</div>

<section class="settings-section">
  <h3 class="section-title">Project</h3>
  {% if project %}
  <table class="settings-table">
    <tbody>
      <tr><th>Name</th><td>{{ project.get('project', {}).get('name', '—') }}</td></tr>
      <tr><th>Primary repo</th><td>{{ project.get('project', {}).get('primary_repo', '—') }}</td></tr>
      <tr><th>Logigraph data dir</th><td><code>{{ project.get('logigraph', {}).get('data_dir', '—') }}</code></td></tr>
      <tr><th>Memory mirror</th><td><code>{{ project.get('memory', {}).get('mirror', '—') }}</code></td></tr>
      <tr><th>project.toml path</th><td><code>{{ project_toml_path }}</code></td></tr>
    </tbody>
  </table>
  {% else %}
  <p class="empty">No <code>project.toml</code> found at <code>{{ project_toml_path }}</code>.</p>
  {% endif %}
</section>

<section class="settings-section">
  <h3 class="section-title">Tracked repos · {{ repos|length }}</h3>
  {% if repos %}
  <table class="settings-table settings-table-wide">
    <thead>
      <tr>
        <th>Key</th>
        <th>Basename</th>
        <th>Path</th>
        <th>Git remote</th>
        <th>Extractor</th>
        <th>files_arg</th>
      </tr>
    </thead>
    <tbody>
      {% for r in repos %}
      <tr>
        <td><code>{{ r.key }}</code></td>
        <td><a href="/graph/repo/{{ r.basename }}">{{ r.basename }}</a></td>
        <td>
          <code class="settings-path{% if not r.path_exists %} settings-path-missing{% endif %}">{{ r.path }}</code>
          {% if not r.path_exists %}<span class="settings-warn">⚠ missing</span>{% endif %}
        </td>
        <td>
          {% if r.git_remote %}<a href="{{ r.git_remote }}" target="_blank" rel="noopener">{{ r.git_remote }}</a>
          {% else %}<span class="settings-mute">—</span>{% endif %}
        </td>
        <td>
          <code class="settings-cmd">{% for part in r.extractor_cmd %}{{ part }}{% if not loop.last %} {% endif %}{% endfor %}</code>
        </td>
        <td>
          {% if r.files_arg %}<code>{{ r.files_arg }}</code>
          {% else %}<span class="settings-mute">—</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">No <code>[repos.*]</code> tables in project.toml.</p>
  {% endif %}
</section>

<section class="settings-section">
  <h3 class="section-title">Extractors · {{ extractors|length }}</h3>
  {% if extractors %}
  <table class="settings-table settings-table-wide">
    <thead>
      <tr>
        <th>File</th>
        <th>Scope</th>
        <th>Version</th>
        <th class="numeric">Size</th>
        <th>Modified</th>
        <th>SHA-256</th>
      </tr>
    </thead>
    <tbody>
      {% for e in extractors %}
      <tr>
        <td><code>{{ e.filename }}</code></td>
        <td><span class="settings-scope settings-scope-{{ e.scope }}">{{ e.scope }}</span></td>
        <td>{% if e.declared_version %}<code>{{ e.declared_version }}</code>{% else %}<span class="settings-mute">—</span>{% endif %}</td>
        <td class="numeric">{{ e.size_bytes }}</td>
        <td><code class="settings-mute">{{ e.mtime_iso or '—' }}</code></td>
        <td><code class="settings-mute">{{ e.sha256_prefix }}</code></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <p class="settings-note">
    <strong>Scope</strong>: <em>project</em> = lives in this project's <code>extractors/</code> dir; <em>generic</em> = framework-shipped reusable extractor (none today — coming in a follow-up plan).
    <strong>Version</strong>: parsed from the file's <code>__extractor_version__ = "..."</code> constant if present; otherwise rely on the SHA-256 prefix for identity.
  </p>
  {% else %}
  <p class="empty">No extractor files found under <code>{{ project_toml_path | replace('/project.toml', '/extractors/') }}</code> or the framework generic dir.</p>
  {% endif %}
</section>

{% endblock %}
```

- [ ] **Step 2: Append styles**

Append to `app/static/style.css`:
```css
.settings-header { margin-bottom: 16px; }
.settings-header h1 { margin: 0 0 4px; font-size: 22px; color: #e5e7eb; }
.settings-note { color: #94a3b8; font-size: 12px; margin: 4px 0 12px; }
.settings-section { margin-bottom: 20px; }
.settings-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.settings-table-wide { table-layout: auto; }
.settings-table th { text-align: left; padding: 6px 8px; background: #1e293b; color: #94a3b8; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
.settings-table td { padding: 4px 8px; border-bottom: 1px solid #1e293b; color: #e5e7eb; vertical-align: top; }
.settings-table td.numeric { text-align: right; font-family: var(--mono); }
.settings-table a { color: #60a5fa; text-decoration: none; }
.settings-path { color: #e5e7eb; }
.settings-path-missing { color: #f87171; }
.settings-warn { color: #fbbf24; font-size: 11px; margin-left: 6px; }
.settings-mute { color: #64748b; }
.settings-cmd { color: #94a3b8; font-size: 11px; word-break: break-all; }
.settings-scope { padding: 1px 8px; border-radius: 3px; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.settings-scope-project { background: #1e3a8a; color: #bfdbfe; }
.settings-scope-generic { background: #14532d; color: #bbf7d0; }
```

- [ ] **Step 3: Commit**

```
git add app/templates/settings.html app/static/style.css
git commit -m "feat(graphui): settings.html template + styles

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Route · `GET /graph/settings` + integration test

**Files:**
- Modify: `app/main.py` — add route
- Create: `tests/test_settings_route.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_settings_route.py`:
```python
def test_settings_renders_200(client):
    r = client.get("/graph/settings")
    assert r.status_code == 200


def test_settings_includes_all_sections(client):
    r = client.get("/graph/settings")
    body = r.text
    for marker in ("Project", "Tracked repos", "Extractors"):
        assert marker in body, f"missing section header: {marker}"


def test_settings_lists_fixture_repos(client):
    r = client.get("/graph/settings")
    body = r.text
    # Fixture project.toml declares repos.web and repos.api.
    assert "concorda-web" in body
    assert "concorda-api" in body


def test_settings_lists_fixture_extractor(client):
    r = client.get("/graph/settings")
    body = r.text
    assert "example.py" in body
    # The fixture declared __extractor_version__ = "0.1.0".
    assert "0.1.0" in body
```

- [ ] **Step 2: Verify FAIL**

`.venv/bin/pytest tests/test_settings_route.py -v`
Expected: 4 failures (404 on the route).

- [ ] **Step 3: Add the route**

In `app/main.py`, insert this route handler near the other page routes (place it after `activity_page` for consistency with grouping):

```python
@app.get("/graph/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    """Read-only view of project.toml, tracked repos with git remotes, and the
    extractor file inventory. v1 is informational only — no editing."""
    return TEMPLATES.TemplateResponse(
        request,
        "settings.html",
        {
            "project": loader.read_project_toml(),
            "repos": loader.tracked_repos_settings(),
            "extractors": loader.extractor_inventory(),
            "project_toml_path": str(loader.DEPGRAPH / "project.toml"),
            "meta": loader.load_meta(),
        },
    )
```

- [ ] **Step 4: PASS**

`.venv/bin/pytest tests/test_settings_route.py -v` → 4 passed.

- [ ] **Step 5: Full suite**

`.venv/bin/pytest tests/ -v` → 45 passed (41 prior + 4 new).

- [ ] **Step 6: Commit**

```
git add app/main.py tests/test_settings_route.py
git commit -m "feat(graphui): /graph/settings route + integration tests

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Topbar nav link + manual verification

The page exists but it has no entry point. Add it to the topbar nav.

**Files:**
- Modify: `app/templates/base.html`

- [ ] **Step 1: Locate the nav block**

Open `app/templates/base.html` and find the `<nav>` block inside `<header class="topbar">`. It currently contains links to Knowledge, Issues, Review.

- [ ] **Step 2: Append a Settings link**

Add a Settings anchor at the end of the nav, after the Review link:

```jinja
<a href="/graph/settings" class="nav-settings">Settings</a>
```

(No badge — the link is always available.)

- [ ] **Step 3: Restart graphui + verify in browser**

Run: `systemctl --user restart graphui`
Then: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/graph/settings` → expect `200`.
Open the page in a browser: visually confirm three sections render with real project.toml + the three Concorda extractors (`extract_api.py`, `extract_web.ts`, `extract_tests.ts`). Verify the git-remote column shows GitHub URLs for each repo (or `—` if a repo isn't a GitHub remote).

- [ ] **Step 4: Commit**

```
git add app/templates/base.html
git commit -m "feat(graphui): topbar Settings link

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: If browser verification surfaced any issue (e.g. git-remote not resolving for a repo), fix it in its own commit before declaring done.**

---

## Self-Review Checklist

1. **Coverage** (the user's three asks):
   - ✓ Settings page exists at `/graph/settings`, linked from nav (Tasks 3 + 4)
   - ✓ Shows which git repo each tracked repo points to (Task 1's `git_remote` field; Task 2's "Git remote" column)
   - ✓ Lists extractors with metadata (file, size, mtime, content hash, declared version when present)
   - ✓ Distinguishes project-custom vs generic via `scope` field (Task 1) + colored badge (Task 2 CSS); generic column will be empty until Layer 3 ships, which is correct
   - ✗ "Versions" — we only read `__extractor_version__` when present. None of the existing Concorda extractors declare one today, so the Version column will mostly show `—`. The plan acknowledges this; the long-term fix (Layer 2) is its own plan.

2. **Placeholder scan:** no TBD / TODO / "appropriate error handling" patterns. Every step has concrete code.

3. **Type consistency:**
   - `read_project_toml() -> dict` returns raw TOML dict; template reads `project.get('project',{}).get('name')`. ✓
   - `tracked_repos_settings()` rows: `{key, basename, path, path_exists, git_remote, extractor_cmd, extractor_file, files_arg}` — template uses all of these. ✓
   - `extractor_inventory()` rows: `{filename, path, size_bytes, mtime_iso, sha256_prefix, scope, declared_version}` — template uses all of these. ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-graphui-settings-page.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review, fast iteration.
**2. Inline Execution** — execute here with checkpoints.

Which approach?
