"""kg install teardown — inverse of `kg install bootstrap`.

Reverses every side effect bootstrap creates:

  1. Stops, disables, and removes the graphui systemd `--user` unit.
  2. Strips kg-hook entries from ~/.claude/settings.json (matched by
     command containing `knowledge-graph/bin/kg`).
  3. Removes the kg orchestrator registry at ~/.claude/kg-graphs.toml.
  4. Removes the per-project data dir(s) (`--keep-data` to preserve).
  5. Strips the managed PATH block from ~/.profile (or `--rcfile`).
  6. Removes the framework dir at ~/tools/knowledge-graph/
     (`--keep-framework` to preserve).

Idempotent — each step prints "already absent" instead of failing when its
target isn't there. `--dry-run` reports what would happen without writing.

Data dirs come from the registry when `--data-dir` isn't given. Without a
registry and without `--data-dir`, data dirs are left alone (the user can
re-run with `--data-dir <path>` to remove them).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ._shared import color_yellow, log, ok, warn
from .path import PATH_BLOCK_END_MARKER, PATH_BLOCK_MARKER
from .systemd import (
    _SERVICE_NAME,
    _SYSTEMD_UNIT,
    _systemctl_available,
    _systemd_dir,
)


_BUNDLE_DIR = "knowledge-graph"
_HOOK_COMMAND_SUBSTR = "knowledge-graph/bin/kg"


def _home() -> Path:
    return Path(os.environ.get("HOME", str(Path.home())))


def _strip_kg_hooks(
    settings: dict, kg_substr: str = _HOOK_COMMAND_SUBSTR
) -> tuple[dict, list[tuple[str, str | None, str]]]:
    """Remove hook entries whose command contains `kg_substr`.

    Returns (new_settings, removed) where `removed` is a list of
    (top_key, matcher, command) tuples for logging.
    Empty matcher-blocks are pruned; an empty `hooks` key is removed
    entirely so the resulting settings.json is what a clean uninstall
    should look like.
    """
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return settings, []

    removed: list[tuple[str, str | None, str]] = []
    new_hooks: dict = {}
    for top_key, blocks in hooks.items():
        if not isinstance(blocks, list):
            new_hooks[top_key] = blocks
            continue
        new_blocks: list[dict] = []
        for block in blocks:
            matcher = block.get("matcher")
            entries = block.get("hooks") or []
            keep = []
            for e in entries:
                cmd = (e.get("command") or "") if isinstance(e, dict) else ""
                if kg_substr in cmd:
                    removed.append((top_key, matcher, cmd))
                else:
                    keep.append(e)
            if keep:
                nb = dict(block)
                nb["hooks"] = keep
                new_blocks.append(nb)
        if new_blocks:
            new_hooks[top_key] = new_blocks

    if new_hooks:
        settings["hooks"] = new_hooks
    else:
        settings.pop("hooks", None)
    return settings, removed


def _strip_path_block(text: str) -> tuple[str | None, int]:
    """Strip the managed PATH block from `text`. Returns (new_text, lines_removed).

    Prefers the PATH_BLOCK_END_MARKER for end detection (new installs);
    falls back to walking PATH-block-shaped lines (older installs).

    Returns (None, 0) if no managed block is present.
    """
    lines = text.splitlines()
    start: int | None = None
    for i, ln in enumerate(lines):
        if PATH_BLOCK_MARKER in ln:
            start = i
            break
    if start is None:
        return None, 0

    end: int | None = None
    for i in range(start + 1, len(lines)):
        if PATH_BLOCK_END_MARKER in lines[i]:
            end = i + 1
            break
    if end is None:
        end = start + 1
        while end < len(lines):
            ln = lines[end].lstrip()
            if ln.startswith(("if ", "PATH=", "fi", "export PATH", "    PATH=")) or ln == "":
                end += 1
                if (
                    lines[end - 1].strip() == ""
                    and end >= 2
                    and lines[end - 2].strip() == "export PATH"
                ):
                    break
            else:
                break

    removed = end - start
    new_lines = lines[:start] + lines[end:]
    # Collapse double-blank that opens where the block used to be.
    while len(new_lines) >= 2 and new_lines[-1] == "" and new_lines[-2] == "":
        new_lines.pop()
    new_text = "\n".join(new_lines)
    if new_text and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, removed


def _discover_data_dirs(
    explicit: str | None,
) -> list[Path]:
    """Resolve which data dirs to remove. Explicit arg wins; otherwise read
    the registry. Best-effort — registry read errors are warned, not fatal."""
    if explicit:
        return [Path(explicit).expanduser()]
    try:
        from kg import registry
        return [entry.path for entry in registry.load()]
    except Exception as e:
        warn(f"could not read kg registry: {e}; pass --data-dir to remove data manually")
        return []


def cmd_teardown(args: argparse.Namespace) -> int:
    """Inverse of cmd_bootstrap. Returns 0 on success, even when individual
    steps had nothing to do (idempotent uninstall)."""
    dry: bool = bool(getattr(args, "dry_run", False))
    keep_data: bool = bool(getattr(args, "keep_data", False))
    keep_framework: bool = bool(getattr(args, "keep_framework", False))
    keep_backups: bool = bool(getattr(args, "keep_backups", False))
    data_dir_arg: str | None = getattr(args, "data_dir", None)
    rcfile_arg: str | None = getattr(args, "rcfile", None)
    target_arg: str | None = getattr(args, "target", None)

    if dry:
        log(color_yellow("DRY-RUN — no changes will be made"))

    home = _home()
    target = Path(target_arg or (home / "tools")).expanduser()
    bundle = target / _BUNDLE_DIR
    data_dirs = _discover_data_dirs(data_dir_arg)

    # 1. systemd unit.
    _teardown_systemd(dry=dry)

    # 2. ~/.claude/settings.json hook entries.
    _teardown_hooks(home=home, dry=dry, keep_backups=keep_backups)

    # 3. ~/.claude/kg-graphs.toml registry.
    registry_path = home / ".claude" / "kg-graphs.toml"
    if registry_path.exists():
        if dry:
            log(f"would remove {registry_path}")
        else:
            registry_path.unlink()
            ok(f"removed {registry_path}")
    else:
        log(f"{registry_path} already absent — skip")

    # 4. Data dir(s).
    if keep_data:
        if data_dirs:
            log(f"--keep-data — leaving {len(data_dirs)} data dir(s) in place")
        else:
            log("--keep-data — no data dirs discovered anyway")
    else:
        for d in data_dirs:
            _remove_tree(d, dry=dry, label="data dir")
        if not data_dirs:
            log("no data dirs discovered — skip (pass --data-dir to remove a specific one)")

    # 5. PATH block in rcfile.
    rcfile = Path(rcfile_arg) if rcfile_arg else (home / ".profile")
    _teardown_path_block(rcfile=rcfile, dry=dry, keep_backups=keep_backups)

    # 6. Framework dir.
    if keep_framework:
        log(f"--keep-framework — leaving {bundle} in place")
    else:
        _remove_tree(bundle, dry=dry, label="framework dir")

    print()
    if dry:
        log("DRY-RUN complete; re-run without --dry-run to apply")
    else:
        ok("teardown complete")
    return 0


def _teardown_systemd(*, dry: bool) -> None:
    unit_path = _systemd_dir() / _SYSTEMD_UNIT
    has_systemctl = _systemctl_available()

    if has_systemctl:
        for cmd in (
            ["systemctl", "--user", "stop", _SERVICE_NAME],
            ["systemctl", "--user", "disable", _SERVICE_NAME],
        ):
            if dry:
                log(f"would run: {' '.join(cmd)}")
            else:
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )

    if unit_path.exists():
        if dry:
            log(f"would remove {unit_path}")
        else:
            unit_path.unlink()
            ok(f"removed {unit_path}")
        if has_systemctl and not dry:
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    else:
        log(f"{unit_path} already absent — skip")
    if not has_systemctl and unit_path.exists():
        warn("systemctl not on PATH — unit file removed but service was not stopped")


def _teardown_hooks(*, home: Path, dry: bool, keep_backups: bool) -> None:
    settings_path = home / ".claude" / "settings.json"
    if not settings_path.exists():
        log(f"{settings_path} not present — skip")
        return

    try:
        settings = json.loads(settings_path.read_text() or "{}")
    except json.JSONDecodeError:
        warn(f"{settings_path} is not valid JSON — leaving as-is")
        return

    cleaned, removed = _strip_kg_hooks(settings)
    if not removed:
        log(f"no kg-hook entries in {settings_path} — skip")
        return

    if dry:
        log(f"would strip {len(removed)} kg-hook entries from {settings_path}")
        for top, matcher, cmd in removed:
            loc = top + (f" / {matcher}" if matcher else "")
            print(f"    [{loc}] {cmd}")
        return

    bak = settings_path.with_suffix(settings_path.suffix + ".bak")
    shutil.copy2(settings_path, bak)
    log(f"backed up to {bak}")
    settings_path.write_text(json.dumps(cleaned, indent=2) + "\n")
    ok(f"stripped {len(removed)} kg-hook entries from {settings_path}")

    if not keep_backups and bak.exists():
        bak.unlink()
        log(f"removed {bak} (pass --keep-backups to preserve)")


def _teardown_path_block(*, rcfile: Path, dry: bool, keep_backups: bool) -> None:
    if not rcfile.exists():
        log(f"{rcfile} not present — skip")
        return

    original = rcfile.read_text()
    new_text, removed_lines = _strip_path_block(original)
    if new_text is None:
        log(f"no managed PATH block in {rcfile} — skip")
        return

    if dry:
        log(f"would strip {removed_lines} lines of PATH block from {rcfile}")
        return

    bak = rcfile.with_suffix(rcfile.suffix + ".bak")
    shutil.copy2(rcfile, bak)
    log(f"backed up to {bak}")
    rcfile.write_text(new_text)
    ok(f"stripped PATH block from {rcfile} ({removed_lines} lines)")

    if not keep_backups and bak.exists():
        bak.unlink()
        log(f"removed {bak} (pass --keep-backups to preserve)")


def _remove_tree(p: Path, *, dry: bool, label: str) -> None:
    p = p.expanduser()
    if not p.exists():
        log(f"{p} already absent — skip ({label})")
        return
    if dry:
        log(f"would remove {p} ({label})")
        return
    try:
        shutil.rmtree(p)
        ok(f"removed {p} ({label})")
    except OSError as e:
        warn(f"could not remove {p}: {e}")
