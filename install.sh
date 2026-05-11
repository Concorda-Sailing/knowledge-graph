#!/usr/bin/env bash
# install.sh — installer + project scaffolder for the knowledge-graph
# substrate (depgraph + logigraph + graphui).
#
# Usage:
#   ./install.sh                   # install tools to ~/tools/
#   ./install.sh --target /path    # install to /path/{depgraph,logigraph,graphui}
#   ./install.sh init <project>    # scaffold a project data dir at <project>
#   ./install.sh hooks             # print the ~/.claude/settings.json hook snippet
#   ./install.sh systemd           # print the graphui systemd --user unit
#   ./install.sh --help            # show this help
#
# Safe by default: never overwrites existing files; never modifies
# ~/.claude/settings.json or systemd units without explicit consent
# (you copy/paste the printed snippets).

set -euo pipefail

# ----- configuration --------------------------------------------------------

DEFAULT_TARGET="$HOME/tools"
ORG="Concorda-Sailing"
REPOS=("depgraph" "logigraph" "graphui")

# ----- helpers --------------------------------------------------------------

color_red()    { printf '\033[31m%s\033[0m' "$*"; }
color_green()  { printf '\033[32m%s\033[0m' "$*"; }
color_yellow() { printf '\033[33m%s\033[0m' "$*"; }
color_dim()    { printf '\033[2m%s\033[0m' "$*"; }

log()    { printf '%s %s\n' "$(color_dim "·")" "$*"; }
ok()     { printf '%s %s\n' "$(color_green "✓")" "$*"; }
warn()   { printf '%s %s\n' "$(color_yellow "⚠")" "$*" >&2; }
err()    { printf '%s %s\n' "$(color_red "✗")" "$*" >&2; }
die()    { err "$*"; exit 1; }

usage() {
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
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
        *) die "python 3.10+ required (found $pyver) — tomllib is stdlib from 3.11; project.toml parsing needs it" ;;
    esac
    ok "git + python $pyver"
}

# ----- subcommands ----------------------------------------------------------

cmd_install() {
    local target="$DEFAULT_TARGET"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target) target="$2"; shift 2 ;;
            --help|-h) usage; exit 0 ;;
            *) die "unknown flag: $1" ;;
        esac
    done

    check_prereqs
    mkdir -p "$target"
    log "installing into $(color_yellow "$target")"

    for repo in "${REPOS[@]}"; do
        local dir="$target/$repo"
        local url="https://github.com/$ORG/$repo.git"
        if [[ -d "$dir/.git" ]]; then
            log "$repo: present; pulling latest"
            (cd "$dir" && git pull --quiet --ff-only 2>&1 | sed 's/^/    /')
        else
            log "$repo: cloning $url"
            git clone --quiet "$url" "$dir"
        fi
        ok "$repo at $dir"
    done

    # graphui needs a python venv for its FastAPI server
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

    echo
    ok "install complete"
    echo
    cat <<NEXT
$(color_yellow "Next steps:")

  1. Scaffold a project data dir:
       $0 init ~/your-project

  2. Print the Claude Code hooks snippet to add to
     ~/.claude/settings.json (so depgraph + logigraph fire on edits):
       $0 hooks

  3. (Optional) Run the graphui viewer:
       cd $g && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8081

     Or register it as a systemd --user service:
       $0 systemd
NEXT
}

cmd_init() {
    local project_dir="${1:-}"
    [[ -n "$project_dir" ]] || die "usage: $0 init <project-data-dir>"
    [[ "$project_dir" = /* ]] || project_dir="$PWD/$project_dir"
    [[ ! -e "$project_dir/depgraph" ]] || die "$project_dir/depgraph already exists; refusing to overwrite"

    log "scaffolding project at $(color_yellow "$project_dir")"
    local pname
    pname=$(basename "$project_dir")

    # depgraph data dir
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

Examples in the Concorda reference implementation
(\`Concorda-Sailing/concorda-depgraph\` once published):

- \`extract_api.py\` — FastAPI route handlers + SQLAlchemy models
- \`extract_web.ts\` — Next.js components + React hooks
- \`extract_tests.ts\` — Playwright specs
MD

    # logigraph data dir
    mkdir -p "$project_dir/logigraph/nodes/rules" \
             "$project_dir/logigraph/nodes/domain" \
             "$project_dir/logigraph/dossiers/rules" \
             "$project_dir/logigraph/dossiers/domain" \
             "$project_dir/logigraph/telemetry"
    cat > "$project_dir/logigraph/project.toml" <<TOML
# $pname logigraph project config.

[project]
name = "$pname"

# Path to this project's depgraph data dir (logigraph rules claim
# against depgraph node ids).
[depgraph]
data_dir = "$project_dir/depgraph"
TOML
    cat > "$project_dir/logigraph/CANDIDATES.md" <<MD
# Rule candidates

This file is the human notebook for rules that should be authored.
Add candidates as you discover them; remove (or strike through) once
authored via \`~/tools/logigraph/bin/logigraph rule-stub\`.

Format per candidate:

\`\`\`
### rule::category::short_name
- statement: one-sentence rule
- why: motivation + history (incident, commit, ADR)
- surfaces: file:line refs of where the rule is enforced
- confidence: high | medium | low
\`\`\`
MD

    ok "scaffolded $project_dir"
    echo
    cat <<NEXT
$(color_yellow "Next:")

  Set these env vars whenever you run the tools or wire them into
  ~/.claude/settings.json (see '$0 hooks'):

    export DEPGRAPH_DATA_DIR=$project_dir/depgraph
    export LOGIGRAPH_DATA_DIR=$project_dir/logigraph

  First regen (after you write your first extractor):
    \$(realpath ~/tools/depgraph/bin/depgraph) regen

  Validate:
    \$(realpath ~/tools/logigraph/bin/logigraph) validate
NEXT
}

cmd_hooks() {
    local target="$DEFAULT_TARGET"
    [[ "${1:-}" != "--target" ]] || { target="$2"; shift 2; }
    cat <<HOOKS
# Add the following to your ~/.claude/settings.json under "hooks":
#
# (Replace \$HOME/your-project with the project data dir you scaffolded
# via '$0 init'.)
#
# This snippet wires the PreToolUse and Stop hooks for both graphs.
# Multiple projects? Add more hook blocks with different DATA_DIR env
# vars per project; you can match them by file path via additional
# matchers if needed.

{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "DEPGRAPH_DATA_DIR=\$HOME/your-project/depgraph python3 $target/depgraph/hooks/pre_edit_inject.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "LOGIGRAPH_DATA_DIR=\$HOME/your-project/logigraph DEPGRAPH_DATA_DIR=\$HOME/your-project/depgraph python3 $target/logigraph/hooks/pre_edit_inject.py",
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
            "command": "DEPGRAPH_DATA_DIR=\$HOME/your-project/depgraph python3 $target/depgraph/hooks/post_edit_regen.py",
            "timeout": 60
          },
          {
            "type": "command",
            "command": "DEPGRAPH_DATA_DIR=\$HOME/your-project/depgraph python3 $target/depgraph/hooks/post_edit_telemetry.py",
            "timeout": 30
          },
          {
            "type": "command",
            "command": "LOGIGRAPH_DATA_DIR=\$HOME/your-project/logigraph python3 $target/logigraph/hooks/post_edit_telemetry.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
HOOKS
}

cmd_systemd() {
    local target="$DEFAULT_TARGET"
    [[ "${1:-}" != "--target" ]] || { target="$2"; shift 2; }
    cat <<UNIT
# Write the following to ~/.config/systemd/user/graphui.service and run:
#   systemctl --user daemon-reload && systemctl --user enable --now graphui
#
# (Replace DEPGRAPH_DATA_DIR / LOGIGRAPH_DATA_DIR with your project's
# data dirs.)

[Unit]
Description=knowledge-graph viewer (depgraph + logigraph)
After=network.target

[Service]
Type=simple
WorkingDirectory=$target/graphui
Environment=PATH=$target/graphui/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=DEPGRAPH_DATA_DIR=%h/your-project/depgraph
Environment=LOGIGRAPH_DATA_DIR=%h/your-project/logigraph
Environment=DEPGRAPH_BIN=$target/depgraph/bin/depgraph
ExecStart=$target/graphui/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8081
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
UNIT
}

# ----- dispatch -------------------------------------------------------------

main() {
    if [[ $# -eq 0 ]]; then
        cmd_install
        return
    fi
    local cmd="$1"
    shift
    case "$cmd" in
        --help|-h)    usage ;;
        --target)     cmd_install --target "$@" ;;
        init)         cmd_init "$@" ;;
        hooks)        cmd_hooks "$@" ;;
        systemd)      cmd_systemd "$@" ;;
        install)      cmd_install "$@" ;;
        *)            err "unknown command: $cmd"; usage; exit 1 ;;
    esac
}

main "$@"
