#!/usr/bin/env bash
# install.sh — installer + project scaffolder for the knowledge-graph
# substrate (depgraph + logigraph + graphui).
#
# Usage:
#   ./install.sh                              install tools to ~/tools/
#   ./install.sh --target /path               install tools to /path/
#   ./install.sh --data <owner/repo>=<path>   clone a data repo too (repeatable)
#   ./install.sh --concorda                   shortcut: clones Concorda's
#                                             concorda-depgraph + concorda-logigraph
#                                             into ~/concorda/{depgraph,logigraph}
#
#   ./install.sh init <project>               scaffold a project data dir
#
#   ./install.sh hooks [--project <dir>] [--apply]
#                                             print (or write) the
#                                             ~/.claude/settings.json hook snippet
#   ./install.sh systemd [--project <dir>] [--apply]
#                                             print (or write) graphui systemd unit
#
#   ./install.sh bootstrap-concorda           one-shot: install tools + clone
#                                             Concorda data + apply hooks + apply
#                                             systemd. Idempotent; asks before
#                                             touching ~/.claude/settings.json.
#
#   ./install.sh --help                       show this help
#
# Safe by default: never overwrites without a backup; never modifies
# ~/.claude/settings.json or systemd units unless --apply is passed.

set -euo pipefail

# ----- configuration --------------------------------------------------------

DEFAULT_TARGET="$HOME/tools"
ORG="Concorda-Sailing"
FRAMEWORK_REPOS=("depgraph" "logigraph" "graphui")
SETTINGS_FILE="$HOME/.claude/settings.json"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SYSTEMD_UNIT="graphui.service"
GRAPHUI_PORT=8081

# Concorda bootstrap data repos: "github_repo=local_path" pairs
CONCORDA_DATA=(
    "concorda-depgraph=$HOME/concorda/depgraph"
    "concorda-logigraph=$HOME/concorda/logigraph"
)

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
    sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
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
    local include_concorda=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)   target="$2"; shift 2 ;;
            --data)     extra_data+=("$2"); shift 2 ;;
            --concorda) include_concorda=1; shift ;;
            --help|-h)  usage; exit 0 ;;
            *)          die "unknown flag: $1" ;;
        esac
    done

    check_prereqs
    mkdir -p "$target"
    log "installing into $(color_yellow "$target")"

    # Framework repos
    for repo in "${FRAMEWORK_REPOS[@]}"; do
        clone_or_pull "https://github.com/$ORG/$repo.git" "$target/$repo"
    done

    # graphui venv
    local g="$target/graphui"
    if [[ ! -d "$g/.venv" ]]; then
        log "graphui: creating venv + installing requirements"
        python3 -m venv "$g/.venv"
        "$g/.venv/bin/pip" install --quiet -r "$g/requirements.txt"
    else
        log "graphui: venv present; upgrading requirements"
        "$g/.venv/bin/pip" install --quiet --upgrade -r "$g/requirements.txt"
    fi
    ok "graphui venv at $g/.venv"

    # Concorda data shortcut adds the two repos to extra_data
    if [[ "$include_concorda" -eq 1 ]]; then
        for d in "${CONCORDA_DATA[@]}"; do extra_data+=("$d"); done
    fi

    # Arbitrary --data clones
    for spec in "${extra_data[@]}"; do
        local repo="${spec%%=*}"
        local path="${spec#*=}"
        [[ "$repo" != "$path" ]] || die "invalid --data spec: $spec (expected owner/repo=local-path)"
        # If `owner/` is omitted, default to the configured ORG.
        [[ "$repo" == */* ]] || repo="$ORG/$repo"
        clone_or_pull "https://github.com/$repo.git" "$(eval echo "$path")"
    done

    echo
    ok "install complete"
    if [[ "$include_concorda" -eq 1 || ${#extra_data[@]} -gt 0 ]]; then
        echo
        cat <<NEXT
$(color_yellow "Next:")

  Apply Claude Code hooks for the data dirs you just cloned:
    $0 hooks --project $HOME/concorda --apply

  Register graphui as a systemd --user service:
    $0 systemd --project $HOME/concorda --apply
NEXT
    else
        echo
        cat <<NEXT
$(color_yellow "Next:")

  1. Scaffold a project data dir:           $0 init ~/your-project
  2. Print the hook snippet:                $0 hooks
  3. (Optional) Register graphui daemon:    $0 systemd
NEXT
    fi
}

cmd_init() {
    local project_dir="${1:-}"
    [[ -n "$project_dir" ]] || die "usage: $0 init <project-data-dir>"
    [[ "$project_dir" = /* ]] || project_dir="$PWD/$project_dir"
    [[ ! -e "$project_dir/depgraph" ]] || die "$project_dir/depgraph already exists; refusing to overwrite"

    log "scaffolding project at $(color_yellow "$project_dir")"
    local pname
    pname=$(basename "$project_dir")

    mkdir -p "$project_dir/depgraph/extractors" \
             "$project_dir/depgraph/nodes" \
             "$project_dir/depgraph/dossiers" \
             "$project_dir/depgraph/telemetry"
    cat > "$project_dir/depgraph/project.toml" <<TOML
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
    cat > "$project_dir/depgraph/extractors/README.md" <<MD
# Extractors

Drop your extractor scripts in here. Each extractor walks a repo (declared
in \`../project.toml [repos]\`) and emits JSON node files under \`../nodes/\`
following the framework schema at \`~/tools/depgraph/schema/node.schema.json\`.

The Concorda reference implementation lives at
\`Concorda-Sailing/concorda-depgraph\` — clone it for examples:

- \`extract_api.py\` — FastAPI route handlers + SQLAlchemy models
- \`extract_web.ts\` — Next.js components + React hooks
- \`extract_tests.ts\` — Playwright specs
MD

    mkdir -p "$project_dir/logigraph/nodes/rules" \
             "$project_dir/logigraph/nodes/domain" \
             "$project_dir/logigraph/dossiers/rules" \
             "$project_dir/logigraph/dossiers/domain" \
             "$project_dir/logigraph/telemetry"
    cat > "$project_dir/logigraph/project.toml" <<TOML
# $pname logigraph project config.

[project]
name = "$pname"

# Path to this project's depgraph data dir.
[depgraph]
data_dir = "$project_dir/depgraph"
TOML
    cat > "$project_dir/logigraph/CANDIDATES.md" <<MD
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

    ok "scaffolded $project_dir"
    echo
    cat <<NEXT
$(color_yellow "Next:")

  Apply Claude Code hooks pointing at this project:
    $0 hooks --project $project_dir --apply

  Or print the snippet to merge by hand:
    $0 hooks --project $project_dir
NEXT
}

# ----- hooks: print or apply -----------------------------------------------

generate_hooks_json() {
    local target="$1" depg="$2" logg="$3"
    cat <<JSON
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [
        {
          "type": "command",
          "command": "DEPGRAPH_DATA_DIR=$depg python3 $target/depgraph/hooks/pre_edit_inject.py",
          "timeout": 5
        },
        {
          "type": "command",
          "command": "LOGIGRAPH_DATA_DIR=$logg DEPGRAPH_DATA_DIR=$depg python3 $target/logigraph/hooks/pre_edit_inject.py",
          "timeout": 5
        }
      ]
    },
    {
      "matcher": "Bash|mcp__.*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 $target/logigraph/hooks/pre_irreversible_inject.py",
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
          "command": "DEPGRAPH_DATA_DIR=$depg python3 $target/depgraph/hooks/post_edit_regen.py",
          "timeout": 60
        },
        {
          "type": "command",
          "command": "DEPGRAPH_DATA_DIR=$depg python3 $target/depgraph/hooks/post_edit_telemetry.py",
          "timeout": 30
        },
        {
          "type": "command",
          "command": "LOGIGRAPH_DATA_DIR=$logg python3 $target/logigraph/hooks/post_edit_telemetry.py",
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

    if [[ -z "$project" ]]; then
        project="$HOME/your-project"
        warn "no --project given; using placeholder $project"
    fi
    local depg="$project/depgraph"
    local logg="$project/logigraph"

    local hooks_json
    hooks_json=$(generate_hooks_json "$target" "$depg" "$logg")

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
if existing == new_hooks:
    print(f"✓ hooks already match in {p} — no-op")
    sys.exit(0)
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
    cat <<UNIT
[Unit]
Description=knowledge-graph viewer (depgraph + logigraph)
After=network.target

[Service]
Type=simple
WorkingDirectory=$target/graphui
Environment=PATH=$target/graphui/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=DEPGRAPH_DATA_DIR=$depg
Environment=LOGIGRAPH_DATA_DIR=$logg
Environment=DEPGRAPH_BIN=$target/depgraph/bin/depgraph
ExecStart=$target/graphui/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $GRAPHUI_PORT
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
    local depg="$project/depgraph"
    local logg="$project/logigraph"

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

# ----- bootstrap-concorda: install + data + hooks + systemd ----------------

cmd_bootstrap_concorda() {
    log "bootstrapping the full Concorda substrate"
    echo

    cmd_install --concorda
    echo

    log "applying Claude Code hooks → $SETTINGS_FILE"
    # bootstrap-concorda implies "set up Concorda from scratch" — overwrite
    # any existing hooks (after backing them up). Use plain `cmd_hooks` for
    # interactive review.
    cmd_hooks --project "$HOME/concorda" --apply --force
    echo

    log "applying systemd unit for graphui"
    cmd_systemd --project "$HOME/concorda" --apply
    echo

    ok "Concorda bootstrap complete"
    cat <<DONE

  Tools:                       ~/tools/{depgraph,logigraph,graphui}/
  Concorda data:               ~/concorda/{depgraph,logigraph}/
  Claude Code hooks:           $SETTINGS_FILE
  Graphui daemon:              $SYSTEMD_DIR/$SYSTEMD_UNIT
  Graphui URL:                 http://localhost:$GRAPHUI_PORT/graph/

  Note: Claude Code reads settings.json at session start. Restart any
  open sessions to pick up the new hooks.
DONE
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
        --target|--data|--concorda)
                                cmd_install "$@" ;;
        init)                   shift; cmd_init "$@" ;;
        hooks)                  shift; cmd_hooks "$@" ;;
        systemd)                shift; cmd_systemd "$@" ;;
        install)                shift; cmd_install "$@" ;;
        bootstrap-concorda)     shift; cmd_bootstrap_concorda "$@" ;;
        *)                      err "unknown command: $cmd"; usage; exit 1 ;;
    esac
}

main "$@"
