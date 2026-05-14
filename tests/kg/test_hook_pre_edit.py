"""Integration tests for `kg hook pre-edit`.

The dispatcher reads a Claude Code Edit/Write tool input from stdin,
finds which registered graphs own the touched file (by source_roots),
and shells out to each (graph, subsystem) pair's inject script.

Tests use a fake graph with stub inject scripts that emit known envelopes.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


def _make_graph_with_inject(
    parent: Path,
    name: str,
    source_root: Path,
    subsystem_messages: dict[str, str],
) -> Path:
    """Build a graph with subsystems whose vendored inject script
    emits a fixed envelope for testing."""
    g = parent / f"{name}-knowledge-graph"
    g.mkdir(parents=True)
    subsystems = list(subsystem_messages.keys())
    sublist = ", ".join(f'"{s}"' for s in subsystems)
    (g / "project.toml").write_text(
        f"""
[project]
name = "{name}"
subsystems = [{sublist}]
source_roots = ["{source_root}"]
"""
    )
    hooks_dir = g / "hooks"
    hooks_dir.mkdir()
    for sub, msg in subsystem_messages.items():
        (g / sub).mkdir()
        script = hooks_dir / f"pre_edit_inject_{sub}.py"
        script.write_text(
            f"""#!/usr/bin/env python3
import json, sys
sys.stdin.read()
payload = {{
    "hookSpecificOutput": {{
        "hookEventName": "PreToolUse",
        "additionalContext": {json.dumps(msg)}
    }}
}}
print(json.dumps(payload))
"""
        )
        script.chmod(0o755)
    return g


def _run_pre_edit(
    file_path: str, env: dict[str, str]
) -> subprocess.CompletedProcess:
    stdin = json.dumps(
        {"tool_name": "Edit", "tool_input": {"file_path": file_path}}
    )
    full_env = dict(os.environ)
    full_env.update(env)
    return subprocess.run(
        [str(KG_BIN), "hook", "pre-edit"],
        input=stdin,
        capture_output=True,
        text=True,
        env=full_env,
    )


def _run_kg(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    full_env.update(env)
    return subprocess.run(
        [str(KG_BIN), *args], capture_output=True, text=True, env=full_env
    )


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    return {"KG_REGISTRY_PATH": str(tmp_path / "kg-graphs.toml")}


def test_pre_edit_empty_registry_exits_0(env: dict[str, str]) -> None:
    result = _run_pre_edit("/tmp/anything", env=env)
    assert result.returncode == 0


def test_pre_edit_file_not_in_any_source_root(
    tmp_path: Path, env: dict[str, str]
) -> None:
    """A file outside all source_roots produces no injection but still exits 0."""
    src = tmp_path / "src"
    src.mkdir()
    g = _make_graph_with_inject(
        tmp_path, "alpha", src, {"depgraph": "this should not appear"}
    )
    _run_kg("add", str(g), env=env)

    other_file = tmp_path / "elsewhere" / "x.py"
    result = _run_pre_edit(str(other_file), env=env)
    assert result.returncode == 0
    # Either empty stdout or an envelope with no graph-injected content.
    if result.stdout.strip():
        ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "this should not appear" not in ctx


def test_pre_edit_dispatches_to_matching_graph(
    tmp_path: Path, env: dict[str, str]
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    g = _make_graph_with_inject(
        tmp_path,
        "beta",
        src,
        {"depgraph": "DEPGRAPH-CONTEXT-FOR-BETA"},
    )
    _run_kg("add", str(g), env=env)

    edited_file = src / "deep" / "nested" / "file.py"
    edited_file.parent.mkdir(parents=True)
    edited_file.touch()

    result = _run_pre_edit(str(edited_file), env=env)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "DEPGRAPH-CONTEXT-FOR-BETA" in ctx


def test_pre_edit_runs_all_subsystems_for_matched_graph(
    tmp_path: Path, env: dict[str, str]
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    g = _make_graph_with_inject(
        tmp_path,
        "gamma",
        src,
        {
            "depgraph": "DEP-MARKER",
            "logigraph": "LOGI-MARKER",
        },
    )
    _run_kg("add", str(g), env=env)

    f = src / "x.py"
    f.touch()
    result = _run_pre_edit(str(f), env=env)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "DEP-MARKER" in ctx
    assert "LOGI-MARKER" in ctx


def test_pre_edit_fans_to_multiple_owning_graphs(
    tmp_path: Path, env: dict[str, str]
) -> None:
    shared = tmp_path / "shared-lib"
    shared.mkdir()
    g1 = _make_graph_with_inject(
        tmp_path / "p1", "first", shared, {"depgraph": "FIRST-CTX"}
    )
    g2 = _make_graph_with_inject(
        tmp_path / "p2", "second", shared, {"depgraph": "SECOND-CTX"}
    )
    _run_kg("add", str(g1), env=env)
    _run_kg("add", str(g2), env=env)

    f = shared / "thing.py"
    f.touch()
    result = _run_pre_edit(str(f), env=env)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "FIRST-CTX" in ctx
    assert "SECOND-CTX" in ctx


def test_pre_edit_continues_when_one_subsystem_inject_fails(
    tmp_path: Path, env: dict[str, str]
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    g = _make_graph_with_inject(
        tmp_path, "delta", src, {"depgraph": "GOOD-CTX"}
    )
    # Add a logigraph subsystem with a broken script.
    (g / "logigraph").mkdir()
    broken = g / "hooks" / "pre_edit_inject_logigraph.py"
    broken.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(99)\n")
    broken.chmod(0o755)
    # Update project.toml to declare both.
    (g / "project.toml").write_text(
        f"""
[project]
name = "delta"
subsystems = ["depgraph", "logigraph"]
source_roots = ["{src}"]
"""
    )
    _run_kg("add", str(g), env=env)

    f = src / "x.py"
    f.touch()
    result = _run_pre_edit(str(f), env=env)
    assert result.returncode == 0  # never blocks
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "GOOD-CTX" in ctx


def test_pre_edit_handles_invalid_stdin(env: dict[str, str]) -> None:
    full_env = dict(os.environ)
    full_env.update(env)
    result = subprocess.run(
        [str(KG_BIN), "hook", "pre-edit"],
        input="not valid json",
        capture_output=True,
        text=True,
        env=full_env,
    )
    assert result.returncode == 0  # never blocks even on bad input
