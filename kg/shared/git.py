"""Git helpers used by depgraph and logigraph CLIs.

Lifted from logigraph/lib/cli/_shared.py (the superset implementation
with the actor parameter). depgraph's _depgraph_commit_if_changed is
re-exported in P5T2.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def default_actor() -> str:
    """Return git config user.name, or $USER, or 'unknown'."""
    r = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return os.environ.get("USER", "unknown")


def git_commit_if_changed(
    repo_dir: Path,
    paths: list,  # list[Path] | list[str]
    message: str,
    actor: str | None = None,
) -> bool:
    """Stage `paths` in `repo_dir`, commit with `message`. Returns True if
    anything was actually committed (i.e. the staged diff was non-empty).
    """
    # Tolerate a data dir that isn't under git: the node/dossier write has
    # already happened, so a missing repo must degrade gracefully rather than
    # crash the bump command with git's exit 128.
    inside = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
    )
    if inside.returncode != 0:
        print(f"note: {repo_dir} is not a git repository; skipping auto-commit")
        return False
    paths_str = [str(p) for p in paths]
    if paths_str:
        subprocess.run(
            ["git", "-C", str(repo_dir), "add", "--", *paths_str],
            check=True,
        )
    diff = subprocess.run(
        ["git", "-C", str(repo_dir), "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    if not diff.stdout.strip():
        return False
    cmd = ["git", "-C", str(repo_dir), "commit", "-q", "-m", message]
    if actor:
        cmd += ["--author", actor]
    subprocess.run(cmd, check=True)
    return True
