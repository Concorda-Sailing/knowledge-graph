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
#   ./install.sh hooks [--project <dir>] [--apply]
#                                             print (or write) the
#                                             ~/.claude/settings.json hook snippet
#   ./install.sh systemd [--project <dir>] [--apply]
#                                             print (or write) graphui systemd unit
#
#   ./install.sh migrate <project-dir>        retrofit an old flat
#                                             <project>/{depgraph,logigraph}
#                                             into <project>/knowledge-graph/
#                                             and rewrite project.toml paths.
#                                             Re-runs hooks+systemd if --apply.
#
#   ./install.sh bootstrap <project-dir>      one-shot: install tools + scaffold
#                                             project (or use existing data) +
#                                             apply hooks + apply systemd.
#                                             Idempotent. Migrates old flat
#                                             layouts in-place.
#
#   ./install.sh --help                       show this help
#
# Safe by default: never overwrites without a backup; never modifies
# ~/.claude/settings.json or systemd units unless --apply is passed.
# Old flat layouts are migrated in-place on re-run (no destructive
# operations without explicit pre-condition checks).

set -euo pipefail

# ----- configuration --------------------------------------------------------

DEFAULT_TARGET="$HOME/tools"
# Default GitHub org for framework repos; override with KNOWLEDGE_GRAPH_ORG env.
ORG="${KNOWLEDGE_GRAPH_ORG:-Concorda-Sailing}"
FRAMEWORK_REPOS=("depgraph" "logigraph" "graphui")
# All framework repos and project data dirs live one level deep under
# this bundle dir, so a tools install or a project init produces a
# single new directory rather than a scatter. See migrate_*_layout for
# the in-place migration from the old flat layout.
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
    sed -n '2,36p' "$0" | sed 's/^# \{0,1\}//'
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

# ----- layout migration -----------------------------------------------------
#
# Older installs used a flat layout: framework repos sat next to each
# other under $target (and project data sat flat under $project). The
# bundle layout puts everything one level deeper under $BUNDLE_DIR so a
# single subdirectory contains the whole knowledge-graph install. These
# helpers are idempotent — they detect old-flat vs new-bundled and only
# act if migration is needed. Pre-conditions are checked strictly; on
# any conflict they bail with a clear error rather than overwrite.

# Move flat $target/{depgraph,logigraph,graphui} → $target/$BUNDLE_DIR/{...}.
# No-op if any framework repo already lives under the bundle.
migrate_tools_layout() {
    local target="$1"
    local bundle="$target/$BUNDLE_DIR"

    # If anything is already inside the bundle, this looks like a
    # previously-migrated (or freshly-installed) layout — nothing to do.
    local already_bundled=0
    local repo
    for repo in "${FRAMEWORK_REPOS[@]}"; do
        [[ -d "$bundle/$repo" ]] && already_bundled=1
    done
    [[ "$already_bundled" -eq 1 ]] && return 0

    # Find which (if any) flat repos exist. If none, there is nothing
    # to migrate — caller will clone fresh into the bundle.
    local present=()
    for repo in "${FRAMEWORK_REPOS[@]}"; do
        [[ -d "$target/$repo" ]] && present+=("$repo")
    done
    [[ ${#present[@]} -gt 0 ]] || return 0

    warn "migrating flat tools layout $target/{$(IFS=,; echo "${present[*]}")} → $bundle/"

    # If $bundle doesn't exist yet, create it. If it exists (e.g. as the
    # orchestrator checkout), we just mv into it.
    mkdir -p "$bundle"

    for repo in "${present[@]}"; do
        # mv -n refuses to overwrite. If a dest exists, that means a
        # partial prior migration — bail rather than fight it.
        if [[ -e "$bundle/$repo" ]]; then
            die "migration aborted: $bundle/$repo already exists (partial prior migration?); resolve manually"
        fi
        mv "$target/$repo" "$bundle/$repo"
        ok "mv $target/$repo → $bundle/$repo"
    done

    # graphui's .venv bakes absolute paths into shebangs and activate
    # scripts — moving the venv leaves them pointing at the old location.
    # Rebuild it in-place. requirements.txt is the source of truth.
    if [[ -d "$bundle/graphui" && -f "$bundle/graphui/requirements.txt" ]]; then
        log "rebuilding graphui venv (mv invalidates baked-in shebang paths)"
        rm -rf "$bundle/graphui/.venv"
        python3 -m venv "$bundle/graphui/.venv"
        "$bundle/graphui/.venv/bin/pip" install --quiet -r "$bundle/graphui/requirements.txt"
        ok "graphui venv rebuilt at $bundle/graphui/.venv"
    fi

    warn "tools layout migrated. Existing ~/.claude/settings.json hooks and graphui systemd unit reference the OLD paths and will fail until regenerated."
    warn "Re-run with 'hooks --project <project-dir> --apply --force' and 'systemd --project <project-dir> --apply' to fix, or use 'bootstrap <project-dir>' to handle both at once."
}

# Move flat $project/{depgraph,logigraph} → $project/$BUNDLE_DIR/{...} and
# rewrite paths that reference the old layout:
#  - logigraph/project.toml [depgraph] data_dir
#  - any [repos.*] paths that point at $HOME/tools/{framework-repo}
#    (these become $HOME/tools/$BUNDLE_DIR/{framework-repo}, used by
#    knowledge-graph-meta to track the framework itself).
migrate_project_layout() {
    local project="$1"
    [[ -n "$project" && -d "$project" ]] || return 0
    local bundle="$project/$BUNDLE_DIR"

    local already_bundled=0
    [[ -d "$bundle/depgraph" || -d "$bundle/logigraph" ]] && already_bundled=1
    # Even if already bundled, still rewrite framework [repos.*] paths
    # below — a project might have been bundled before the framework
    # tools were, leaving those repo paths pointing at the old flat
    # tools layout.

    if [[ "$already_bundled" -eq 0 ]]; then
        local present=()
        [[ -d "$project/depgraph" ]] && present+=("depgraph")
        [[ -d "$project/logigraph" ]] && present+=("logigraph")
        [[ ${#present[@]} -gt 0 ]] || return 0

        warn "migrating flat project layout $project/{$(IFS=,; echo "${present[*]}")} → $bundle/"
        mkdir -p "$bundle"
        local d
        for d in "${present[@]}"; do
            if [[ -e "$bundle/$d" ]]; then
                die "migration aborted: $bundle/$d already exists (partial prior migration?); resolve manually"
            fi
            mv "$project/$d" "$bundle/$d"
            ok "mv $project/$d → $bundle/$d"
        done
    fi

    # Rewrite paths inside the bundled project.toml files. Two distinct
    # rewrites, both idempotent (skip if pattern not present, skip if
    # already rewritten).
    local lp="$bundle/logigraph/project.toml"
    local dp="$bundle/depgraph/project.toml"

    # 1. logigraph [depgraph] data_dir = "<X>/depgraph"
    #    → "<X>/$BUNDLE_DIR/depgraph" (where <X> is the project root, in
    #    either tilde-expanded or absolute form).
    if [[ -f "$lp" ]] && ! grep -q "data_dir = \"[^\"]*/$BUNDLE_DIR/depgraph\"" "$lp"; then
        if grep -q '^data_dir = ".*\/depgraph"$' "$lp"; then
            sed -i -E "s|^(data_dir = \".*)(/depgraph\")$|\1/$BUNDLE_DIR\2|" "$lp"
            ok "rewrote $lp [depgraph] data_dir → bundled path"
        fi
    fi

    # 2. [repos.*] path entries pointing at the flat tools layout, e.g.
    #    path = "~/tools/depgraph" → "~/tools/$BUNDLE_DIR/depgraph".
    #    Only rewrite values whose basename exactly matches a framework
    #    repo — so a project that legitimately has a repo named
    #    "depgraph-fork" elsewhere isn't touched.
    local f r
    for f in "$lp" "$dp"; do
        [[ -f "$f" ]] || continue
        for r in "${FRAMEWORK_REPOS[@]}"; do
            # Skip if already bundled in this file.
            grep -q "path = \"[^\"]*/$BUNDLE_DIR/$r\"" "$f" && continue
            # Match path = "<X>/$r" where <X> is anything not containing
            # the bundle segment already.
            if grep -qE "^path = \"[^\"]*/${r}\"$" "$f"; then
                sed -i -E "s|^(path = \".*)(/${r}\")$|\1/$BUNDLE_DIR\2|" "$f"
                ok "rewrote $f [repos.*] path → bundled $r"
            fi
        done
    done
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
    migrate_tools_layout "$target"
    mkdir -p "$bundle"
    log "installing into $(color_yellow "$bundle")"

    # Framework repos
    for repo in "${FRAMEWORK_REPOS[@]}"; do
        clone_or_pull "https://github.com/$ORG/$repo.git" "$bundle/$repo"
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
        # If the data repo was cloned to a project root that still has a
        # flat $project/{depgraph,logigraph} layout, migrate it on the
        # spot so all downstream hooks and systemd point at the bundled
        # paths. Idempotent: no-op if already bundled.
        migrate_project_layout "$cloned_path"
    done

    echo
    ok "install complete"
    if [[ ${#extra_data[@]} -gt 0 ]]; then
        echo
        cat <<NEXT
$(color_yellow "Next:")

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
  2. Print the hook snippet:                $0 hooks
  3. (Optional) Register graphui daemon:    $0 systemd

  Or one-shot:                              $0 bootstrap ~/your-project
NEXT
    fi
}

cmd_init() {
    local project_dir="${1:-}"
    [[ -n "$project_dir" ]] || die "usage: $0 init <project-data-dir>"
    [[ "$project_dir" = /* ]] || project_dir="$PWD/$project_dir"
    # Adopt an existing flat layout into the bundle before refusing on a
    # conflict — re-running `init` against a pre-bundled project should
    # rescue it, not error out.
    migrate_project_layout "$project_dir"
    local bundle="$project_dir/$BUNDLE_DIR"
    [[ ! -e "$bundle/depgraph" ]] || die "$bundle/depgraph already exists; refusing to overwrite"

    log "scaffolding project at $(color_yellow "$bundle")"
    local pname
    pname=$(basename "$project_dir")

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

  Apply Claude Code hooks pointing at this project:
    $0 hooks --project $project_dir --apply

  Or print the snippet to merge by hand:
    $0 hooks --project $project_dir
NEXT
}

# ----- hooks: print or apply -----------------------------------------------

generate_hooks_json() {
    # $target is the tools target (e.g. ~/tools); hooks/extractors live
    # one level deeper under $BUNDLE_DIR. Data dirs ($depg, $logg) are
    # already passed in as their fully-qualified bundled paths by the
    # caller, so don't re-rewrite them here.
    local target="$1" depg="$2" logg="$3"
    local bundle="$target/$BUNDLE_DIR"
    cat <<JSON
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [
        {
          "type": "command",
          "command": "DEPGRAPH_DATA_DIR=$depg python3 $bundle/depgraph/hooks/pre_edit_inject.py",
          "timeout": 5
        },
        {
          "type": "command",
          "command": "LOGIGRAPH_DATA_DIR=$logg DEPGRAPH_DATA_DIR=$depg python3 $bundle/logigraph/hooks/pre_edit_inject.py",
          "timeout": 5
        }
      ]
    },
    {
      "matcher": "Bash|mcp__.*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 $bundle/logigraph/hooks/pre_irreversible_inject.py",
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
          "command": "DEPGRAPH_DATA_DIR=$depg python3 $bundle/depgraph/hooks/post_edit_regen.py",
          "timeout": 60
        },
        {
          "type": "command",
          "command": "DEPGRAPH_DATA_DIR=$depg python3 $bundle/depgraph/hooks/post_edit_telemetry.py",
          "timeout": 30
        },
        {
          "type": "command",
          "command": "LOGIGRAPH_DATA_DIR=$logg python3 $bundle/logigraph/hooks/post_edit_telemetry.py",
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
    local depg="$project/$BUNDLE_DIR/depgraph"
    local logg="$project/$BUNDLE_DIR/logigraph"

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

# ----- migrate: retrofit an old flat project layout into the bundle -------

cmd_migrate() {
    local project=""
    local target="$DEFAULT_TARGET"
    local apply=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)  target="$2"; shift 2 ;;
            --apply)   apply=1; shift ;;
            -*) die "unknown flag: $1" ;;
            *) [[ -z "$project" ]] || die "multiple project dirs given"; project="$1"; shift ;;
        esac
    done
    [[ -n "$project" ]] || die "usage: $0 migrate <project-dir> [--apply]"
    [[ "$project" = /* ]] || project="$PWD/$project"
    [[ -d "$project" ]] || die "no such directory: $project"

    log "migrating project at $(color_yellow "$project")"

    # Migration of the tools dir is the user's call (different scope);
    # do it here only if the flat layout is detected at $target so the
    # rewritten [repos.*] paths inside the project actually resolve.
    migrate_tools_layout "$target"
    migrate_project_layout "$project"
    echo

    if [[ "$apply" -eq 1 ]]; then
        log "applying Claude Code hooks → $SETTINGS_FILE"
        cmd_hooks --target "$target" --project "$project" --apply --force
        echo
        log "applying systemd unit for graphui"
        cmd_systemd --target "$target" --project "$project" --apply
        echo
    else
        cat <<NEXT
$(color_yellow "Next:") regenerate hooks + systemd so they reference the bundled paths:

  $0 hooks   --target $target --project $project --apply --force
  $0 systemd --target $target --project $project --apply

Or re-run with --apply to do both automatically.
NEXT
    fi
    ok "migrate complete"
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

    # Adopt an existing flat $project/{depgraph,logigraph} into the bundle
    # so the rest of bootstrap (hooks + systemd + scaffolding decision)
    # sees a uniform $project/$BUNDLE_DIR/{...} shape.
    migrate_project_layout "$project"

    # If the project doesn't have a data layout yet, scaffold it. Otherwise
    # use what's there (e.g. cloned via --data, or just migrated above).
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

    log "applying systemd unit for graphui"
    cmd_systemd --project "$project" --apply
    echo

    ok "bootstrap complete"
    cat <<DONE

  Tools:                       $DEFAULT_TARGET/$BUNDLE_DIR/{depgraph,logigraph,graphui}/
  Project data:                $project/$BUNDLE_DIR/{depgraph,logigraph}/
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
        --target|--data)        cmd_install "$@" ;;
        init)                   shift; cmd_init "$@" ;;
        hooks)                  shift; cmd_hooks "$@" ;;
        systemd)                shift; cmd_systemd "$@" ;;
        install)                shift; cmd_install "$@" ;;
        migrate)                shift; cmd_migrate "$@" ;;
        bootstrap)              shift; cmd_bootstrap "$@" ;;
        *)                      err "unknown command: $cmd"; usage; exit 1 ;;
    esac
}

main "$@"
