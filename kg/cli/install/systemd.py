"""kg install systemd — generate or apply the graphui systemd unit.

Mirrors install.sh:generate_systemd_unit() and install.sh:cmd_systemd().
All Phase-1 improvements are included:
  - --depgraph-data-dir / --logigraph-data-dir explicit overrides
  - Sibling-with-hyphen layout auto-detect
  - Preflight refusal on missing data dirs
  - graphui venv bootstrap if .venv/bin/uvicorn is missing
  - Idempotent re-apply (no-op if unit already current)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from ._shared import backup_file, die, err, log, ok, warn

_BUNDLE_DIR = "knowledge-graph"
_SYSTEMD_UNIT = "graphui.service"
_SERVICE_NAME = "graphui"  # unit name without .service
_GRAPHUI_PORT = 8081


def _systemd_dir() -> Path:
    """Return ~/.config/systemd/user/, honouring a monkeypatched $HOME."""
    home = Path(os.environ.get("HOME", str(Path.home())))
    return home / ".config" / "systemd" / "user"


def generate_systemd_unit(
    target: str,
    depg: str,
    logg: str,
    port: int = _GRAPHUI_PORT,
) -> str:
    """Return the unit file content.

    Mirrors install.sh:generate_systemd_unit() exactly.  The returned string
    ends with a single trailing newline (as the bash heredoc produces).
    """
    bundle = f"{target}/{_BUNDLE_DIR}"
    return (
        "[Unit]\n"
        "Description=knowledge-graph viewer (depgraph + logigraph)\n"
        "After=network.target\n"
        "\n"
        "[Service]\n"
        "Type=simple\n"
        f"WorkingDirectory={bundle}/graphui\n"
        f"Environment=PATH={bundle}/graphui/.venv/bin:/usr/local/bin:/usr/bin:/bin\n"
        f"Environment=DEPGRAPH_DATA_DIR={depg}\n"
        f"Environment=LOGIGRAPH_DATA_DIR={logg}\n"
        f"Environment=DEPGRAPH_BIN={bundle}/depgraph/bin/depgraph\n"
        f"Environment=LOGIGRAPH_BIN={bundle}/logigraph/bin/logigraph\n"
        f"ExecStart={bundle}/graphui/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port {port}\n"
        "Restart=on-failure\n"
        "RestartSec=3\n"
        "\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def cmd_systemd(args: argparse.Namespace) -> int:
    """Port of install.sh:cmd_systemd().

    Generates the graphui systemd unit file.  Without --apply, prints a
    header comment and the unit content to stdout.  With --apply, writes
    the unit to ~/.config/systemd/user/graphui.service and manages the
    service via systemctl --user.
    """
    target: str = args.target
    project: str | None = getattr(args, "project", None) or ""
    depg_override: str = getattr(args, "depgraph_data_dir", None) or ""
    logg_override: str = getattr(args, "logigraph_data_dir", None) or ""
    apply: bool = getattr(args, "apply", False)

    # Mirror install.sh: if no --project and not both overrides given, use a
    # placeholder and warn.
    if not project and not (depg_override and logg_override):
        project = str(Path.home() / "your-project")
        warn(f"no --project given; using placeholder {project}")

    # Resolve data dirs: explicit flags win, otherwise resolve the project
    # path through the shared bundle-layout helper so both data-dir
    # conventions ("nested" <p>/knowledge-graph/ and "sibling-with-hyphen"
    # <p>-knowledge-graph/) work consistently across bootstrap, init, and
    # systemd. Avoids the doubled-path bug where a user passing
    # ~/concorda-knowledge-graph got DEPGRAPH_DATA_DIR=...concorda-knowledge-graph/knowledge-graph/depgraph.
    from kg.cli.install.init import resolve_bundle_layout
    depg = depg_override
    logg = logg_override

    if not depg or not logg:
        bundle, _pname = resolve_bundle_layout(Path(project))
        if not depg:
            depg = str(bundle / "depgraph")
        if not logg:
            logg = str(bundle / "logigraph")

    unit = generate_systemd_unit(target, depg, logg)

    if not apply:
        # Dry-run: print header + unit to stdout so the user can copy/pipe.
        systemd_dir = _systemd_dir()
        unit_path = systemd_dir / _SYSTEMD_UNIT
        print(f"# Write the following to {unit_path} and run:")
        print(
            f"#   systemctl --user daemon-reload && "
            f"systemctl --user enable --now {_SERVICE_NAME}"
        )
        print()
        print(unit, end="")
        return 0

    # --apply path -------------------------------------------------------

    # Preflight: data dirs must exist before we write a unit that points at
    # them — otherwise graphui loads zero nodes and renders an empty
    # dashboard with no obvious cause.
    bundle = f"{target}/{_BUNDLE_DIR}"
    missing: list[str] = []
    if not Path(depg).is_dir():
        missing.append(f"DEPGRAPH_DATA_DIR={depg}")
    if not Path(logg).is_dir():
        missing.append(f"LOGIGRAPH_DATA_DIR={logg}")
    if missing:
        err("refusing to write unit — data dir(s) do not exist:")
        for m in missing:
            print(f"    {m}", file=sys.stderr)
        err("pass --depgraph-data-dir / --logigraph-data-dir, or fix --project layout")
        return 1

    # Preflight: ensure the venv binary the unit will point at actually
    # exists.  Bootstrap it now so the unit doesn't crash-loop with
    # status=203/EXEC after restart.
    g = Path(f"{bundle}/graphui")
    uvicorn_bin = g / ".venv" / "bin" / "uvicorn"
    if not uvicorn_bin.exists():
        if not g.is_dir():
            die(
                f"graphui directory missing at {g} — "
                f"run 'kg install tools --target {target}' first"
            )
        log(f"graphui venv missing at {g}/.venv; bootstrapping")
        subprocess.run([sys.executable, "-m", "venv", str(g / ".venv")], check=True)
        subprocess.run(
            [str(g / ".venv" / "bin" / "pip"), "install", "--quiet", "--upgrade", "pip"],
            check=True,
        )
        subprocess.run(
            [
                str(g / ".venv" / "bin" / "pip"),
                "install",
                "--quiet",
                "-r",
                str(g / "requirements.txt"),
            ],
            check=True,
        )
        ok(f"graphui venv ready at {g}/.venv")

    # Idempotent write: detect existing unit file with same content.
    systemd_dir = _systemd_dir()
    systemd_dir.mkdir(parents=True, exist_ok=True)
    path = systemd_dir / _SYSTEMD_UNIT
    changed = True
    if path.exists() and path.read_text() == unit:
        changed = False
        log("unit file already current — no-op")
    else:
        backup_file(path)
        path.write_text(unit)
        ok(f"wrote {path}")

    # systemctl calls.
    if _systemctl_available():
        if changed:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        subprocess.run(
            ["systemctl", "--user", "enable", _SERVICE_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        is_active = subprocess.run(
            ["systemctl", "--user", "is-active", _SERVICE_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if is_active:
            if changed:
                subprocess.run(
                    ["systemctl", "--user", "restart", _SERVICE_NAME], check=False
                )
                ok(f"graphui restarted on port {_GRAPHUI_PORT}")
            else:
                ok(f"graphui already active on port {_GRAPHUI_PORT}")
        else:
            subprocess.run(
                ["systemctl", "--user", "start", _SERVICE_NAME], check=False
            )
            import time
            time.sleep(1)
            still_active = subprocess.run(
                ["systemctl", "--user", "is-active", _SERVICE_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0
            if still_active:
                ok(f"graphui active on port {_GRAPHUI_PORT}")
            else:
                warn(
                    f"graphui failed to start; run "
                    f"'systemctl --user status {_SERVICE_NAME}' to inspect"
                )
                return 1
    else:
        warn("systemctl not found; unit written but not enabled")

    return 0


def _systemctl_available() -> bool:
    """Return True if systemctl is on PATH."""
    import shutil
    return shutil.which("systemctl") is not None
