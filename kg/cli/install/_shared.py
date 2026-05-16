"""Shared utilities for kg/cli/install — Python equivalents of install.sh's helpers."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ---- color output (TTY-aware, matches install.sh's behavior) ---------------

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR", "") == ""


def _wrap(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def color_red(text: str) -> str:     return _wrap("31", text)
def color_green(text: str) -> str:   return _wrap("32", text)
def color_yellow(text: str) -> str:  return _wrap("33", text)
def color_dim(text: str) -> str:     return _wrap("2", text)


# ---- print-style logging (mirrors install.sh's log/ok/warn/err/die) --------

def log(msg: str) -> None:
    print(f"{color_dim('·')} {msg}")


def ok(msg: str) -> None:
    print(f"{color_green('✓')} {msg}")


def warn(msg: str) -> None:
    print(f"{color_yellow('⚠')} {msg}", file=sys.stderr)


def err(msg: str) -> None:
    print(f"{color_red('✗')} {msg}", file=sys.stderr)


def die(msg: str, code: int = 1) -> None:
    """Print error and exit. Equivalent to bash 'die'."""
    err(msg)
    raise SystemExit(code)


# ---- prerequisites --------------------------------------------------------

def require(cmd: str) -> None:
    """Verify `cmd` is on PATH; die if not."""
    if shutil.which(cmd) is None:
        die(f"missing prerequisite: {cmd}")


def check_prereqs() -> None:
    """Verify git + python 3.10+. Mirrors install.sh:check_prereqs()."""
    log("checking prerequisites")
    require("git")
    pyver = sys.version_info
    if pyver < (3, 10):
        die(f"python 3.10+ required (found {pyver.major}.{pyver.minor}) — tomllib is stdlib from 3.11")
    ok(f"git + python {pyver.major}.{pyver.minor}")


# ---- file helpers ---------------------------------------------------------

def backup_file(p: Path) -> Path | None:
    """If `p` exists, copy to `p.bak.<mtime>` and return the backup path.

    Returns None if `p` doesn't exist. Equivalent to install.sh:backup_file()
    semantics (bak suffix includes mtime so re-runs don't clobber prior backups).
    """
    if not p.exists():
        return None
    mtime = int(p.stat().st_mtime)
    bak = p.with_suffix(p.suffix + f".bak.{mtime}")
    if not bak.exists():
        shutil.copy2(p, bak)
        log(f"backed up to {bak}")
    return bak
