"""kg install cascade — write a pre-push hook into a target repo.

Mirrors install.sh:cmd_cascade().

Writes a pre-push hook into a target repo's .git/hooks/pre-push that
regenerates the knowledge graph and commits/pushes KG changes when
the target repo pushes. Used once per project repo tracked in the
depgraph corpus.

Idempotent. Backs up an existing pre-push hook before overwrite.
"""
from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path

from ._shared import backup_file, die, log, ok, warn


def _resolve_script_path() -> str:
    """Return the absolute path to bin/kg-prepush-cascade.

    Resolves from this module's location (mirrors install.sh's
    'dirname "$0"/bin/kg-prepush-cascade' logic).
    """
    # kg/cli/install/cascade.py → parents[3] = knowledge-graph root
    tool_root = Path(__file__).resolve().parents[3]
    return str(tool_root / "bin" / "kg-prepush-cascade")


def generate_hook_script(
    depgraph: str,
    logigraph: str,
    script_path: str,
) -> str:
    """Return the pre-push hook script content.

    Mirrors the heredoc in install.sh:cmd_cascade() exactly.
    The returned string ends with a single trailing newline (matches
    bash 'printf "%s\\n" "$generated"').
    """
    return (
        "#!/bin/bash\n"
        "# pre-push hook installed by knowledge-graph install.sh cascade.\n"
        "# Cascades regen + commit + push to the KG corpora when this repo pushes.\n"
        f'export KG_DEPGRAPH_DIR="{depgraph}"\n'
        f'export KG_LOGIGRAPH_DIR="{logigraph}"\n'
        f'exec "{script_path}" "$@"\n'
    )


def cmd_cascade(args: argparse.Namespace) -> int:
    """Port of install.sh:cmd_cascade().

    Without --apply, prints the hook script to stdout.
    With --apply, writes .git/hooks/pre-push and sets the executable bit.
    """
    target_repo: str = getattr(args, "target_repo", "") or ""
    kg_depg: str = getattr(args, "depgraph", "") or ""
    kg_logg: str = getattr(args, "logigraph", "") or ""
    apply: bool = getattr(args, "apply", False)
    force: bool = getattr(args, "force", False)

    # Validations mirror install.sh's die() calls.
    if not target_repo:
        die(
            "usage: install.sh cascade <target-repo> --depgraph <dir> "
            "[--logigraph <dir>] [--apply]"
        )

    if not (Path(target_repo) / ".git").is_dir():
        die(f"{target_repo} is not a git repo")

    if not kg_depg and not kg_logg:
        die("at least one of --depgraph / --logigraph must be supplied")

    if kg_depg and not Path(kg_depg).is_dir():
        die(f"depgraph dir not found: {kg_depg}")

    if kg_logg and not Path(kg_logg).is_dir():
        die(f"logigraph dir not found: {kg_logg}")

    script_path = _resolve_script_path()
    if not Path(script_path).is_file():
        die(f"kg-prepush-cascade script missing at {script_path}")

    hook_path = Path(target_repo) / ".git" / "hooks" / "pre-push"
    generated = generate_hook_script(kg_depg, kg_logg, script_path)

    if not apply:
        print(generated, end="")
        log(f"(not written — pass --apply to install at {hook_path})")
        return 0

    # --apply path -----------------------------------------------------------

    if hook_path.exists() and not force:
        # If the existing file already matches what we'd write, no-op.
        if hook_path.read_text() == generated:
            ok(f"pre-push hook already in place: {hook_path}")
            return 0
        backup_file(hook_path)
        warn("existing pre-push hook backed up; pass --force to skip backup next time")

    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(generated)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ok(f"installed pre-push hook: {hook_path}")
    log(f"  KG depgraph:  {kg_depg if kg_depg else '(unset)'}")
    log(f"  KG logigraph: {kg_logg if kg_logg else '(unset)'}")
    return 0
