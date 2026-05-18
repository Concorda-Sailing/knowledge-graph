"""#41: TypeScript extractor emits `route_call` primitives for HTTP call
sites, and the v2 regen pipeline joins them against FastAPI endpoint
primitives to produce cross-repo dependent edges."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]  # depgraph/


def _run_ts_extractor(repo_key: str, repo_path: Path) -> list[dict]:
    cmd = [
        "npx", "tsx", str(REPO_ROOT / "extractors" / "typescript" / "extract.ts"),
        "--repo-key", repo_key,
        "--repo-path", str(repo_path),
        "--format", "ndjson",
    ]
    env = {**os.environ, "NODE_OPTIONS": "--max-old-space-size=4096"}
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    assert result.returncode == 0, f"TS extractor failed:\n{result.stderr}"
    prims = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            prims.append(json.loads(line))
    return prims


def _route_calls(prims: list[dict]) -> list[dict]:
    return [p for p in prims if p.get("kind") == "route_call"]


def test_ts_extractor_emits_route_call_for_fetch_string(tmp_path):
    (tmp_path / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2020"}}))
    (tmp_path / "api.ts").write_text(
        "export async function loadUser() {\n"
        "  return fetch('/api/users/me');\n"
        "}\n"
    )
    prims = _run_ts_extractor("web", tmp_path)
    calls = _route_calls(prims)
    assert len(calls) == 1, f"expected 1 route_call, got {calls}"
    sig = calls[0]["signature"]
    assert sig["method"] == "GET"
    assert sig["url_pattern"] == "/api/users/me"
    assert calls[0]["primitive"] == "function"


def test_ts_extractor_reads_method_from_fetch_init_object(tmp_path):
    (tmp_path / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2020"}}))
    (tmp_path / "api.ts").write_text(
        "export async function createUser() {\n"
        "  return fetch('/api/users', { method: 'POST' });\n"
        "}\n"
    )
    calls = _route_calls(_run_ts_extractor("web", tmp_path))
    assert len(calls) == 1
    assert calls[0]["signature"]["method"] == "POST"


def test_ts_extractor_emits_route_call_for_axios_methods(tmp_path):
    (tmp_path / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2020"}}))
    (tmp_path / "api.ts").write_text(
        "import axios from 'axios';\n"
        "export async function fetchUser() { return axios.get('/api/users/me'); }\n"
        "export async function patchUser() { return axios.patch('/api/users/me'); }\n"
    )
    calls = _route_calls(_run_ts_extractor("web", tmp_path))
    methods = sorted(c["signature"]["method"] for c in calls)
    assert methods == ["GET", "PATCH"]
    urls = sorted(c["signature"]["url_pattern"] for c in calls)
    assert urls == ["/api/users/me", "/api/users/me"]


def test_ts_extractor_normalizes_template_literal_url(tmp_path):
    """A template literal `/api/users/${id}` should collapse to
    `/api/users/<var>` to match the Python endpoint's normalized path."""
    (tmp_path / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2020"}}))
    (tmp_path / "api.ts").write_text(
        "export async function loadUser(id: number) {\n"
        "  return fetch(`/api/users/${id}`);\n"
        "}\n"
    )
    calls = _route_calls(_run_ts_extractor("web", tmp_path))
    assert len(calls) == 1
    assert calls[0]["signature"]["url_pattern"] == "/api/users/<var>"


# ---------------------------------------------------------------------------
# Cross-repo join via the v2 pipeline
# ---------------------------------------------------------------------------

def _regen_cross_repo(umbrella: Path, api: Path, web: Path) -> subprocess.CompletedProcess:
    # Cross-repo regen needs project.toml since --repo-key takes only one repo.
    (umbrella / "depgraph").mkdir(parents=True, exist_ok=True)
    (umbrella / "depgraph" / "project.toml").write_text(
        f'[repos.api]\npath = "{api}"\nlanguages = ["python"]\n\n'
        f'[repos.web]\npath = "{web}"\nlanguages = ["typescript"]\n'
    )
    return subprocess.run(
        [
            sys.executable, "-m", "kg.cli",
            "depgraph", "regen",
            "--data-dir", str(umbrella),
        ],
        capture_output=True, text=True, timeout=120,
    )


def test_regen_joins_route_call_to_fastapi_endpoint(tmp_path):
    """End-to-end: a Python FastAPI endpoint and a TS fetch site that calls
    it land in the same corpus with a `calls` edge from the route_call to
    the endpoint."""
    umbrella = tmp_path / "project"
    umbrella.mkdir()
    api = tmp_path / "api"
    web = tmp_path / "web"
    api.mkdir(); web.mkdir()

    # Python: a router that exposes GET /api/users/me. pyproject.toml is
    # what activates the FastAPI plugin (via `has_pypi_dep`), which is what
    # turns `@router.get(...)` into a `kind: endpoint` classification.
    (api / "pyproject.toml").write_text(
        '[project]\nname = "api"\ndependencies = ["fastapi"]\n'
    )
    (api / "main.py").write_text(
        "from fastapi import APIRouter\n\n"
        "router = APIRouter()\n\n"
        "@router.get('/api/users/me')\n"
        "def get_me():\n"
        "    return {'id': 1}\n"
    )

    # TS: a fetch call site against the same URL.
    (web / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2020"}}))
    (web / "useUser.ts").write_text(
        "export async function loadUser() {\n"
        "  return fetch('/api/users/me');\n"
        "}\n"
    )

    r = _regen_cross_repo(umbrella, api, web)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "route_call join:" in r.stdout

    depgraph = umbrella / "depgraph"
    by_target = json.loads((depgraph / "nodes" / "_index" / "by_target.json").read_text())

    # Find the endpoint id.
    endpoint_ids = [
        nid for nid in by_target.keys() if "/api/users/me" in nid or "get_me" in nid
    ]
    if not endpoint_ids:
        # Look in node files for the endpoint.
        endpoint_ids = []
        for f in (depgraph / "nodes").rglob("*.json"):
            if f.name.startswith("_"):
                continue
            try:
                data = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            if data.get("kind") == "endpoint":
                endpoint_ids.append(data["id"])

    assert endpoint_ids, "endpoint never made it into the corpus"
    # At least one endpoint should have an inbound route_call edge.
    matched = False
    for eid in endpoint_ids:
        for edge in by_target.get(eid, []):
            if edge.get("via") == "route_call":
                matched = True
                break
        if matched:
            break
    assert matched, (
        f"no route_call edge found pointing at endpoints {endpoint_ids}; "
        f"by_target keys with route_call edges: "
        f"{[k for k, v in by_target.items() if any(e.get('via') == 'route_call' for e in v)]}"
    )
