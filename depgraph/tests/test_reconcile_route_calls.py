"""Integration test: reconcile.py joins route_call nodes against endpoint
nodes and writes the cross-repo edge to by_target.json."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "route_calls"
REPO_ROOT = Path(__file__).resolve().parent.parent  # depgraph repo root


def _run_reconcile(work: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(work)}
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "extractors" / "reconcile.py")],
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )


def _setup_work(tmp_path: Path) -> Path:
    """Copy fixture into tmp_path, create real repo dirs + stub source files,
    and rewrite project.toml to point at those dirs.

    Without real repo dirs detect_orphans archives the fixture nodes before
    _join_route_calls runs (a missing repo dir is a misconfiguration signal,
    not a silent skip)."""
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)

    # Create real repo dirs + stub source files the fixture nodes point at.
    api_root = tmp_path / "rc-api"
    web_root = tmp_path / "rc-web"
    (api_root / "routers").mkdir(parents=True)
    (api_root / "routers" / "events.py").touch()
    (web_root / "src" / "lib").mkdir(parents=True)
    (web_root / "src" / "lib" / "api.ts").touch()

    # Rewrite project.toml to point at the tmp dirs, not /tmp/rc-*.
    cfg_path = work / "project.toml"
    txt = cfg_path.read_text()
    txt = txt.replace("/tmp/rc-api", str(api_root))
    txt = txt.replace("/tmp/rc-web", str(web_root))
    cfg_path.write_text(txt)

    return work


def test_reconcile_emits_route_call_dependent(tmp_path):
    work = _setup_work(tmp_path)

    result = _run_reconcile(work)
    assert result.returncode == 0, (
        f"reconcile failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    dependents_path = work / "nodes" / "_index" / "by_target.json"
    assert dependents_path.exists(), "reconcile did not write by_target.json"
    # Regression for #43: reconcile.py used to write to the pre-rename
    # `dependents.json` filename. Make sure the legacy name isn't produced.
    assert not (work / "nodes" / "_index" / "dependents.json").exists()
    idx = json.loads(dependents_path.read_text())
    by_target = idx.get("by_target") or {}

    endpoint_id = "rc-api::routers/events.py::import_events_endpoint"
    assert endpoint_id in by_target, (
        f"endpoint missing from dependents: {sorted(by_target)}"
    )
    dependers = by_target[endpoint_id]
    dep_ids = [d["source"] for d in dependers]
    assert "rc-web::src/lib/api.ts:42::importEvent" in dep_ids


def test_reconcile_skips_route_call_with_mismatched_method(tmp_path):
    work = _setup_work(tmp_path)

    # Flip the route_call method to GET — should not match the POST endpoint.
    call_path = work / "nodes" / "route_calls" / "example_call.json"
    call = json.loads(call_path.read_text())
    call["signature"]["method"] = "GET"
    call_path.write_text(json.dumps(call))

    result = _run_reconcile(work)
    assert result.returncode == 0, (
        f"reconcile failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    idx = json.loads(
        (work / "nodes" / "_index" / "by_target.json").read_text()
    )
    by_target = idx.get("by_target") or {}
    endpoint_id = "rc-api::routers/events.py::import_events_endpoint"
    dependers = by_target.get(endpoint_id, [])
    dep_ids = [d["source"] for d in dependers]
    assert "rc-web::src/lib/api.ts:42::importEvent" not in dep_ids
