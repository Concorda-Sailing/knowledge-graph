import argparse
import json
from pathlib import Path
import pytest

from kg.cli.install.hooks import cmd_hooks


def test_hooks_dry_run_prints_snippet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Without --apply, prints the JSON snippet to stdout."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = argparse.Namespace(project=str(tmp_path / "myproject"), apply=False, force=False)
    rc = cmd_hooks(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "kg hook" in out
    assert "PreToolUse" in out or "pre-edit" in out


def test_hooks_apply_writes_settings_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With --apply, writes ~/.claude/settings.json with the hooks block."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    args = argparse.Namespace(project=str(tmp_path / "myproject"), apply=True, force=False)
    rc = cmd_hooks(args)
    assert rc == 0
    settings = fake_home / ".claude" / "settings.json"
    assert settings.exists()
    data = json.loads(settings.read_text())
    assert "hooks" in data


def test_hooks_apply_preserves_other_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An existing settings.json with unrelated keys keeps them on apply."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({
        "theme": "dark",
        "permissions": {"allow": ["foo"]},
    }))
    args = argparse.Namespace(project=str(tmp_path / "myproject"), apply=True, force=False)
    rc = cmd_hooks(args)
    assert rc == 0
    data = json.loads(settings.read_text())
    assert data["theme"] == "dark"
    assert data["permissions"] == {"allow": ["foo"]}
    assert "hooks" in data


def test_hooks_apply_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-applying with same project is a no-op (no error)."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    args = argparse.Namespace(project=str(tmp_path / "myproject"), apply=True, force=False)
    assert cmd_hooks(args) == 0
    assert cmd_hooks(args) == 0  # second call also succeeds


def test_hooks_dry_run_has_all_phases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Dry-run output contains all 4 top-level phase keys."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = argparse.Namespace(project=None, apply=False, force=False)
    rc = cmd_hooks(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert set(data["hooks"].keys()) == {"PreToolUse", "Stop", "SessionStart", "SessionEnd"}


def test_hooks_dry_run_commands_point_at_kg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Each hook command invokes bin/kg hook <phase>."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = argparse.Namespace(project=None, apply=False, force=False)
    cmd_hooks(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    hooks = data["hooks"]
    commands = []
    for blocks in hooks.values():
        for block in blocks:
            for entry in block.get("hooks", []):
                commands.append(entry["command"])
    assert any("pre-edit" in c for c in commands)
    assert any("pre-irreversible" in c for c in commands)
    assert any("post-edit" in c for c in commands)
    assert any("session-start" in c for c in commands)
    assert any("session-end" in c for c in commands)


def test_hooks_apply_refuses_extra_user_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If existing hooks has entries install.sh can't reproduce, refuse even without --force."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    # Write settings with an extra user hook that install.sh doesn't generate
    existing = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "SomeTool",
                    "hooks": [{"type": "command", "command": "/usr/local/bin/my-custom-hook"}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))
    args = argparse.Namespace(project=None, apply=True, force=False)
    rc = cmd_hooks(args)
    assert rc == 2


def test_hooks_apply_refuses_extra_user_hooks_even_with_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Extra user hooks block the write even when --force is passed."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    existing = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "SomeTool",
                    "hooks": [{"type": "command", "command": "/usr/local/bin/my-custom-hook"}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))
    args = argparse.Namespace(project=None, apply=True, force=True)
    rc = cmd_hooks(args)
    assert rc == 2


def test_hooks_apply_force_overwrites_stale_kg_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--force is required (but not sufficient alone) for path migrations.

    Old-path commands that differ from new_flat are treated as extras by the
    extras guard — install.sh refuses to clobber them even with --force because
    it can't reproduce an arbitrary old path.  The caller must manually remove
    the stale 'hooks' key first.  This test documents that --force alone does
    NOT bypass the extras check.
    """
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    # Existing hooks point at an old path — diff from new_flat → treated as extras
    old_kg = "/old/path/to/bin/kg"
    existing = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit",
                    "hooks": [{"type": "command", "command": f"{old_kg} hook pre-edit", "timeout": 10}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))
    args = argparse.Namespace(project=None, apply=True, force=True)
    rc = cmd_hooks(args)
    # extras guard fires even with --force
    assert rc == 2


def test_hooks_apply_force_overwrites_when_only_schema_diff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--force allows overwrite when existing hooks diff is cosmetic (no extras).

    If the existing hooks block has the exact same commands as new_flat but with
    a structural difference (e.g. same commands, different key order), extras is
    empty, so with --force the write succeeds.
    """
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)

    # Build a hooks block that uses the SAME commands as what _hook_block()
    # would generate (same tool_root), but in a different structural shape
    # so existing_hooks != block (triggers the non-extras force gate).
    from kg.cli.install.hooks import _hook_block
    from pathlib import Path as P
    tool_root = P(__file__).resolve().parents[3]
    real_block = _hook_block(tool_root)
    # Wrap only part of the block so existing != block, but all commands match
    partial_block = {k: v for k, v in real_block.items() if k != "SessionEnd"}
    settings.write_text(json.dumps({"hooks": partial_block}))

    args = argparse.Namespace(project=None, apply=True, force=True)
    rc = cmd_hooks(args)
    assert rc == 0
    data = json.loads(settings.read_text())
    assert "SessionEnd" in data["hooks"]


def test_hooks_apply_no_force_refuses_differing_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without --force, a differing (but install.sh-subset) hooks block is refused."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    old_kg = "/old/path/to/bin/kg"
    existing = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit",
                    "hooks": [{"type": "command", "command": f"{old_kg} hook pre-edit", "timeout": 10}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))
    args = argparse.Namespace(project=None, apply=True, force=False)
    rc = cmd_hooks(args)
    assert rc == 2


def test_hooks_apply_backs_up_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When applying to an existing settings.json, a .bak file is created."""
    fake_home = tmp_path
    monkeypatch.setenv("HOME", str(fake_home))
    settings = fake_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"theme": "dark"}))
    args = argparse.Namespace(project=None, apply=True, force=False)
    rc = cmd_hooks(args)
    assert rc == 0
    bak_files = list((fake_home / ".claude").glob("settings.json.bak.*"))
    assert len(bak_files) == 1
