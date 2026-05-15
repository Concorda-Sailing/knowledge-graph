"""Tests for the destructive-bash detector.

The hook went from regex-on-raw-string matching to shlex-tokenized
per-segment matching to fix two classes of bug:
  - False positives from quoted substrings (`grep "git push" file`).
  - False negatives from operator-glued chains (`ls; rm -rf x`).

Both are exercised here, plus a representative sample of every pattern
the detector claims to catch. New patterns should add a positive case
AND a quoted-substring negative case.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "hooks"))

from pre_irreversible_inject import detect_bash  # noqa: E402


# ----- positives: things that should flag, one per supported pattern -----


def test_rm_short_flags():
    assert "rm with -r/-f flags" in detect_bash("rm -rf /tmp/foo")
    assert "rm with -r/-f flags" in detect_bash("rm -fR /tmp/foo")


def test_rm_long_flags():
    assert "rm with -r/-f flags" in detect_bash("rm --recursive /tmp/foo")
    assert "rm with -r/-f flags" in detect_bash("rm --force /tmp/foo")


def test_git_push_real():
    assert "git push (real, not dry-run)" in detect_bash("git push origin main")


def test_git_destructive_subcommands():
    assert "git reset --hard" in detect_bash("git reset --hard HEAD")
    assert "git commit --amend (rewrites history)" in detect_bash("git commit --amend")
    assert "git rebase" in detect_bash("git rebase main")
    assert "git branch -D (force-delete)" in detect_bash("git branch -D feature")
    assert "git clean -f" in detect_bash("git clean -fd")


def test_sudo_flags_both_labels():
    """`sudo rm -rf` should flag BOTH sudo AND rm-rf — sudo is recursive."""
    labels = detect_bash("sudo rm -rf /etc")
    assert "sudo (privileged execution)" in labels
    assert "rm with -r/-f flags" in labels


def test_curl_mutating():
    assert "curl with mutating verb" in detect_bash("curl -X POST https://example.com")
    assert "curl with mutating verb" in detect_bash("curl -XDELETE https://example.com")
    assert "curl with --data (POST-shaped)" in detect_bash('curl -d "k=v" https://example.com')


def test_psql_mutating_sql():
    assert "psql mutating SQL" in detect_bash('psql -c "DROP TABLE users"')
    assert "psql mutating SQL" in detect_bash('psql -c "delete from users"')


def test_kubectl_destructive():
    assert "kubectl mutating command" in detect_bash("kubectl delete pod foo")


def test_systemctl_split():
    """Separate labels for system-wide vs --user systemctl."""
    assert "systemctl service control" in detect_bash("systemctl stop nginx")
    assert "systemctl --user service control" in detect_bash("systemctl --user stop nginx")


def test_docker_destructive():
    assert "docker destructive command" in detect_bash("docker rm container")
    assert "docker destructive command" in detect_bash("docker stop container")


def test_aws_action_pattern():
    assert "aws mutating command" in detect_bash("aws s3api delete-bucket --bucket foo")


def test_gcloud_deep_command_shape():
    """Real gcloud commands have variable depth: the verb isn't always rest[1].
    Regression for a refactor bug that pinned the verb to rest[1] only."""
    assert "gcloud mutating command" in detect_bash("gcloud compute instances delete foo")
    assert "gcloud mutating command" in detect_bash("gcloud sql databases create mydb --instance=x")


def test_npm_publish():
    assert "npm publish" in detect_bash("npm publish")


def test_pip_install():
    assert "pip install/uninstall (real)" in detect_bash("pip install requests")


def test_dd_disk_write():
    assert "dd (raw disk write)" in detect_bash("dd if=/dev/zero of=/dev/sda bs=1M")


def test_redirect_block_device():
    assert "redirection to block device" in detect_bash("echo x > /dev/sda")


# ----- negatives: things that look dangerous but aren't -----


def test_rm_without_flags():
    assert detect_bash("rm foo.txt") == []


def test_git_push_dry_run():
    assert detect_bash("git push origin main --dry-run") == []


def test_git_rebase_abort_continue():
    assert detect_bash("git rebase --abort") == []
    assert detect_bash("git rebase --continue") == []


def test_pip_install_dry_run():
    assert detect_bash("pip install --dry-run requests") == []


# ----- false-positive class: dangerous strings inside quoted args -----


def test_quoted_git_push_in_grep():
    """grep'ing for the literal string `git push` should not flag."""
    assert detect_bash('grep "git push" notes.txt') == []


def test_quoted_rm_rf_in_echo():
    assert detect_bash('echo "rm -rf would be bad"') == []


def test_quoted_sudo_in_grep():
    assert detect_bash('cat file | grep "sudo"') == ["curl with --data (POST-shaped)"] or \
        "sudo (privileged execution)" not in detect_bash('cat file | grep "sudo"')


# ----- chained commands: operators must split segments -----


def test_chained_and_push():
    """`git pull && git push` — push is the second segment, must still flag."""
    assert "git push (real, not dry-run)" in detect_bash("git pull && git push")


def test_chained_semicolon_glued():
    """`ls; rm -rf x` (no space before `;`) — shlex.split would miss this;
    shlex.shlex with punctuation_chars catches it. Regression for the
    refactor's first attempt."""
    assert "rm with -r/-f flags" in detect_bash("ls; rm -rf /tmp/x")


def test_chained_pipe_no_space():
    """`cmd1|cmd2` — same shape as above."""
    assert "git push (real, not dry-run)" in detect_bash("echo done|git push")


# ----- robustness: malformed input must not crash -----


def test_unbalanced_quotes_returns_empty():
    """Unparseable shell — return [] rather than crashing or false-flagging."""
    assert detect_bash('echo "unterminated') == []


# ----- block-then-allow flow: first hit denies + writes ack, retry consumes -----


import json as _json
import os as _os
import subprocess as _subprocess
import sys as _sys


_HOOK = REPO / "hooks" / "pre_irreversible_inject.py"


def _invoke_hook(tool_name: str, tool_input: dict, ack_dir: Path, ttl: int = 120):
    env = _os.environ.copy()
    env["KG_PRE_IRREVERSIBLE_ACK_DIR"] = str(ack_dir)
    env["KG_PRE_IRREVERSIBLE_TTL"] = str(ttl)
    payload = {"tool_name": tool_name, "tool_input": tool_input}
    return _subprocess.run(
        [_sys.executable, str(_HOOK)],
        input=_json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def test_first_hit_denies_and_writes_ack(tmp_path):
    """First flagged call: hook must emit permissionDecision=deny and create
    an ack-file keyed by the command hash."""
    ack_dir = tmp_path / "ack"
    r = _invoke_hook("Bash", {"command": "rm -rf /tmp/whatever"}, ack_dir)
    assert r.returncode == 0, r.stderr
    out = _json.loads(r.stdout)
    hso = out["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "Goal" in hso["permissionDecisionReason"]
    acks = list(ack_dir.iterdir())
    assert len(acks) == 1


def test_retry_consumes_ack_and_allows(tmp_path):
    """Second identical call (within TTL) must exit 0 with empty stdout and
    consume the ack-file so a third call would block again."""
    ack_dir = tmp_path / "ack"
    cmd = {"command": "rm -rf /tmp/whatever"}
    first = _invoke_hook("Bash", cmd, ack_dir)
    assert _json.loads(first.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

    second = _invoke_hook("Bash", cmd, ack_dir)
    assert second.returncode == 0
    assert second.stdout.strip() == "", f"expected empty stdout, got: {second.stdout!r}"
    assert list(ack_dir.iterdir()) == []

    # Third call: ack is gone, must block again.
    third = _invoke_hook("Bash", cmd, ack_dir)
    assert _json.loads(third.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_expired_ack_does_not_allow(tmp_path):
    """An ack-file older than TTL should be treated as absent."""
    ack_dir = tmp_path / "ack"
    cmd = {"command": "rm -rf /tmp/whatever"}
    first = _invoke_hook("Bash", cmd, ack_dir, ttl=120)
    assert _json.loads(first.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Backdate the ack-file beyond TTL.
    ack_file = next(ack_dir.iterdir())
    stale = ack_file.stat().st_mtime - 3600
    _os.utime(ack_file, (stale, stale))

    retry = _invoke_hook("Bash", cmd, ack_dir, ttl=120)
    assert _json.loads(retry.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_different_commands_have_independent_acks(tmp_path):
    """Acking command A must not allow command B."""
    ack_dir = tmp_path / "ack"
    a = _invoke_hook("Bash", {"command": "rm -rf /tmp/a"}, ack_dir)
    assert _json.loads(a.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    b = _invoke_hook("Bash", {"command": "rm -rf /tmp/b"}, ack_dir)
    assert _json.loads(b.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert len(list(ack_dir.iterdir())) == 2


def test_non_flagged_command_passes(tmp_path):
    """Non-destructive commands should pass with no output, no ack."""
    ack_dir = tmp_path / "ack"
    r = _invoke_hook("Bash", {"command": "ls /tmp"}, ack_dir)
    assert r.returncode == 0
    assert r.stdout.strip() == ""
    assert not ack_dir.exists() or list(ack_dir.iterdir()) == []


def test_retry_with_different_description_still_consumes_ack(tmp_path):
    """The Bash tool's optional `description` (and `timeout`, etc.) varies
    across retries when the model rewords its narration. The ack key must
    ignore those auxiliary fields, otherwise the legitimate retry misses
    the cache and stays blocked.
    """
    ack_dir = tmp_path / "ack"
    cmd = "rm -rf /tmp/whatever"
    first = _invoke_hook(
        "Bash",
        {"command": cmd, "description": "first try", "timeout": 60000},
        ack_dir,
    )
    assert _json.loads(first.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

    second = _invoke_hook(
        "Bash",
        {"command": cmd, "description": "retry after stating trio", "timeout": 30000},
        ack_dir,
    )
    assert second.returncode == 0
    assert second.stdout.strip() == "", f"expected empty stdout, got: {second.stdout!r}"
    assert list(ack_dir.iterdir()) == []
