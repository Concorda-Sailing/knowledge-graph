"""Hook dispatcher: ``kg hook <phase>``.

Invoked by Claude Code (via ~/.claude/settings.json) **and** Grok
(via ~/.claude/settings.json or ~/.grok/hooks/*.json).

Reads the machine-local registry (~/.grok/kg-graphs.toml or ~/.claude/),
routes the hook to each registered graph as appropriate for the phase,
and emits a combined envelope on stdout.

The emitted shape uses the Claude/Grok-compatible
hookSpecificOutput + additionalContext convention for context injection
on PreToolUse / Stop.

Phases:

* ``session-start``    — fan to all graphs; run subsystem ``health`` per graph.
* ``pre-edit``         — dispatch by file path → owning graph's hook.
* ``post-edit``        — fan regen + telemetry to all graphs.
* ``session-end``      — fan memory-sync etc. to all graphs.
* ``pre-irreversible`` — project-agnostic; delegates to a standalone script.

Failure mode: a single graph's failure never blocks the hook. Errors are
surfaced inside the envelope; exit code is always 0.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from kg import project, registry


TOOL_ROOT = Path(__file__).resolve().parents[1]


# Single source of truth for hook phase names. Consumed by:
#   * ``kg.cli.orchestrator`` — argparse ``choices`` for ``kg hook <phase>``.
#   * ``kg.cli.install.hooks`` — commands emitted into Claude settings.json
#     and/or native Grok ~/.grok/hooks/ files.
#   * ``run()`` below — dispatch table.
# Adding a phase means: (1) add the name here, (2) add the handler here,
# (3) wire it into the installer's hook block. Tests in
# ``tests/kg/test_hook_phases_single_source.py`` catch drift.
HOOK_PHASES: tuple[str, ...] = (
    "pre-edit",
    "post-edit",
    "session-start",
    "session-end",
    "pre-irreversible",
)


def run(phase: str) -> int:
    """Entry point invoked by ``kg.cli``."""
    handler = _DISPATCH.get(phase)
    if handler is None:
        # argparse should prevent this, but be safe.
        _emit("UnknownHook", f"Unknown hook phase: {phase}")
        return 0
    return handler()


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------


def _emit(event_name: str, body: str) -> None:
    """Print a hook envelope understood by both Claude Code and Grok.

    Both agents support the hookSpecificOutput + additionalContext shape
    for injecting text into the model's context (especially on PreToolUse).
    """
    payload = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": body,
        }
    }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# session-start: run health per subsystem per registered graph.
# ---------------------------------------------------------------------------


def _resolve_subsystem_bin(graph_dir: Path, subsystem: str) -> Optional[Path]:
    """Find the binary for ``<subsystem>`` for this graph.

    Order:
      1. ``<graph>/bin/<subsystem>`` — vendored binary (post-migration shape).
      2. ``<TOOL_ROOT>/<subsystem>/bin/<subsystem>`` — framework-global
         binary (migration fallback, used by graphs that haven't been
         vendored yet).
    Returns None if neither exists.
    """
    vendored = graph_dir / "bin" / subsystem
    if vendored.exists():
        return vendored
    framework = TOOL_ROOT / subsystem / "bin" / subsystem
    if framework.exists():
        return framework
    return None


def _data_dir_env_var(subsystem: str) -> str:
    return f"{subsystem.upper()}_DATA_DIR"


def _run_health(subsystem: str, graph_dir: Path) -> tuple[bool, str]:
    """Run ``<binary> health`` for one subsystem in one graph.

    Returns (had_problem, rendered_output).
    """
    binary = _resolve_subsystem_bin(graph_dir, subsystem)
    if binary is None:
        return True, (
            f"  ⚠ {subsystem} binary missing (looked in {graph_dir}/bin/ and "
            f"framework {subsystem}/bin/). "
            f"Run `kg upgrade` once that command exists."
        )

    data_dir = graph_dir / subsystem
    if not data_dir.exists():
        return True, f"  ⚠ {subsystem} data dir missing at {data_dir}"

    env = os.environ.copy()
    env[_data_dir_env_var(subsystem)] = str(data_dir)
    # Some subsystems want the sibling subsystem's data dir too (logigraph
    # claims against depgraph). Pass both when available.
    sibling_subs = ("depgraph", "logigraph")
    for other in sibling_subs:
        other_dir = graph_dir / other
        if other_dir.exists():
            env.setdefault(_data_dir_env_var(other), str(other_dir))

    try:
        proc = subprocess.run(
            [str(binary), "health"],
            cwd=str(data_dir),
            env=env,
            capture_output=True,
            text=True,
            # Headroom for a fully-populated corpus on a cold cache. `health`
            # itself is near-linear now (compiled validator + single walk),
            # but a large graph + contended IO can still exceed a tight bound;
            # 60s keeps a healthy graph from reporting a false "failed to
            # launch" at SessionStart.
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return True, f"  ⚠ {subsystem} health failed to launch: {exc}"

    out = (proc.stdout or "") + (proc.stderr or "")
    return (proc.returncode != 0), out.rstrip()


def _recent_cascade_issues(subsystem_dir: Path, hours: int = 24) -> list[dict]:
    """Read recent entries from ``<subsystem_dir>/telemetry/cascade-issues.jsonl``.

    Returns at most the 10 most recent issues newer than ``hours`` old.
    Silent on read errors.
    """
    import datetime as _dt

    log = subsystem_dir / "telemetry" / "cascade-issues.jsonl"
    if not log.exists():
        return []
    try:
        content = log.read_text()
    except OSError:
        return []

    cutoff = _dt.datetime.utcnow() - _dt.timedelta(hours=hours)
    recent: list[dict] = []
    for raw in content.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            ev = json.loads(raw)
            ts = _dt.datetime.strptime(ev.get("ts", ""), "%Y-%m-%dT%H:%M:%SZ")
        except (json.JSONDecodeError, ValueError):
            continue
        if ts < cutoff:
            continue
        recent.append(ev)
    return recent[-10:]


def _check_graph_health(graph_dir: Path) -> tuple[bool, str]:
    """Run health for every subsystem declared in the graph's project.toml.

    Also surfaces unaddressed cascade failures from each subsystem's
    ``telemetry/cascade-issues.jsonl``.

    Returns (any_problems, rendered_block).
    """
    try:
        proj = project.load(graph_dir)
    except (FileNotFoundError, ValueError) as exc:
        return True, f"## {graph_dir.name}\n  ⚠ Could not load project.toml: {exc}\n"

    lines = [f"## {proj.name}"]
    any_problem = False
    for subsystem in proj.subsystems:
        had_problem, block = _run_health(subsystem, graph_dir)
        if block:
            lines.append(block)
        if had_problem:
            any_problem = True

    issue_lines: list[str] = []
    for subsystem in proj.subsystems:
        sub_dir = graph_dir / subsystem
        recent = _recent_cascade_issues(sub_dir)
        if not recent:
            continue
        issue_lines.append(f"### Cascade issues in {subsystem} (last 24h)")
        for ev in recent:
            issue_lines.append(
                f"- [{ev.get('ts','?')}] **{ev.get('kind','?')}** "
                f"from `{ev.get('target_repo','?')}@{ev.get('target_sha','?')}`: "
                f"{ev.get('message','?')}"
            )
    if issue_lines:
        any_problem = True
        lines.append("\n## ⚠ Unaddressed cascade failures\n")
        lines.extend(issue_lines)
        lines.append(
            "\n_Address with the user: investigate root cause, propose a fix, "
            "and clear the log when resolved (`> telemetry/cascade-issues.jsonl`)._"
        )

    return any_problem, "\n".join(lines) + "\n"


def _session_start() -> int:
    entries = registry.load()
    header = "# 🩺 Knowledge graph health (session start)"

    if not entries:
        _emit(
            "SessionStart",
            header
            + "\n\n_No graphs registered. Use `kg add <path>` to register one._",
        )
        return 0

    blocks: list[str] = []
    any_problem = False
    for entry in entries:
        if not entry.path.exists():
            blocks.append(f"## {entry.name}\n  (skipped — path missing: {entry.path})")
            any_problem = True
            continue
        problem, block = _check_graph_health(entry.path)
        any_problem = any_problem or problem
        blocks.append(block)

    body = header + "\n\n" + "\n".join(blocks)
    if any_problem:
        body += (
            "\n_⚠ Knowledge graph has out-of-date items. "
            "Address before edits that depend on accurate context._"
        )
    else:
        body += (
            "\n_All graphs clean. Health is checked on session start; "
            "run `<subsystem> health` anytime to recheck._"
        )

    _emit("SessionStart", body)
    return 0


# ---------------------------------------------------------------------------
# pre-edit: dispatch by file path to owning graph's inject scripts.
# ---------------------------------------------------------------------------


def _extract_file_path(tool_input: dict) -> Optional[str]:
    """Pull the touched file path from Edit/Write/MultiEdit input.

    All three tools nest the path under ``tool_input.file_path``.
    """
    ti = tool_input.get("tool_input") or {}
    fp = ti.get("file_path")
    if isinstance(fp, str) and fp:
        return fp
    return None


def _resolve_inject_script(
    graph_dir: Path, subsystem: str
) -> Optional[Path]:
    """Find the pre-edit inject script for this (graph, subsystem) pair.

    Order:
      1. ``<graph>/hooks/pre_edit_inject_<subsystem>.py`` — vendored.
      2. ``<TOOL_ROOT>/<subsystem>/hooks/pre_edit_inject.py`` — framework
         fallback while graphs are still un-vendored.
    """
    vendored = graph_dir / "hooks" / f"pre_edit_inject_{subsystem}.py"
    if vendored.exists():
        return vendored
    framework = TOOL_ROOT / subsystem / "hooks" / "pre_edit_inject.py"
    if framework.exists():
        return framework
    return None


def _run_inject_script(
    graph_dir: Path, subsystem: str, stdin_payload: str
) -> Optional[str]:
    """Run the inject script and return its additionalContext text.

    Returns None if the script is missing or fails to produce a valid
    envelope. Failures are swallowed (logged into the merged output by
    the caller); the hook layer never blocks edits.
    """
    script = _resolve_inject_script(graph_dir, subsystem)
    if script is None:
        return None

    data_dir = graph_dir / subsystem
    env = os.environ.copy()
    env[_data_dir_env_var(subsystem)] = str(data_dir)
    for other in ("depgraph", "logigraph"):
        other_dir = graph_dir / other
        if other_dir.exists():
            env.setdefault(_data_dir_env_var(other), str(other_dir))

    try:
        proc = subprocess.run(
            ["python3", str(script)],
            input=stdin_payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if proc.returncode != 0 or not proc.stdout.strip():
        return None

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None

    out = payload.get("hookSpecificOutput") or {}
    ctx = out.get("additionalContext")
    if isinstance(ctx, str) and ctx.strip():
        return ctx
    return None


def _pre_edit() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        # No input means nothing to dispatch on. Silent exit.
        return 0

    try:
        tool_input = json.loads(raw)
    except json.JSONDecodeError:
        # Bad input from the harness — surface a one-liner, never block.
        _emit("PreToolUse", "_kg hook pre-edit: stdin was not valid JSON._")
        return 0

    file_path = _extract_file_path(tool_input)
    if not file_path:
        # Not an edit-shaped tool call; nothing to do.
        return 0

    entries = registry.load()
    if not entries:
        return 0

    target = Path(file_path).expanduser()

    blocks: list[str] = []
    for entry in entries:
        if not entry.path.exists():
            continue
        try:
            proj = project.load(entry.path)
        except (FileNotFoundError, ValueError):
            continue
        if not proj.owns(target):
            continue
        for subsystem in proj.subsystems:
            ctx = _run_inject_script(entry.path, subsystem, raw)
            if ctx:
                blocks.append(ctx.rstrip())

    if not blocks:
        return 0

    _emit("PreToolUse", "\n\n---\n\n".join(blocks))
    return 0


# ---------------------------------------------------------------------------
# post-edit: fan regen + telemetry per (graph, subsystem). No envelope output.
# ---------------------------------------------------------------------------


_POST_EDIT_SCRIPT_NAMES = ("post_edit_regen", "post_edit_telemetry")


def _resolve_phase_script(
    graph_dir: Path, subsystem: str, script_name: str
) -> Optional[Path]:
    """Find a phase script. Same vendored-then-framework order as inject."""
    vendored = graph_dir / "hooks" / f"{script_name}_{subsystem}.py"
    if vendored.exists():
        return vendored
    framework = TOOL_ROOT / subsystem / "hooks" / f"{script_name}.py"
    if framework.exists():
        return framework
    return None


def _run_phase_script(
    graph_dir: Path,
    subsystem: str,
    script_name: str,
    stdin_payload: str = "",
) -> None:
    """Run a phase script for one (graph, subsystem). Output ignored.

    ``stdin_payload`` is forwarded so scripts that consume the Claude Code
    Stop-hook payload (transcript_path, session_id, etc.) work correctly.
    """
    script = _resolve_phase_script(graph_dir, subsystem, script_name)
    if script is None:
        return
    env = os.environ.copy()
    env[_data_dir_env_var(subsystem)] = str(graph_dir / subsystem)
    for other in ("depgraph", "logigraph"):
        other_dir = graph_dir / other
        if other_dir.exists():
            env.setdefault(_data_dir_env_var(other), str(other_dir))
    try:
        subprocess.run(
            ["python3", str(script)],
            input=stdin_payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def _post_edit() -> int:
    # Claude Code / Grok send a Stop-hook payload (session_id, transcript_path, etc.)
    # on stdin. Forward it verbatim to each subsystem's regen/telemetry script
    # so they can find the session transcript.
    stdin_payload = sys.stdin.read()
    for entry in registry.load():
        if not entry.path.exists():
            continue
        try:
            proj = project.load(entry.path)
        except (FileNotFoundError, ValueError):
            continue
        for subsystem in proj.subsystems:
            for script_name in _POST_EDIT_SCRIPT_NAMES:
                _run_phase_script(
                    entry.path, subsystem, script_name, stdin_payload
                )
    return 0


# ---------------------------------------------------------------------------
# session-end: per-graph housekeeping (currently depgraph memory-sync).
# ---------------------------------------------------------------------------


# Per-subsystem session-end commands. The dispatcher invokes
# ``<subsystem-binary> <args>`` for each. Subsystems without an entry
# get nothing — that's intentional.
_SESSION_END_COMMANDS: dict[str, list[str]] = {
    "depgraph": ["memory-sync"],
}


def _session_end() -> int:
    for entry in registry.load():
        if not entry.path.exists():
            continue
        try:
            proj = project.load(entry.path)
        except (FileNotFoundError, ValueError):
            continue
        for subsystem in proj.subsystems:
            args = _SESSION_END_COMMANDS.get(subsystem)
            if not args:
                continue
            binary = _resolve_subsystem_bin(entry.path, subsystem)
            if binary is None:
                continue
            env = os.environ.copy()
            env[_data_dir_env_var(subsystem)] = str(entry.path / subsystem)
            try:
                subprocess.run(
                    [str(binary), *args],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30,
                )
            except (OSError, subprocess.SubprocessError):
                pass
    return 0


# ---------------------------------------------------------------------------
# pre-irreversible: project-agnostic; forwards stdin to the framework script.
# ---------------------------------------------------------------------------


def _resolve_pre_irreversible_script() -> Optional[Path]:
    """Find the project-agnostic pre-irreversible script.

    Post-migration location: ``<TOOL_ROOT>/hooks/pre_irreversible.py``.
    Current location: ``<TOOL_ROOT>/logigraph/hooks/pre_irreversible_inject.py``.
    """
    new_loc = TOOL_ROOT / "hooks" / "pre_irreversible.py"
    if new_loc.exists():
        return new_loc
    legacy = TOOL_ROOT / "logigraph" / "hooks" / "pre_irreversible_inject.py"
    if legacy.exists():
        return legacy
    return None


def _pre_irreversible() -> int:
    script = _resolve_pre_irreversible_script()
    if script is None:
        return 0
    stdin_data = sys.stdin.read()
    try:
        proc = subprocess.run(
            ["python3", str(script)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    return 0


# ---------------------------------------------------------------------------
# Dispatch table — keyed on HOOK_PHASES so adding a phase here forces a
# matching entry in HOOK_PHASES (the test suite asserts the two agree).
# ---------------------------------------------------------------------------

_DISPATCH: dict[str, "callable"] = {
    "pre-edit": _pre_edit,
    "post-edit": _post_edit,
    "session-start": _session_start,
    "session-end": _session_end,
    "pre-irreversible": _pre_irreversible,
}
