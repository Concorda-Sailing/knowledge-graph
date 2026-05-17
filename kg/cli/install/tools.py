"""kg install tools — install/upgrade the framework binaries.

Was `install.sh install`. Verifies the bundle layout exists, bootstraps
graphui's venv if missing, optionally clones --data repos.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from ._shared import check_prereqs, color_yellow, err, log, ok


BUNDLE_DIR = "knowledge-graph"


def _clone_or_pull(url: str, dest: Path) -> None:
    if (dest / ".git").exists():
        log(f"{dest.name}: present; pulling latest")
        # Fetch + try fast-forward to origin/<current> then origin/HEAD
        try:
            subprocess.run(["git", "-C", str(dest), "fetch", "--quiet", "origin"], check=False)
            cur = subprocess.run(
                ["git", "-C", str(dest), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True, check=False,
            ).stdout.strip() or "main"
            r = subprocess.run(
                ["git", "-C", str(dest), "merge", "--quiet", "--ff-only", f"origin/{cur}"],
                capture_output=True, text=True, check=False,
            )
            if r.returncode != 0:
                subprocess.run(
                    ["git", "-C", str(dest), "merge", "--quiet", "--ff-only", "origin/HEAD"],
                    capture_output=True, text=True, check=False,
                )
        except Exception:
            pass
    else:
        log(f"cloning {url} → {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", url, str(dest)], check=True)
    ok(str(dest))


def cmd_tools(args: argparse.Namespace) -> int:
    """Install/upgrade the framework. Mirrors install.sh:cmd_install."""
    check_prereqs()
    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    bundle = target / BUNDLE_DIR
    bundle.mkdir(parents=True, exist_ok=True)
    log(f"installing into {color_yellow(str(bundle))}")

    # Subsystems must be present (this script lives in the bundle itself).
    for subsystem in ("depgraph", "logigraph", "graphui"):
        if not (bundle / subsystem).is_dir():
            err(f"missing {bundle / subsystem} — install.sh must be run from inside the knowledge-graph checkout")
            return 1

    # graphui venv bootstrap
    g = bundle / "graphui"
    venv = g / ".venv"
    if not venv.exists():
        log("graphui: creating venv + installing requirements")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run(
            [str(venv / "bin" / "pip"), "install", "--quiet", "-r", str(g / "requirements.txt")],
            check=True,
        )
    else:
        log("graphui: venv present; upgrading requirements")
        subprocess.run(
            [str(venv / "bin" / "pip"), "install", "--quiet", "--upgrade", "-r", str(g / "requirements.txt")],
            check=True,
        )
    ok(f"graphui venv at {venv}")

    # --data clones
    org = os.environ.get("KNOWLEDGE_GRAPH_ORG")
    for spec in (args.data or []):
        if "=" not in spec:
            err(f"invalid --data spec: {spec} (expected owner/repo=local-path)")
            return 1
        repo_part, path_part = spec.split("=", 1)
        if "/" not in repo_part:
            if not org:
                err(
                    f"--data spec {spec!r} omits the owner; pass owner/repo=path "
                    "or set KNOWLEDGE_GRAPH_ORG"
                )
                return 1
            repo_part = f"{org}/{repo_part}"
        cloned_path = Path(os.path.expanduser(path_part))
        _clone_or_pull(f"https://github.com/{repo_part}.git", cloned_path)

    print()
    ok("install complete")
    return 0
