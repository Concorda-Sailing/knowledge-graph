"""HOOK_PHASES is the single source of truth for hook phase names.

These tests catch drift between:
* ``kg.hook.HOOK_PHASES`` (the declared tuple),
* ``kg.cli.orchestrator``'s argparse ``choices`` for ``kg hook <phase>``, and
* ``kg.cli.install.hooks._hook_block`` (the commands emitted into Claude
  Code's ``settings.json``).

If a future phase is added in one place but not the others, one of these
tests fails — instead of a silent "valid CLI phase that does nothing" or
"installed hook with no handler".
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kg import hook
from kg.cli import orchestrator
from kg.cli.install.hooks import _hook_block


EXPECTED_PHASES = (
    "pre-edit",
    "post-edit",
    "session-start",
    "session-end",
    "pre-irreversible",
)


def test_hook_phases_constant_exists_and_is_tuple() -> None:
    """``kg.hook`` exposes ``HOOK_PHASES`` as an immutable tuple of names."""
    assert hasattr(hook, "HOOK_PHASES")
    assert isinstance(hook.HOOK_PHASES, tuple)
    # Names are non-empty strings.
    for name in hook.HOOK_PHASES:
        assert isinstance(name, str) and name


def test_hook_phases_matches_expected_set() -> None:
    """The current shipped phase set is exactly these five names."""
    assert set(hook.HOOK_PHASES) == set(EXPECTED_PHASES)


def test_orchestrator_argparse_choices_match_hook_phases() -> None:
    """The argparse ``choices`` for ``kg hook <phase>`` is exactly HOOK_PHASES.

    Builds the same parser ``kg.cli`` builds and finds the ``hook``
    subparser's ``phase`` argument.
    """
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    orchestrator.register_alias(sub)

    # Find the `hook` subparser.
    subparsers_action = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    hook_parser = subparsers_action.choices["hook"]

    phase_action = next(a for a in hook_parser._actions if a.dest == "phase")
    assert tuple(phase_action.choices) == hook.HOOK_PHASES


def test_install_hooks_emits_command_for_every_phase() -> None:
    """Every phase in HOOK_PHASES is referenced by some ``kg hook <phase>``
    command in the installer's hook block, and no extras leak in."""
    block = _hook_block(Path("/fake/tool/root"))

    commands: list[str] = []
    for blocks in block.values():
        for entry in blocks:
            for h in entry.get("hooks", []):
                commands.append(h.get("command", ""))

    # Extract the phase token from each `... hook <phase>` command.
    phases_in_install: set[str] = set()
    for cmd in commands:
        parts = cmd.split()
        if "hook" in parts:
            idx = parts.index("hook")
            if idx + 1 < len(parts):
                phases_in_install.add(parts[idx + 1])

    assert phases_in_install == set(hook.HOOK_PHASES)


def test_hook_dispatch_handles_every_phase(monkeypatch) -> None:
    """``hook.run(<phase>)`` for every HOOK_PHASES name dispatches to a
    handler and does not fall through to the "Unknown hook phase" branch.

    Stubs the dispatch table directly so the test stays a pure routing
    check (no registry/filesystem state).
    """
    called: list[str] = []

    def _stub_for(name: str):
        def _f() -> int:
            called.append(name)
            return 0
        return _f

    stub_dispatch = {name: _stub_for(name) for name in hook.HOOK_PHASES}
    monkeypatch.setattr(hook, "_DISPATCH", stub_dispatch)

    # Capture _emit so the unknown-phase branch would be visible.
    emitted: list[tuple[str, str]] = []
    monkeypatch.setattr(
        hook, "_emit", lambda name, body: emitted.append((name, body))
    )

    for phase in hook.HOOK_PHASES:
        rc = hook.run(phase)
        assert rc == 0

    assert sorted(called) == sorted(hook.HOOK_PHASES)
    assert emitted == []


def test_hook_dispatch_table_keys_match_hook_phases() -> None:
    """The private ``_DISPATCH`` map is keyed on exactly HOOK_PHASES.

    A regression here means ``run()`` would silently miss a phase or carry
    a dead entry — both of which the public contract is meant to forbid.
    """
    assert set(hook._DISPATCH.keys()) == set(hook.HOOK_PHASES)


def test_hook_dispatch_unknown_phase_emits_unknown_hook(monkeypatch) -> None:
    """``run()`` for an unknown phase emits the UnknownHook envelope and
    returns 0 — preserves the prior fall-through behaviour."""
    emitted: list[tuple[str, str]] = []
    monkeypatch.setattr(
        hook, "_emit", lambda name, body: emitted.append((name, body))
    )
    rc = hook.run("not-a-real-phase")
    assert rc == 0
    assert len(emitted) == 1
    assert emitted[0][0] == "UnknownHook"
    assert "not-a-real-phase" in emitted[0][1]
