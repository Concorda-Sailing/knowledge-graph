#!/usr/bin/env bash
# install.sh — installer + project scaffolder for the knowledge-graph
# substrate (depgraph + logigraph + graphui).
#
# Usage:
#   ./install.sh                              install tools to ~/tools/knowledge-graph/
#   ./install.sh --target /path               install tools to /path/knowledge-graph/
#   ./install.sh --data <owner/repo>=<path>   also clone a data repo (repeatable)
#
#   ./install.sh init <project>               scaffold a fresh project data dir
#                                             under <project>/knowledge-graph/
#
#   ./install.sh hooks [--apply]              print (or write) the
#                                             ~/.claude/settings.json hook
#                                             snippet. One entry per phase
#                                             pointing at the `kg`
#                                             orchestrator — project paths
#                                             come from kg-graphs.toml, not
#                                             from settings.json.
#   ./install.sh systemd [--project <dir>] [--apply]
#                                             print (or write) graphui systemd unit
#   ./install.sh path [--rcfile <file>] [--apply] [--force]
#                                             print (or write) the shell PATH
#                                             snippet that puts depgraph and
#                                             logigraph CLIs on $PATH.
#
#   ./install.sh cascade <target-repo> \
#                --depgraph <kg-depgraph-dir> \
#                [--logigraph <kg-logigraph-dir>] [--apply]
#                                             write a pre-push hook into
#                                             <target-repo>/.git/hooks/pre-push
#                                             that regenerates the KG and
#                                             commits + pushes any KG changes
#                                             when the target repo pushes.
#                                             Run once per project repo
#                                             tracked in depgraph project.toml.
#
#   ./install.sh bootstrap <project-dir>      one-shot: install tools + scaffold
#                                             project (or use existing data) +
#                                             apply hooks + apply systemd.
#                                             Idempotent.
#
#   ./install.sh --help                       show this help
#
# Safe by default: never overwrites without a backup; never modifies
# ~/.claude/settings.json or systemd units unless --apply is passed.

set -euo pipefail

# ----- configuration --------------------------------------------------------

DEFAULT_TARGET="$HOME/tools"
# Default GitHub org for framework repos; override with KNOWLEDGE_GRAPH_ORG env.
ORG="${KNOWLEDGE_GRAPH_ORG:-Concorda-Sailing}"
# Tools install and project data both live one level deep under this dir.
BUNDLE_DIR="knowledge-graph"
SETTINGS_FILE="$HOME/.claude/settings.json"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SYSTEMD_UNIT="graphui.service"
GRAPHUI_PORT=8081

# ----- helpers --------------------------------------------------------------

# Color output only when stdout is a terminal. When an LLM agent or CI
# captures the output, ANSI escapes are noise.
if [[ -t 1 ]] && [[ "${NO_COLOR:-}" == "" ]]; then
    color_red()    { printf '\033[31m%s\033[0m' "$*"; }
    color_green()  { printf '\033[32m%s\033[0m' "$*"; }
    color_yellow() { printf '\033[33m%s\033[0m' "$*"; }
    color_dim()    { printf '\033[2m%s\033[0m' "$*"; }
else
    color_red()    { printf '%s' "$*"; }
    color_green()  { printf '%s' "$*"; }
    color_yellow() { printf '%s' "$*"; }
    color_dim()    { printf '%s' "$*"; }
fi

log()  { printf '%s %s\n' "$(color_dim "·")" "$*"; }
ok()   { printf '%s %s\n' "$(color_green "✓")" "$*"; }
warn() { printf '%s %s\n' "$(color_yellow "⚠")" "$*" >&2; }
err()  { printf '%s %s\n' "$(color_red "✗")" "$*" >&2; }
die()  { err "$*"; exit 1; }

usage() {
    sed -n '2,42p' "$0" | sed 's/^# \{0,1\}//'
}

require() {
    command -v "$1" >/dev/null 2>&1 || die "missing prerequisite: $1"
}

check_prereqs() {
    log "checking prerequisites"
    require git
    require python3
    local pyver
    pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    case "$pyver" in
        3.1[0-9]|3.[2-9][0-9]) ;;
        *) die "python 3.10+ required (found $pyver) — tomllib is stdlib from 3.11" ;;
    esac
    ok "git + python $pyver"
}

clone_or_pull() {
    local url="$1" dir="$2"
    if [[ -d "$dir/.git" ]]; then
        log "$(basename "$dir"): present; pulling latest"
        # Pull from origin/HEAD rather than the local branch's recorded
        # upstream — robust to default-branch renames (master→main) where
        # the local tracking ref might be stale.
        (
            cd "$dir"
            local cur
            cur=$(git symbolic-ref --short HEAD 2>/dev/null || echo main)
            git fetch --quiet origin 2>&1 | sed 's/^/    /' || true
            # Try to fast-forward to the matching remote branch, then to
            # origin/HEAD, then give up quietly.
            git merge --quiet --ff-only "origin/$cur" 2>/dev/null \
                || git merge --quiet --ff-only "$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)" 2>/dev/null \
                || warn "$(basename "$dir"): could not fast-forward — uncommitted local changes?"
        )
    else
        log "cloning $url → $dir"
        mkdir -p "$(dirname "$dir")"
        git clone --quiet "$url" "$dir"
    fi
    ok "$dir"
}

backup_file() {
    local f="$1"
    [[ -f "$f" ]] || return 0
    local bak="${f}.bak.$(date +%s)"
    cp -p "$f" "$bak"
    log "backed up to $bak"
}

# ----- subcommands ----------------------------------------------------------

cmd_install() {
    local target="$DEFAULT_TARGET"
    local extra_data=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)   target="$2"; shift 2 ;;
            --data)     extra_data+=("$2"); shift 2 ;;
            --help|-h)  usage; exit 0 ;;
            *)          die "unknown flag: $1" ;;
        esac
    done

    check_prereqs
    mkdir -p "$target"
    local bundle="$target/$BUNDLE_DIR"
    mkdir -p "$bundle"
    log "installing into $(color_yellow "$bundle")"

    # Subsystems are siblings of install.sh in this consolidated repo.
    # Verify each is on disk; absence means the script is being run
    # outside the knowledge-graph checkout.
    local subsystem
    for subsystem in depgraph logigraph graphui; do
        if [[ ! -d "$bundle/$subsystem" ]]; then
            die "missing $bundle/$subsystem — install.sh must be run from inside the knowledge-graph checkout"
        fi
    done

    # graphui venv
    local g="$bundle/graphui"
    if [[ ! -d "$g/.venv" ]]; then
        log "graphui: creating venv + installing requirements"
        python3 -m venv "$g/.venv"
        "$g/.venv/bin/pip" install --quiet -r "$g/requirements.txt"
    else
        log "graphui: venv present; upgrading requirements"
        "$g/.venv/bin/pip" install --quiet --upgrade -r "$g/requirements.txt"
    fi
    ok "graphui venv at $g/.venv"

    # Arbitrary --data clones
    for spec in "${extra_data[@]}"; do
        local repo="${spec%%=*}"
        local path="${spec#*=}"
        [[ "$repo" != "$path" ]] || die "invalid --data spec: $spec (expected owner/repo=local-path)"
        # If `owner/` is omitted, default to the configured ORG.
        [[ "$repo" == */* ]] || repo="$ORG/$repo"
        local cloned_path
        cloned_path=$(eval echo "$path")
        clone_or_pull "https://github.com/$repo.git" "$cloned_path"
    done

    echo
    ok "install complete"
    if [[ ${#extra_data[@]} -gt 0 ]]; then
        echo
        cat <<NEXT
$(color_yellow "Next:")

  Add depgraph + logigraph CLIs to your shell PATH:
    $0 path --apply

  Apply Claude Code hooks pointing at your project data dir:
    $0 hooks --project <project-dir> --apply

  Register graphui as a systemd --user service:
    $0 systemd --project <project-dir> --apply
NEXT
    else
        echo
        cat <<NEXT
$(color_yellow "Next:")

  1. Scaffold a project data dir:           $0 init ~/your-project
  2. Add CLIs to your shell PATH:           $0 path --apply
  3. Print the hook snippet:                $0 hooks
  4. (Optional) Register graphui daemon:    $0 systemd

  Or one-shot:                              $0 bootstrap ~/your-project
NEXT
    fi
}

cmd_init() {
    local project_dir="${1:-}"
    [[ -n "$project_dir" ]] || die "usage: $0 init <project-data-dir>"
    [[ "$project_dir" = /* ]] || project_dir="$PWD/$project_dir"
    local bundle="$project_dir/$BUNDLE_DIR"
    [[ ! -e "$bundle/depgraph" ]] || die "$bundle/depgraph already exists; refusing to overwrite"

    log "scaffolding project at $(color_yellow "$bundle")"
    local pname
    pname=$(basename "$project_dir")

    mkdir -p "$bundle"
    # Root project.toml: declares the graph as a whole. `kg add` reads
    # this to learn the graph's name and subsystem list.
    cat > "$bundle/project.toml" <<TOML
# Root project descriptor read by \`kg\` (the orchestrator). Per-subsystem
# configuration lives in depgraph/project.toml and logigraph/project.toml.

[project]
name = "$pname"
subsystems = ["depgraph", "logigraph"]
TOML

    mkdir -p "$bundle/depgraph/extractors" \
             "$bundle/depgraph/nodes" \
             "$bundle/depgraph/dossiers" \
             "$bundle/depgraph/telemetry"
    cat > "$bundle/depgraph/project.toml" <<TOML
# $pname depgraph project config.

[project]
name = "$pname"

# Repos this depgraph corpus extracts from. The logical name on the left
# is what extractors refer to; the path on the right is the directory
# under \$HOME (or an absolute path).
[repos]
# api = "$pname-api"
# web = "$pname-web"
TOML
    cat > "$bundle/depgraph/extractors/README.md" <<MD
# Extractors

Drop your extractor scripts in here. Each extractor walks a repo (declared
in \`../project.toml [repos]\`) and emits JSON node files under \`../nodes/\`
following the framework schema at \`~/tools/$BUNDLE_DIR/depgraph/schema/node.schema.json\`.

The Concorda reference implementation lives at
\`Concorda-Sailing/concorda-depgraph\` — clone it for examples:

- \`extract_api.py\` — FastAPI route handlers + SQLAlchemy models
- \`extract_web.ts\` — Next.js components + React hooks
- \`extract_tests.ts\` — Playwright specs
MD

    mkdir -p "$bundle/logigraph/nodes/rules" \
             "$bundle/logigraph/nodes/domain" \
             "$bundle/logigraph/dossiers/rules" \
             "$bundle/logigraph/dossiers/domain" \
             "$bundle/logigraph/telemetry"
    cat > "$bundle/logigraph/project.toml" <<TOML
# $pname logigraph project config.

[project]
name = "$pname"

# Path to this project's depgraph data dir.
[depgraph]
data_dir = "$bundle/depgraph"
TOML
    cat > "$bundle/logigraph/CANDIDATES.md" <<MD
# Rule candidates

This file is the human notebook for rules that should be authored. Add
candidates as you discover them; mark as authored after \`bin/logigraph
rule-stub\` materializes them.

### rule::category::short_name
- statement: one-sentence rule
- why: motivation + history
- surfaces: file:line refs
- confidence: high | medium | low
MD

    ok "scaffolded $bundle"
    echo
    cat <<NEXT
$(color_yellow "Next:")

  Register this graph with the kg orchestrator:
    $DEFAULT_TARGET/$BUNDLE_DIR/bin/kg add $bundle

  Apply the project-agnostic Claude Code hook block (one-time per machine):
    $0 hooks --apply

  Or print the hook snippet to merge by hand:
    $0 hooks
NEXT
}

# ----- hooks: print or apply -----------------------------------------------

generate_hooks_json() {
    # One entry per phase, all pointing at the `kg` orchestrator. kg reads
    # ~/.claude/kg-graphs.toml and dispatches to whichever registered graph
    # owns the file being edited — so settings.json no longer carries
    # per-project paths. Add/remove projects with `kg add` / `kg remove`.
    local target="$1"
    local kg_bin="$target/$BUNDLE_DIR/bin/kg"
    cat <<JSON
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [
        {
          "type": "command",
          "command": "$kg_bin hook pre-edit",
          "timeout": 10
        }
      ]
    },
    {
      "matcher": "Bash|mcp__.*",
      "hooks": [
        {
          "type": "command",
          "command": "$kg_bin hook pre-irreversible",
          "timeout": 5
        }
      ]
    }
  ],
  "Stop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "$kg_bin hook post-edit",
          "timeout": 120
        }
      ]
    }
  ],
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "$kg_bin hook session-start",
          "timeout": 30
        }
      ]
    }
  ],
  "SessionEnd": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "$kg_bin hook session-end",
          "timeout": 30
        }
      ]
    }
  ]
}
JSON
}

cmd_hooks() {
    local target="$DEFAULT_TARGET"
    local project=""
    local apply=0
    local force=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)  target="$2"; shift 2 ;;
            --project) project="$2"; shift 2 ;;
            --apply)   apply=1; shift ;;
            --force)   force=1; shift ;;
            *)         die "unknown flag: $1" ;;
        esac
    done

    # --project is no longer required (hooks are project-agnostic via the kg
    # orchestrator) but we still accept it so callers like `bootstrap` can
    # register the project via `kg add` after writing the hooks block.

    local hooks_json
    hooks_json=$(generate_hooks_json "$target")

    if [[ "$apply" -eq 0 ]]; then
        cat <<HEADER
# Merge the following into your $SETTINGS_FILE under "hooks":
# (the top-level "hooks" key wraps PreToolUse + Stop blocks below.)

HEADER
        echo "$hooks_json"
        return
    fi

    # --apply path: idempotent merge into settings.json.
    # Re-applying with the same content is a no-op success — safe for an
    # agent to call without checking first.
    require python3
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    python3 - "$SETTINGS_FILE" "$force" <<PY
import json, sys, os
from pathlib import Path
p = Path(sys.argv[1])
force = sys.argv[2] == "1"
if p.exists() and p.read_text().strip():
    settings = json.loads(p.read_text())
else:
    settings = {}
new_hooks = $hooks_json
existing = settings.get("hooks")

# Flatten {top_key: [{matcher, hooks: [{type, command, timeout}, ...]}, ...]}
# into a set of (top_key, matcher_or_None, command) tuples. The command
# string captures everything we care about preserving (data-dir paths,
# script paths) without locking on cosmetic differences like timeout.
def flatten(h):
    out = set()
    for top_key, blocks in (h or {}).items():
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            matcher = block.get("matcher")
            for entry in block.get("hooks", []) or []:
                out.add((top_key, matcher, entry.get("command", "")))
    return out

if existing == new_hooks:
    print(f"✓ hooks already match in {p} — no-op")
    sys.exit(0)

# Entries in existing that this command would not regenerate. Even under
# --force, refuse to clobber these — the previous bug was that --force
# replaced the entire hooks dict, silently dropping user hooks and
# other-project hooks. Force is for *path migrations* (same install.sh-
# generated commands, different bundle dir), not for blowing away
# information the script can't reproduce.
new_flat = flatten(new_hooks)
existing_flat = flatten(existing)
extras = sorted(existing_flat - new_flat)

if extras:
    print("⚠ refusing to write: settings.json has hook entries beyond what install.sh would generate.",
          file=sys.stderr)
    print("  --force will NOT bypass this check; these entries can't be reproduced from install.sh args.",
          file=sys.stderr)
    print("  Entries that would be lost:", file=sys.stderr)
    for top, matcher, cmd in extras:
        loc = top + (f" / {matcher}" if matcher else "")
        print(f"    [{loc}] {cmd}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  To proceed: back up settings.json, remove the conflicting entries (or the entire 'hooks' key),",
          file=sys.stderr)
    print("  and re-run. Run without --apply to see the snippet install.sh would write.",
          file=sys.stderr)
    sys.exit(2)

if existing and not force:
    print("⚠ settings.json has a different 'hooks' section.", file=sys.stderr)
    print("  Existing keys:", list(existing.keys()), file=sys.stderr)
    print("  Re-run with '--apply --force' to overwrite, or merge manually", file=sys.stderr)
    print("  (run without --apply to see the snippet).", file=sys.stderr)
    sys.exit(2)
# Backup before write
if p.exists():
    bak = p.with_suffix(p.suffix + ".bak." + str(int(os.path.getmtime(p))))
    if not bak.exists():
        bak.write_bytes(p.read_bytes())
        print(f"· backed up to {bak}")
settings["hooks"] = new_hooks
p.write_text(json.dumps(settings, indent=2) + "\n")
print(f"✓ wrote hooks into {p}")
PY
}

# ----- systemd: print or apply ---------------------------------------------

generate_systemd_unit() {
    local target="$1" depg="$2" logg="$3"
    local bundle="$target/$BUNDLE_DIR"
    cat <<UNIT
[Unit]
Description=knowledge-graph viewer (depgraph + logigraph)
After=network.target

[Service]
Type=simple
WorkingDirectory=$bundle/graphui
Environment=PATH=$bundle/graphui/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=DEPGRAPH_DATA_DIR=$depg
Environment=LOGIGRAPH_DATA_DIR=$logg
Environment=DEPGRAPH_BIN=$bundle/depgraph/bin/depgraph
Environment=LOGIGRAPH_BIN=$bundle/logigraph/bin/logigraph
ExecStart=$bundle/graphui/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $GRAPHUI_PORT
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
UNIT
}

cmd_systemd() {
    local target="$DEFAULT_TARGET"
    local project=""
    local apply=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)  target="$2"; shift 2 ;;
            --project) project="$2"; shift 2 ;;
            --apply)   apply=1; shift ;;
            *)         die "unknown flag: $1" ;;
        esac
    done

    if [[ -z "$project" ]]; then
        project="$HOME/your-project"
        warn "no --project given; using placeholder $project"
    fi
    local depg="$project/$BUNDLE_DIR/depgraph"
    local logg="$project/$BUNDLE_DIR/logigraph"

    local unit
    unit=$(generate_systemd_unit "$target" "$depg" "$logg")

    if [[ "$apply" -eq 0 ]]; then
        cat <<HEADER
# Write the following to $SYSTEMD_DIR/$SYSTEMD_UNIT and run:
#   systemctl --user daemon-reload && systemctl --user enable --now ${SYSTEMD_UNIT%.service}

HEADER
        echo "$unit"
        return
    fi

    # --apply path: idempotent.
    mkdir -p "$SYSTEMD_DIR"
    local path="$SYSTEMD_DIR/$SYSTEMD_UNIT"
    local changed=1
    if [[ -f "$path" ]] && diff -q <(echo "$unit") "$path" >/dev/null 2>&1; then
        changed=0
        log "unit file already current — no-op"
    else
        backup_file "$path"
        echo "$unit" > "$path"
        ok "wrote $path"
    fi

    if command -v systemctl >/dev/null 2>&1; then
        [[ "$changed" -eq 1 ]] && systemctl --user daemon-reload
        systemctl --user enable "${SYSTEMD_UNIT%.service}" >/dev/null 2>&1 || true
        if systemctl --user is-active "${SYSTEMD_UNIT%.service}" >/dev/null 2>&1; then
            if [[ "$changed" -eq 1 ]]; then
                systemctl --user restart "${SYSTEMD_UNIT%.service}"
                ok "graphui restarted on port $GRAPHUI_PORT"
            else
                ok "graphui already active on port $GRAPHUI_PORT"
            fi
        else
            systemctl --user start "${SYSTEMD_UNIT%.service}"
            sleep 1
            if systemctl --user is-active "${SYSTEMD_UNIT%.service}" >/dev/null 2>&1; then
                ok "graphui active on port $GRAPHUI_PORT"
            else
                warn "graphui failed to start; run 'systemctl --user status ${SYSTEMD_UNIT%.service}' to inspect"
                exit 1
            fi
        fi
    else
        warn "systemctl not found; unit written but not enabled"
    fi
}

# ----- path: print or apply the shell PATH snippet -------------------------
#
# The hooks block puts the framework on Claude Code's invocation surface,
# but interactive shells (and the LLM's Bash tool) need `depgraph` /
# `logigraph` resolvable on $PATH too. This subcommand emits a sentinel-
# guarded block that can be appended to ~/.profile (default) or any other
# rcfile. Re-applying is idempotent; --apply --force replaces a block
# pointing at a different target after backing it up.

# Sentinel comment — used as the marker to find/replace the block on
# re-apply. Existing installs' rcfiles use the literal string to identify
# the block, so don't change it casually.
PATH_BLOCK_MARKER="# Knowledge-graph framework CLIs (depgraph, logigraph) — managed by install.sh"

generate_path_snippet() {
    local target="$1"
    local bundle="$target/$BUNDLE_DIR"
    cat <<SNIPPET
$PATH_BLOCK_MARKER
if [ -d "$bundle/depgraph/bin" ] ; then
    PATH="$bundle/depgraph/bin:\$PATH"
fi
if [ -d "$bundle/logigraph/bin" ] ; then
    PATH="$bundle/logigraph/bin:\$PATH"
fi
export PATH
SNIPPET
}

cmd_path() {
    local target="$DEFAULT_TARGET"
    local rcfile=""
    local apply=0
    local force=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)  target="$2"; shift 2 ;;
            --rcfile)  rcfile="$2"; shift 2 ;;
            --apply)   apply=1; shift ;;
            --force)   force=1; shift ;;
            --help|-h) usage; exit 0 ;;
            *)         die "unknown flag: $1" ;;
        esac
    done

    # Default to ~/.profile: it's sourced by login shells AND by
    # non-interactive bash (`bash -c`, agent harnesses) where ~/.bashrc's
    # standard "early-return when non-interactive" guard would skip it.
    [[ -n "$rcfile" ]] || rcfile="$HOME/.profile"

    local snippet
    snippet=$(generate_path_snippet "$target")

    if [[ "$apply" -eq 0 ]]; then
        cat <<HEADER
# Append the following to $rcfile (or re-run with --apply to write it
# automatically; --apply --force replaces a managed block pointing at a
# different target after backing it up).

HEADER
        echo "$snippet"
        return
    fi

    require python3
    mkdir -p "$(dirname "$rcfile")"
    touch "$rcfile"

    # Idempotent merge driven by the sentinel marker. Three cases:
    #   1. No marker present                 → append block.
    #   2. Marker present, current target    → no-op.
    #   3. Marker present, different target  → require --force; rewrite.
    python3 - "$rcfile" "$target" "$BUNDLE_DIR" "$PATH_BLOCK_MARKER" "$force" <<'PY'
import os, sys, time
from pathlib import Path

rcfile, target, bundle, marker, force = sys.argv[1:6]
force = force == "1"
p = Path(rcfile)
text = p.read_text() if p.exists() else ""

new_block = f"""{marker}
if [ -d "{target}/{bundle}/depgraph/bin" ] ; then
    PATH="{target}/{bundle}/depgraph/bin:$PATH"
fi
if [ -d "{target}/{bundle}/logigraph/bin" ] ; then
    PATH="{target}/{bundle}/logigraph/bin:$PATH"
fi
export PATH"""

lines = text.splitlines()
try:
    start = next(i for i, ln in enumerate(lines) if marker in ln)
except StopIteration:
    # Case 1: no existing block — append.
    sep = "" if text.endswith("\n") or text == "" else "\n"
    p.write_text(text + sep + "\n" + new_block + "\n")
    print(f"✓ appended PATH block to {rcfile}")
    sys.exit(0)

# Find end of block: walk forward over PATH-block-shaped lines until
# something else appears. Conservative — bails on the first unfamiliar
# line so a hand-edited rcfile never has unrelated content eaten.
end = start + 1
while end < len(lines):
    ln = lines[end].lstrip()
    if (ln.startswith(("if ", "PATH=", "fi", "export PATH", "    PATH="))
            or ln == ""):
        end += 1
        # Stop one line past `fi` followed by `export PATH` followed by blank
        if (lines[end-1].strip() == ""
                and end >= 2 and lines[end-2].strip() == "export PATH"):
            break
    else:
        break

existing = "\n".join(lines[start:end]).rstrip()
if existing == new_block:
    print(f"✓ PATH block already current in {rcfile} — no-op")
    sys.exit(0)

if not force:
    print(f"⚠ {rcfile} has a managed PATH block pointing at a different target.",
          file=sys.stderr)
    print(f"  Existing first line: {lines[start+1] if start+1 < len(lines) else '(empty)'}",
          file=sys.stderr)
    print("  Re-run with '--apply --force' to replace it (a backup will be made).",
          file=sys.stderr)
    sys.exit(2)

# Backup before rewrite.
bak = p.with_suffix(p.suffix + f".bak.{int(time.time())}")
bak.write_bytes(p.read_bytes())
print(f"· backed up to {bak}")

new_lines = lines[:start] + new_block.splitlines() + lines[end:]
p.write_text("\n".join(new_lines).rstrip() + "\n")
print(f"✓ rewrote PATH block in {rcfile}")
PY
}

# ----- bootstrap: install + (init|use existing data) + hooks + systemd -----

cmd_bootstrap() {
    local project=""
    local data_args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --data) data_args+=(--data "$2"); shift 2 ;;
            --help|-h) usage; exit 0 ;;
            -*) die "unknown flag: $1" ;;
            *) [[ -z "$project" ]] || die "multiple project dirs given"; project="$1"; shift ;;
        esac
    done
    [[ -n "$project" ]] || die "usage: $0 bootstrap <project-dir> [--data owner/repo=path]"
    [[ "$project" = /* ]] || project="$PWD/$project"

    log "bootstrapping → $(color_yellow "$project")"
    echo

    cmd_install "${data_args[@]}"
    echo

    # If the project doesn't have a data layout yet, scaffold it.
    # Otherwise use what's there (e.g. cloned via --data).
    if [[ ! -d "$project/$BUNDLE_DIR/depgraph" || ! -d "$project/$BUNDLE_DIR/logigraph" ]]; then
        log "scaffolding empty project layout at $project/$BUNDLE_DIR"
        cmd_init "$project"
        echo
    else
        log "using existing project data at $project/$BUNDLE_DIR"
    fi

    log "applying Claude Code hooks → $SETTINGS_FILE"
    # bootstrap implies "set up from scratch" — overwrite any existing hooks
    # block (after backing it up). Use plain `cmd_hooks` for interactive review.
    cmd_hooks --project "$project" --apply --force
    echo

    log "registering project with kg orchestrator"
    # The hooks are project-agnostic; kg-graphs.toml is where dispatch
    # happens. `kg add` is idempotent — re-running with the same path is
    # a no-op success.
    "$DEFAULT_TARGET/$BUNDLE_DIR/bin/kg" add "$project/$BUNDLE_DIR" \
        || warn "kg add failed; run '$DEFAULT_TARGET/$BUNDLE_DIR/bin/kg add $project/$BUNDLE_DIR' manually"
    echo

    log "applying systemd unit for graphui"
    cmd_systemd --project "$project" --apply
    echo

    # PATH for interactive shells + the LLM's Bash tool. Without this,
    # `depgraph` and `logigraph` resolve only inside Claude Code's hook
    # environment — manual lookups (and any agent tasked to "run depgraph
    # context X") break with command-not-found, which historically led
    # the agent to skip the discovery step entirely.
    log "applying PATH block to ~/.profile"
    # bootstrap implies a clean slate — replace any managed block that
    # points at a different target.
    cmd_path --apply --force || warn "PATH apply skipped or failed; run '$0 path' to inspect"
    echo

    ok "bootstrap complete"
    cat <<DONE

  Tools:                       $DEFAULT_TARGET/$BUNDLE_DIR/{depgraph,logigraph,graphui}/
  Project data:                $project/$BUNDLE_DIR/{depgraph,logigraph}/
  Claude Code hooks:           $SETTINGS_FILE
  Graphui daemon:              $SYSTEMD_DIR/$SYSTEMD_UNIT
  Graphui URL:                 http://localhost:$GRAPHUI_PORT/graph/
  Shell PATH:                  ~/.profile (run 'source ~/.profile' to pick up depgraph/logigraph in this shell)

  Note: Claude Code reads settings.json at session start. Restart any
  open sessions to pick up the new hooks.
DONE
}

cmd_cascade() {
    # Install a pre-push hook in a target project repo that regenerates
    # the knowledge graph, commits any KG changes, and pushes them when
    # the target repo pushes.
    local target_repo=""
    local kg_depg=""
    local kg_logg=""
    local apply=0
    local force=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --depgraph)  kg_depg="$2"; shift 2 ;;
            --logigraph) kg_logg="$2"; shift 2 ;;
            --apply)     apply=1; shift ;;
            --force)     force=1; shift ;;
            -*)          die "unknown flag: $1" ;;
            *)           if [[ -z "$target_repo" ]]; then target_repo="$1"; shift
                         else die "unexpected arg: $1"; fi ;;
        esac
    done

    [[ -n "$target_repo" ]] || die "usage: install.sh cascade <target-repo> --depgraph <dir> [--logigraph <dir>] [--apply]"
    [[ -d "$target_repo/.git" ]] || die "$target_repo is not a git repo"
    [[ -n "$kg_depg" || -n "$kg_logg" ]] || die "at least one of --depgraph / --logigraph must be supplied"
    [[ -z "$kg_depg" || -d "$kg_depg" ]] || die "depgraph dir not found: $kg_depg"
    [[ -z "$kg_logg" || -d "$kg_logg" ]] || die "logigraph dir not found: $kg_logg"

    # Locate the cascade script. Resolve from this install.sh's location so
    # it works against both the source checkout and the installed target.
    local script_path
    script_path="$(cd "$(dirname "$0")" && pwd)/bin/kg-prepush-cascade"
    [[ -f "$script_path" ]] || die "kg-prepush-cascade script missing at $script_path"

    local hook_path="$target_repo/.git/hooks/pre-push"
    local generated
    generated=$(cat <<EOF
#!/bin/bash
# pre-push hook installed by knowledge-graph install.sh cascade.
# Cascades regen + commit + push to the KG corpora when this repo pushes.
export KG_DEPGRAPH_DIR="${kg_depg}"
export KG_LOGIGRAPH_DIR="${kg_logg}"
exec "${script_path}" "\$@"
EOF
)

    if [[ $apply -eq 0 ]]; then
        printf '%s\n' "$generated"
        log "(not written — pass --apply to install at $hook_path)"
        return 0
    fi

    if [[ -e "$hook_path" && $force -eq 0 ]]; then
        # If existing file already matches what we'd write, no-op
        if [[ "$(cat "$hook_path")" == "$generated" ]]; then
            ok "pre-push hook already in place: $hook_path"
            return 0
        fi
        backup_file "$hook_path"
        warn "existing pre-push hook backed up; pass --force to skip backup next time"
    fi

    printf '%s\n' "$generated" >"$hook_path"
    chmod +x "$hook_path"
    ok "installed pre-push hook: $hook_path"
    log "  KG depgraph:  ${kg_depg:-(unset)}"
    log "  KG logigraph: ${kg_logg:-(unset)}"
}


# ----- dispatch -------------------------------------------------------------

main() {
    if [[ $# -eq 0 ]]; then
        cmd_install
        return
    fi
    local cmd="$1"
    case "$cmd" in
        --help|-h)              shift; usage ;;
        --target|--data)        cmd_install "$@" ;;
        init)                   shift; cmd_init "$@" ;;
        hooks)                  shift; cmd_hooks "$@" ;;
        systemd)                shift; cmd_systemd "$@" ;;
        path)                   shift; cmd_path "$@" ;;
        install)                shift; cmd_install "$@" ;;
        cascade)                shift; cmd_cascade "$@" ;;
        bootstrap)              shift; cmd_bootstrap "$@" ;;
        *)                      err "unknown command: $cmd"; usage; exit 1 ;;
    esac
}

main "$@"
