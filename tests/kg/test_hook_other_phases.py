"""Tests for the remaining hook phases: post-edit, session-end, pre-irreversible."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


def _make_graph_with_post_edit_script(
    parent: Path, name: str, marker_file: Path
) -> Path:
    """Build a graph with a vendored post_edit_regen script that touches a
    marker file when run."""
    g = parent / f"{name}-knowledge-graph"
    g.mkdir(parents=True)
    (g / "project.toml").write_text(
        f"""
[project]
name = "{name}"
subsystems = ["depgraph"]
source_roots = ["/tmp/x"]
"""
    )
    (g / "depgraph").mkdir()
    (g / "hooks").mkdir()
    script = g / "hooks" / "post_edit_regen_depgraph.py"
    script.write_text(
        f"""#!/usr/bin/env python3
from pathlib import Path
Path({str(marker_file)!r}).touch()
"""
    )
    script.chmod(0o755)
    return g


def _run_kg(
    *args: str, env: dict[str, str], stdin: str = ""
) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    full_env.update(env)
    return subprocess.run(
        [str(KG_BIN), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=full_env,
    )


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    return {"KG_REGISTRY_PATH": str(tmp_path / "kg-graphs.toml")}


# ---------- post-edit ----------


def test_post_edit_empty_registry_exits_0(env: dict[str, str]) -> None:
    result = _run_kg("hook", "post-edit", env=env)
    assert result.returncode == 0


def test_post_edit_runs_regen_per_subsystem(
    tmp_path: Path, env: dict[str, str]
) -> None:
    marker = tmp_path / "regen-ran"
    g = _make_graph_with_post_edit_script(tmp_path, "phi", marker)
    _run_kg("add", str(g), env=env)

    result = _run_kg("hook", "post-edit", env=env)
    assert result.returncode == 0
    assert marker.exists(), "post-edit regen script should have been invoked"


def test_post_edit_forwards_stdin_to_regen_script(
    tmp_path: Path, env: dict[str, str]
) -> None:
    """The Stop-hook payload (transcript_path, session_id, etc.) must be
    forwarded to subsystem scripts so they can find session edits."""
    capture = tmp_path / "captured-stdin.txt"
    g = tmp_path / "psi-knowledge-graph"
    g.mkdir(parents=True)
    (g / "project.toml").write_text(
        """
[project]
name = "psi"
subsystems = ["depgraph"]
source_roots = ["/tmp/x"]
"""
    )
    (g / "depgraph").mkdir()
    (g / "hooks").mkdir()
    script = g / "hooks" / "post_edit_regen_depgraph.py"
    script.write_text(
        f"""#!/usr/bin/env python3
import sys
from pathlib import Path
Path({str(capture)!r}).write_text(sys.stdin.read())
"""
    )
    script.chmod(0o755)
    _run_kg("add", str(g), env=env)

    payload = '{"session_id":"abc","transcript_path":"/tmp/t.jsonl"}'
    result = _run_kg("hook", "post-edit", env=env, stdin=payload)
    assert result.returncode == 0
    assert capture.exists()
    assert capture.read_text() == payload


def test_post_edit_continues_after_one_graph_regen_fails(
    tmp_path: Path, env: dict[str, str]
) -> None:
    marker = tmp_path / "good-marker"
    good = _make_graph_with_post_edit_script(tmp_path / "good", "good", marker)
    # Bad graph: regen script exits non-zero.
    bad = tmp_path / "bad" / "bad-knowledge-graph"
    bad.mkdir(parents=True)
    (bad / "project.toml").write_text(
        """
[project]
name = "bad"
subsystems = ["depgraph"]
source_roots = ["/tmp/x"]
"""
    )
    (bad / "depgraph").mkdir()
    (bad / "hooks").mkdir()
    bad_script = bad / "hooks" / "post_edit_regen_depgraph.py"
    bad_script.write_text("#!/usr/bin/env python3\nimport sys; sys.exit(99)\n")
    bad_script.chmod(0o755)

    _run_kg("add", str(good), env=env)
    _run_kg("add", str(bad), env=env)

    result = _run_kg("hook", "post-edit", env=env)
    assert result.returncode == 0
    assert marker.exists()  # good graph still ran


# ---------- session-end ----------


def test_session_end_empty_registry_exits_0(env: dict[str, str]) -> None:
    result = _run_kg("hook", "session-end", env=env)
    assert result.returncode == 0


# ---------- pre-irreversible ----------


def test_pre_irreversible_passes_stdin_to_script(env: dict[str, str]) -> None:
    """The pre-irreversible script is project-agnostic and shipped with the
    framework. The dispatcher should invoke it and forward stdin."""
    # The existing script lives at <TOOL_ROOT>/logigraph/hooks/pre_irreversible_inject.py.
    # The dispatcher will be configured to call it (or the migrated location).
    tool_input = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/test"}}
    )
    result = _run_kg("hook", "pre-irreversible", env=env, stdin=tool_input)
    assert result.returncode == 0
    # It may or may not emit content depending on the script's matchers,
    # but it should never crash.
