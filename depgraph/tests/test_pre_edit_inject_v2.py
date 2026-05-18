"""End-to-end tests for hooks/pre_edit_inject.py against a v2 corpus.

The hook is a stdin-driven CLI script: Claude Code feeds it a JSON Edit
payload, the hook resolves the touched file to tracked nodes, renders
dossier + dependents, and writes a `hookSpecificOutput` envelope to
stdout. These tests build a synthetic v2 corpus on disk, invoke the
hook with DEPGRAPH_DATA_DIR set, and inspect the rendered envelope.

Covers Phase 6.2 acceptance:
  • v2 schema_version=2 nodes load correctly.
  • _index/by_target.json (flat dict, no schema_version wrapper) is read.
  • _meta.json validation_report counts surface as banners.
  • Dossier path is computed from kind/primitive + slug, not a stored field.
  • v1 nodes are rejected with a schema-version-mismatch banner.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre_edit_inject.py"
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]


def _write_node(data_dir: Path, kind_dir: str, slug: str, data: dict) -> Path:
    out = data_dir / "nodes" / kind_dir / f"{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True))
    return out


def _write_meta(data_dir: Path, **overrides) -> None:
    meta = {
        "schema_version": 2,
        "regen_status": "complete",
        "generated_at": "2026-05-17T00:00:00+00:00",
        "primitive_count": 0,
        "edge_count": 0,
        "orphan_edge_count": 0,
        "slug_collision_count": 0,
        "primitive_error_count": 0,
        "validation_report": {
            "orphan_edges": [],
            "primitive_errors": [],
            "slug_collisions": [],
        },
    }
    meta.update(overrides)
    p = data_dir / "nodes" / "_meta.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta, indent=2))


def _write_index(data_dir: Path, by_target: dict[str, list[dict]]) -> None:
    p = data_dir / "nodes" / "_index" / "by_target.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(by_target, indent=2, sort_keys=True))


def _write_project_toml(data_dir: Path, repo_path: Path) -> None:
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "synth"\n'
        f'[repos.app]\npath = "{repo_path}"\n'
    )


def _make_node(repo: str, rel: str, primitive: str, name: str, *, kind=None) -> dict:
    nid = f"{repo}::{rel}::{name}" if name else f"{repo}::{rel}"
    return {
        "schema_version": 2,
        "id": nid,
        "primitive": primitive,
        "name": name or rel,
        "owner": None,
        "source": {
            "repo": repo, "path": rel, "language": "python",
            "line": 1, "end_line": 10,
        },
        "signature": {},
        "attributes": {
            "abstract": False, "generated": False, "external": False,
            "template_parameters": [], "macro": False, "mutable": True,
            "instantiable": False, "inheritable": False,
        },
        "edges_out": [],
        "structural_hash": "deadbeef" * 8,
        "kind": kind,
        "extractor": "test",
    }


def _run_hook(data_dir: Path, payload: dict) -> dict:
    env = {**os.environ,
           "DEPGRAPH_DATA_DIR": str(data_dir),
           "PYTHONPATH": str(FRAMEWORK_ROOT)}
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, (
        f"hook exited {result.returncode}: stderr={result.stderr!r}"
    )
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


@pytest.fixture
def repo(tmp_path):
    """Repo directory the [repos.app] table will point at.

    Dir name is intentionally different from the repo key ("app") to
    confirm the hook looks up by [repos.<key>] table name (matching what
    the v2 extractors write into source.repo), not by directory basename."""
    r = tmp_path / "checkout-dir"
    (r / "services").mkdir(parents=True)
    (r / "services" / "users.py").write_text("def get_user(): pass\n")
    return r


@pytest.fixture
def data_dir(tmp_path, repo):
    """Minimal v2 data dir: project.toml + nodes/ + _meta.json + by_target.json."""
    dd = tmp_path / "graph"
    (dd / "nodes").mkdir(parents=True)
    _write_project_toml(dd, repo)
    _write_meta(dd)
    _write_index(dd, {})
    return dd


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_tracked_file_renders_node_block(data_dir, repo):
    node = _make_node("app", "services/users.py", "function", "get_user",
                      kind="service")
    _write_node(data_dir, "services", "app__services_users_py__get_user", node)
    _write_meta(data_dir, primitive_count=1)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "get_user" in body
    assert "**kind:** service" in body
    assert "app::services/users.py::get_user" in body


def test_unified_kind_renders_primitive_value(data_dir, repo):
    """When no classifier fires, the writer sets kind = primitive (unified
    taxonomy — there is no `kind: null`). The hook header reads kind
    directly; no primitive-fallback needed."""
    node = _make_node("app", "services/users.py", "function", "get_user")
    # Simulate writer's behaviour: unclassified node lands with kind=primitive.
    node["kind"] = node["primitive"]
    _write_node(data_dir, "functions", "app__services_users_py__get_user", node)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "**kind:** function" in body, body[:500]


def test_dependents_index_v2_shape_renders_callers(data_dir, repo):
    """v2 by_target.json is a flat {target_id: [...]} dict (no
    schema_version wrapper). The hook reads it as-is."""
    callee = _make_node("app", "services/users.py", "function", "get_user",
                        kind="service")
    _write_node(data_dir, "services", "app__services_users_py__get_user", callee)
    _write_index(data_dir, {
        callee["id"]: [{
            "source": "app::routers/users.py::list_users",
            "kind": "calls", "via": "function_call",
            "where": "routers/users.py:42", "confidence": "exact",
        }],
    })

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "Verified callers" in body
    assert "list_users" in body
    assert "routers/users.py:42" in body
    # New Edge column surfaces the v2 edge kind alongside Via.
    assert "| calls |" in body


# ---------------------------------------------------------------------------
# Status banners from _meta validation_report
# ---------------------------------------------------------------------------

def test_regen_in_progress_banner(data_dir, repo):
    _write_meta(data_dir, regen_status="in_progress")
    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "torn state" in body
    assert "in_progress" in body


def test_primitive_error_count_banner(data_dir, repo):
    _write_meta(data_dir, primitive_error_count=3)
    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "3 primitive validation error" in body


def test_slug_collision_banner(data_dir, repo):
    _write_meta(data_dir, slug_collision_count=2)
    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "2 slug collision" in body


def test_missing_meta_emits_banner(data_dir, repo):
    """Delete _meta.json; the hook should still warn the user (graph state
    unknown) rather than silently rendering an empty injection."""
    (data_dir / "nodes" / "_meta.json").unlink()
    node = _make_node("app", "services/users.py", "function", "get_user",
                      kind="service")
    _write_node(data_dir, "services", "app__services_users_py__get_user", node)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "Corpus metadata missing" in body


# ---------------------------------------------------------------------------
# Schema-version gate
# ---------------------------------------------------------------------------

def test_v1_node_is_rejected_with_banner(data_dir, repo):
    """A node with schema_version=1 in a v2 corpus is skipped and surfaced."""
    v1 = _make_node("app", "services/users.py", "function", "get_user",
                    kind="service")
    v1["schema_version"] = 1
    _write_node(data_dir, "services", "app__services_users_py__get_user", v1)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "schema_version mismatch" in body
    assert "1 node(s) skipped" in body


# ---------------------------------------------------------------------------
# Dossier path resolution
# ---------------------------------------------------------------------------

def test_dossier_picked_up_from_kind_dir(data_dir, repo):
    node = _make_node("app", "services/users.py", "function", "get_user",
                      kind="service")
    _write_node(data_dir, "services", "app__services_users_py__get_user", node)
    dossier = data_dir / "dossiers" / "services" / "app__services_users_py__get_user.md"
    dossier.parent.mkdir(parents=True, exist_ok=True)
    dossier.write_text("# Purpose\n\nReturns a user by id.\n")

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "Returns a user by id" in body


def test_dossier_missing_emits_stub_message(data_dir, repo):
    node = _make_node("app", "services/users.py", "function", "get_user",
                      kind="service")
    _write_node(data_dir, "services", "app__services_users_py__get_user", node)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "No dossier yet" in body


# ---------------------------------------------------------------------------
# File not tracked
# ---------------------------------------------------------------------------

def test_untracked_file_emits_explainer(data_dir, repo):
    """Editing a file not covered by the extractor still produces a block
    explaining the absence, so the agent isn't left wondering why nothing
    fired."""
    other = repo / "services" / "untracked.py"
    other.write_text("# new file\n")

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(other)},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "No tracked nodes" in body


def test_injection_respects_max_bytes_budget(data_dir, repo):
    """High-fan-in files would otherwise pour 100+ KB into the conversation.
    Setting `[depgraph].max_injection_bytes` clamps the body and surfaces a
    truncation marker so the user knows nodes were dropped (#17)."""
    # Override project.toml to set a tiny budget.
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "synth"\n\n'
        f'[depgraph]\nmax_injection_bytes = 2000\n\n'
        f'[repos.app]\npath = "{repo}"\n'
    )
    # Plant a dozen function nodes on the same file so the hook will iterate
    # many blocks; the budget should stop after the first 1-2 fit.
    for i in range(12):
        name = f"handler_{i}"
        node = _make_node("app", "services/users.py", "function", name,
                          kind="service")
        _write_node(data_dir, "services",
                    f"app__services_users_py__{name}", node)
    _write_meta(data_dir, primitive_count=12)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    # Truncation marker must mention how many nodes were skipped.
    assert "additional node" in body
    assert "max_injection_bytes" in body
    # Body should be bounded by the budget (with a small slack for the
    # footer). 12 full node blocks at ~300 bytes each would be ~3.6KB.
    assert len(body) < 4000, f"body too big: {len(body)} bytes"


def test_injection_no_budget_marker_when_under_threshold(data_dir, repo):
    """A single small node should fit comfortably in the default budget;
    no truncation marker should appear."""
    node = _make_node("app", "services/users.py", "function", "get_user",
                      kind="service")
    _write_node(data_dir, "services", "app__services_users_py__get_user", node)
    _write_meta(data_dir, primitive_count=1)

    envelope = _run_hook(data_dir, {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "services" / "users.py")},
    })
    body = envelope["hookSpecificOutput"]["additionalContext"]
    assert "max_injection_bytes" not in body
