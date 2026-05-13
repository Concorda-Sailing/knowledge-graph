"""Integration test: reconcile.py joins route_call nodes against endpoint
nodes and writes the cross-repo edge to dependents.json."""
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


def test_reconcile_emits_route_call_dependent(tmp_path):
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)

    result = _run_reconcile(work)
    assert result.returncode == 0, (
        f"reconcile failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    dependents_path = work / "nodes" / "_index" / "dependents.json"
    assert dependents_path.exists(), "reconcile did not write dependents.json"
    idx = json.loads(dependents_path.read_text())
    by_target = idx.get("by_target") or {}

    endpoint_id = "rc-api::routers/events.py::import_events_endpoint"
    assert endpoint_id in by_target, (
        f"endpoint missing from dependents: {sorted(by_target)}"
    )
    dependers = by_target[endpoint_id]
    dep_ids = [d["id"] for d in dependers]
    assert "rc-web::src/lib/api.ts:42::importEvent" in dep_ids


def test_reconcile_skips_route_call_with_mismatched_method(tmp_path):
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)

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
        (work / "nodes" / "_index" / "dependents.json").read_text()
    )
    by_target = idx.get("by_target") or {}
    endpoint_id = "rc-api::routers/events.py::import_events_endpoint"
    dependers = by_target.get(endpoint_id, [])
    dep_ids = [d["id"] for d in dependers]
    assert "rc-web::src/lib/api.ts:42::importEvent" not in dep_ids
