"""Integration test for `kg hook session-start`.

Spins up a fake graph repo with a stub subsystem binary that returns
known output, registers it, and verifies the SessionStart envelope.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


def _make_fake_graph(parent: Path, name: str, subsystem_outputs: dict[str, str]) -> Path:
    """Make a graph repo with stub binaries that print fixed health output.

    subsystem_outputs maps subsystem name -> the text the stub `health` prints.
    """
    g = parent / f"{name}-knowledge-graph"
    g.mkdir(parents=True)
    subsystems = list(subsystem_outputs.keys())
    sublist = ", ".join(f'"{s}"' for s in subsystems)
    (g / "project.toml").write_text(
        f"""
[project]
name = "{name}"
subsystems = [{sublist}]
source_roots = ["/tmp/fake-src"]
"""
    )
    bin_dir = g / "bin"
    bin_dir.mkdir()
    for sub, out in subsystem_outputs.items():
        # Create a data dir for the subsystem (real graphs have these).
        (g / sub).mkdir()
        # Each stub binary echoes the captured `out` when called with `health`.
        # Anything else exits 0 with empty output.
        stub = bin_dir / sub
        stub.write_text(
            f"""#!/usr/bin/env bash
if [ "$1" = "health" ]; then
  cat <<'EOF'
{out}
EOF
fi
"""
        )
        stub.chmod(0o755)
    return g


def _run_kg(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    full_env.update(env)
    return subprocess.run(
        [str(KG_BIN), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    return {"KG_REGISTRY_PATH": str(tmp_path / "kg-graphs.toml")}


def test_session_start_empty_registry_emits_noop_envelope(
    env: dict[str, str],
) -> None:
    """With nothing registered, exit 0 and emit a valid envelope."""
    result = _run_kg("hook", "session-start", env=env)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "no graphs" in ctx.lower() or "0" in ctx or "knowledge graph" in ctx.lower()


def test_session_start_runs_health_per_subsystem(
    tmp_path: Path, env: dict[str, str]
) -> None:
    g = _make_fake_graph(
        tmp_path,
        "alpha",
        {
            "depgraph": "✓ clean\n  tier-A coverage: 100% (50/50)",
            "logigraph": "✓ clean\n  rules: 12",
        },
    )
    assert _run_kg("add", str(g), env=env).returncode == 0

    result = _run_kg("hook", "session-start", env=env)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "alpha" in ctx
    assert "tier-A coverage" in ctx
    assert "rules: 12" in ctx


def test_session_start_warns_on_missing_binary(
    tmp_path: Path, env: dict[str, str]
) -> None:
    """A registered graph with no bin/<subsystem> surfaces a visible warning,
    not a crash."""
    g = tmp_path / "broken-knowledge-graph"
    g.mkdir()
    (g / "project.toml").write_text(
        """
[project]
name = "broken"
subsystems = ["depgraph"]
source_roots = ["/tmp/x"]
"""
    )
    assert _run_kg("add", str(g), env=env).returncode == 0

    result = _run_kg("hook", "session-start", env=env)
    assert result.returncode == 0  # never blocks
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "broken" in ctx
    assert "missing" in ctx.lower() or "not found" in ctx.lower()


def test_session_start_continues_after_one_graph_fails(
    tmp_path: Path, env: dict[str, str]
) -> None:
    """If graph A fails but graph B succeeds, both appear in the envelope."""
    good = _make_fake_graph(
        tmp_path / "good-parent",
        "good",
        {"depgraph": "✓ clean"},
    )
    bad = tmp_path / "bad-parent" / "bad-knowledge-graph"
    bad.mkdir(parents=True)
    (bad / "project.toml").write_text(
        """
[project]
name = "bad"
subsystems = ["depgraph"]
source_roots = ["/tmp/x"]
"""
    )
    _run_kg("add", str(good), env=env)
    _run_kg("add", str(bad), env=env)

    result = _run_kg("hook", "session-start", env=env)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "good" in ctx
    assert "bad" in ctx
