#!/usr/bin/env bash
# install.sh — back-compat alias. Real implementation lives in kg.cli.install.
#
# Phase 4 of the consolidated-kg-CLI rework ported all install
# subcommands (init, tools, hooks, systemd, path, cascade, bootstrap)
# to Python. This script remains as a thin alias so external callers
# (docs, muscle memory, the prior dev-box bootstrap pattern) keep
# working unchanged.

set -euo pipefail
TOOL_ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$TOOL_ROOT/bin/kg" install "$@"
