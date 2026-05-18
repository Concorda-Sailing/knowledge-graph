"""Tests for kg/cli/install/teardown.py — inverse of `kg install bootstrap`."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from kg.cli.install.path import (
    PATH_BLOCK_END_MARKER,
    PATH_BLOCK_MARKER,
    generate_path_snippet,
)
from kg.cli.install.teardown import (
    _strip_kg_hooks,
    _strip_path_block,
    cmd_teardown,
)


def _make_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        data_dir=None,
        target=None,
        rcfile=None,
        keep_data=False,
        keep_framework=False,
        keep_backups=False,
        dry_run=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _strip_kg_hooks — settings.json surgery (pure function)
# ---------------------------------------------------------------------------


def test_strip_kg_hooks_removes_kg_commands_only() -> None:
    """kg-hook entries are removed; user-authored entries on the same key
    are preserved."""
    settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Edit|Write|MultiEdit", "hooks": [
                    {"type": "command", "command": "/home/u/tools/knowledge-graph/bin/kg hook pre-edit"},
                    {"type": "command", "command": "/home/u/custom-script.sh"},
                ]},
            ],
            "Stop": [
                {"hooks": [
                    {"type": "command", "command": "/home/u/tools/knowledge-graph/bin/kg hook post-edit"},
                ]},
            ],
        }
    }
    cleaned, removed = _strip_kg_hooks(settings)
    assert len(removed) == 2  # one PreToolUse, one Stop
    # The user-authored entry survived.
    assert cleaned["hooks"]["PreToolUse"][0]["hooks"] == [
        {"type": "command", "command": "/home/u/custom-script.sh"},
    ]
    # Stop had only the kg entry, so the whole top key is gone.
    assert "Stop" not in cleaned["hooks"]


def test_strip_kg_hooks_drops_empty_hooks_key() -> None:
    """When every entry is a kg-hook, the entire 'hooks' key is removed
    (settings.json looks like a clean uninstall)."""
    settings = {
        "model": "claude-opus-4-7",
        "hooks": {
            "PreToolUse": [
                {"matcher": "Edit", "hooks": [
                    {"type": "command", "command": "~/tools/knowledge-graph/bin/kg hook pre-edit"},
                ]},
            ],
        },
    }
    cleaned, removed = _strip_kg_hooks(settings)
    assert len(removed) == 1
    assert "hooks" not in cleaned
    assert cleaned["model"] == "claude-opus-4-7"  # other keys untouched


def test_strip_kg_hooks_noop_when_no_kg_entries() -> None:
    """If no command contains the kg substr, removed is empty + settings
    unchanged."""
    settings = {"hooks": {"PreToolUse": [
        {"matcher": "Edit", "hooks": [
            {"type": "command", "command": "/usr/local/bin/other"},
        ]},
    ]}}
    cleaned, removed = _strip_kg_hooks(settings)
    assert removed == []
    assert cleaned == settings


def test_strip_kg_hooks_handles_missing_hooks_key() -> None:
    """Missing top-level 'hooks' is a no-op (don't crash)."""
    settings = {"model": "claude-haiku-4-5"}
    cleaned, removed = _strip_kg_hooks(settings)
    assert removed == []
    assert cleaned == settings


# ---------------------------------------------------------------------------
# _strip_path_block — rcfile surgery (pure function)
# ---------------------------------------------------------------------------


def test_strip_path_block_with_end_sentinel_removes_exact_range() -> None:
    """A block written by the current generate_path_snippet (which includes
    the end sentinel) is stripped exactly."""
    pre = "# user-authored line above\nexport FOO=bar\n\n"
    block = generate_path_snippet("/home/u/tools")
    post = "\n# user-authored line below\nexport BAR=baz\n"
    text = pre + block + post

    new_text, removed = _strip_path_block(text)

    assert new_text is not None
    assert PATH_BLOCK_MARKER not in new_text
    assert PATH_BLOCK_END_MARKER not in new_text
    # Pre and post lines preserved verbatim.
    assert "export FOO=bar" in new_text
    assert "export BAR=baz" in new_text
    assert removed >= len(block.strip().splitlines())


def test_strip_path_block_legacy_no_end_sentinel_walks_to_export_path() -> None:
    """A block written before the end sentinel existed (install.sh-era)
    is still stripped via the line-walking fallback."""
    legacy = (
        f"{PATH_BLOCK_MARKER}\n"
        f'if [ -d "/t/knowledge-graph/depgraph/bin" ] ; then\n'
        f'    PATH="/t/knowledge-graph/depgraph/bin:$PATH"\n'
        f"fi\n"
        f"export PATH\n"
        f"\n"
    )
    pre = "# user line\n"
    post = "# more user lines\nexport X=1\n"
    text = pre + legacy + post

    new_text, removed = _strip_path_block(text)

    assert new_text is not None
    assert PATH_BLOCK_MARKER not in new_text
    assert "depgraph/bin" not in new_text
    assert "# user line" in new_text
    assert "export X=1" in new_text


def test_strip_path_block_absent_returns_none() -> None:
    """No managed block → (None, 0)."""
    text = "# just some unrelated stuff\nexport FOO=bar\n"
    new_text, removed = _strip_path_block(text)
    assert new_text is None
    assert removed == 0


# ---------------------------------------------------------------------------
# cmd_teardown — end-to-end with mocked side effects
# ---------------------------------------------------------------------------


def _bootstrap_filesystem(home: Path) -> dict:
    """Plant the files a real bootstrap would have created. Returns dict of paths."""
    target = home / "tools"
    bundle = target / "knowledge-graph"
    bundle.mkdir(parents=True)
    (bundle / "sentinel.txt").write_text("framework")

    settings_path = home / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({
        "model": "claude-opus-4-7",
        "hooks": {
            "PreToolUse": [
                {"matcher": "Edit|Write|MultiEdit", "hooks": [
                    {"type": "command", "command": f"{bundle}/bin/kg hook pre-edit"},
                ]},
            ],
            "Stop": [
                {"hooks": [
                    {"type": "command", "command": f"{bundle}/bin/kg hook post-edit"},
                ]},
            ],
        },
    }, indent=2))

    registry_path = home / ".claude" / "kg-graphs.toml"
    data_dir = home / "myproject-knowledge-graph"
    data_dir.mkdir()
    (data_dir / "project.toml").write_text('[project]\nname = "myproject"\n')
    registry_path.write_text(
        '[[graph]]\nname = "myproject"\n'
        f'path = "{data_dir}"\n'
    )

    profile = home / ".profile"
    profile.write_text(
        "# user-authored above\nexport FOO=bar\n\n"
        + generate_path_snippet(str(target))
        + "\n# user-authored below\nexport BAR=baz\n"
    )

    systemd_dir = home / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True)
    unit_path = systemd_dir / "graphui.service"
    unit_path.write_text("[Unit]\nDescription=stub\n")

    return {
        "target": target,
        "bundle": bundle,
        "settings": settings_path,
        "registry": registry_path,
        "data_dir": data_dir,
        "profile": profile,
        "unit": unit_path,
    }


def test_cmd_teardown_removes_every_install_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fully-applied teardown removes all six locations bootstrap created."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / ".claude" / "kg-graphs.toml"))
    paths = _bootstrap_filesystem(tmp_path)

    # systemctl: pretend it's absent so we don't try to talk to the real bus.
    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        rc = cmd_teardown(_make_args())

    assert rc == 0
    assert not paths["unit"].exists(), "systemd unit not removed"
    # settings.json stays, but the hooks key is gone.
    assert paths["settings"].exists()
    surviving = json.loads(paths["settings"].read_text())
    assert "hooks" not in surviving
    assert surviving["model"] == "claude-opus-4-7"
    assert not paths["registry"].exists(), "registry not removed"
    assert not paths["data_dir"].exists(), "data dir not removed"
    assert not paths["bundle"].exists(), "framework dir not removed"
    # ~/.profile keeps user-authored lines.
    profile_text = paths["profile"].read_text()
    assert "export FOO=bar" in profile_text
    assert "export BAR=baz" in profile_text
    assert PATH_BLOCK_MARKER not in profile_text


def test_cmd_teardown_dry_run_does_not_touch_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--dry-run reports everything but leaves disk untouched."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / ".claude" / "kg-graphs.toml"))
    paths = _bootstrap_filesystem(tmp_path)
    profile_before = paths["profile"].read_text()
    settings_before = paths["settings"].read_text()

    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        rc = cmd_teardown(_make_args(dry_run=True))

    assert rc == 0
    assert paths["unit"].exists()
    assert paths["registry"].exists()
    assert paths["data_dir"].exists()
    assert paths["bundle"].exists()
    assert paths["profile"].read_text() == profile_before
    assert paths["settings"].read_text() == settings_before


def test_cmd_teardown_idempotent_after_first_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Re-running teardown on an already-clean machine returns 0 with
    'already absent' messages, not failures."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / ".claude" / "kg-graphs.toml"))
    _bootstrap_filesystem(tmp_path)

    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        cmd_teardown(_make_args())
        capsys.readouterr()  # discard first-run output
        rc = cmd_teardown(_make_args())

    assert rc == 0
    out = capsys.readouterr().out
    assert "already absent" in out


def test_cmd_teardown_keep_data_preserves_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--keep-data leaves the discovered data dir(s) alone."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / ".claude" / "kg-graphs.toml"))
    paths = _bootstrap_filesystem(tmp_path)

    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        rc = cmd_teardown(_make_args(keep_data=True))

    assert rc == 0
    assert paths["data_dir"].exists()
    assert (paths["data_dir"] / "project.toml").exists()
    # But the framework + registry still got removed.
    assert not paths["bundle"].exists()
    assert not paths["registry"].exists()


def test_cmd_teardown_keep_framework_preserves_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--keep-framework leaves ~/tools/knowledge-graph/ alone."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / ".claude" / "kg-graphs.toml"))
    paths = _bootstrap_filesystem(tmp_path)

    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        rc = cmd_teardown(_make_args(keep_framework=True))

    assert rc == 0
    assert paths["bundle"].exists()
    assert (paths["bundle"] / "sentinel.txt").exists()


def test_cmd_teardown_invokes_systemctl_when_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When systemctl is on PATH, teardown stops + disables + daemon-reloads."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / ".claude" / "kg-graphs.toml"))
    _bootstrap_filesystem(tmp_path)

    calls: list[list[str]] = []

    def fake_run(cmd, **kw):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with patch("kg.cli.install.teardown._systemctl_available", return_value=True):
        with patch("kg.cli.install.teardown.subprocess.run", side_effect=fake_run):
            rc = cmd_teardown(_make_args())

    assert rc == 0
    joined = [" ".join(c) for c in calls]
    assert any("stop graphui" in c for c in joined)
    assert any("disable graphui" in c for c in joined)
    assert any("daemon-reload" in c for c in joined)


def test_cmd_teardown_data_dir_arg_overrides_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--data-dir wins over the registry. Useful when registry is missing or
    user wants to remove a specific dir without trusting the registry."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Point registry at a path that does not exist — explicit --data-dir should
    # still drive the removal.
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / "no-such-registry.toml"))

    explicit_data = tmp_path / "explicit-data"
    explicit_data.mkdir()
    (explicit_data / "marker").touch()

    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        rc = cmd_teardown(_make_args(data_dir=str(explicit_data)))

    assert rc == 0
    assert not explicit_data.exists()


def test_cmd_teardown_handles_clean_machine_gracefully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Running teardown on a machine that was never bootstrapped doesn't crash;
    every step reports 'already absent' or skip."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / "no-such-registry.toml"))

    with patch("kg.cli.install.teardown._systemctl_available", return_value=False):
        rc = cmd_teardown(_make_args())

    assert rc == 0
    out = capsys.readouterr().out
    assert "teardown complete" in out


# ---------------------------------------------------------------------------
# Round-trip: install bootstrap snippet → teardown strips it cleanly.
# ---------------------------------------------------------------------------


def test_generate_snippet_now_includes_end_sentinel() -> None:
    """The current snippet emits both markers so teardown can match exactly."""
    snippet = generate_path_snippet("/t")
    assert PATH_BLOCK_MARKER in snippet
    assert PATH_BLOCK_END_MARKER in snippet


def test_apply_then_teardown_roundtrips_rcfile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cmd_path --apply then teardown's strip restores the rcfile to its
    original content (modulo trailing newline normalization)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    from kg.cli.install.path import cmd_path

    rcfile = tmp_path / ".profile"
    original = "# preexisting\nexport KEEP=1\n"
    rcfile.write_text(original)

    apply_args = argparse.Namespace(
        target=str(tmp_path / "tools"), rcfile=str(rcfile),
        apply=True, force=False,
    )
    assert cmd_path(apply_args) == 0
    assert PATH_BLOCK_MARKER in rcfile.read_text()

    new_text, _ = _strip_path_block(rcfile.read_text())
    assert new_text is not None
    assert PATH_BLOCK_MARKER not in new_text
    assert "export KEEP=1" in new_text
