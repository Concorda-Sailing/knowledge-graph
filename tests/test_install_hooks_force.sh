#!/usr/bin/env bash
# Regression test for the hooks-clobber bug.
#
# Bug: `install.sh hooks --apply --force` did `settings["hooks"] = new_hooks`,
# which discards any existing hook entries install.sh doesn't itself generate
# (user-authored hooks, other-project hooks, etc.). Triggered today via
# bootstrap/migrate, which invoke cmd_hooks --apply --force unconditionally.
#
# Expected behavior: refuse-and-print-diff. Even under --force, if existing
# settings.json contains hook entries that aren't in the about-to-be-written
# block, exit non-zero, leave the file untouched, and print which entries
# would have been lost.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_SH="$SCRIPT_DIR/../install.sh"
[[ -x "$INSTALL_SH" ]] || { echo "install.sh not executable at $INSTALL_SH" >&2; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Isolated HOME. The script writes to $HOME/.claude/settings.json, so
# overriding HOME (not just SETTINGS_FILE) is the cleanest sandbox.
export HOME="$TMP"
mkdir -p "$HOME/.claude"

# Seed a settings.json with a hook that install.sh would NEVER generate:
# a Notification matcher with an unrelated user command. install.sh only
# generates PreToolUse (Edit|Write|MultiEdit + Bash|mcp__.*) and Stop blocks.
cat > "$HOME/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Notification",
        "hooks": [
          {"type": "command", "command": "echo user-custom-hook", "timeout": 5}
        ]
      }
    ]
  }
}
JSON

# Snapshot for post-run comparison.
cp "$HOME/.claude/settings.json" "$TMP/before.json"

# Run the apply-with-force flow. Because the seed file has entries beyond
# what install.sh generates, this MUST refuse.
set +e
out=$("$INSTALL_SH" hooks \
    --target "$TMP/tools" \
    --project "$TMP/anywhere" \
    --apply --force 2>&1)
rc=$?
set -e

fail() {
    echo "FAIL: $1" >&2
    echo "----- captured output -----" >&2
    printf '%s\n' "$out" >&2
    echo "---------------------------" >&2
    exit 1
}

[[ $rc -ne 0 ]] || fail "expected non-zero exit when existing settings has hooks beyond what install.sh would generate; got rc=$rc"

# File must be byte-identical to the snapshot — no partial writes, no backup
# swap, nothing.
if ! diff -q "$TMP/before.json" "$HOME/.claude/settings.json" >/dev/null; then
    echo "FAIL: settings.json was modified despite the refusal:" >&2
    diff "$TMP/before.json" "$HOME/.claude/settings.json" >&2 || true
    exit 1
fi

# Refusal message must surface what would have been lost, so the operator
# can decide whether to back up and proceed manually.
grep -qi 'would.*lose\|would.*drop\|beyond what\|extra' <<<"$out" \
    || fail "refusal output did not name what would be lost"

# The unrelated Notification hook should appear by command, matcher, or both.
grep -q 'user-custom-hook\|Notification' <<<"$out" \
    || fail "refusal output did not identify the specific lost entry (user-custom-hook / Notification)"

echo "PASS: refuses to clobber rich hooks under --force, file untouched, diff printed"
