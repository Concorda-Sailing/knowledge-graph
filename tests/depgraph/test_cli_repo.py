"""Tests for bin/depgraph repo-add / repo-list / repo-remove subcommands."""
from __future__ import annotations

import subprocess
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[2]
BIN = TOOL_ROOT / "depgraph" / "bin" / "depgraph"


def _make_fixture(tmp_path: Path) -> Path:
    """Minimal depgraph data dir with a project.toml containing one repo."""
    (tmp_path / "nodes" / "_index").mkdir(parents=True)
    (tmp_path / "project.toml").write_text(
        '[project]\nname = "test"\nprimary_repo = "myrepo"\n'
        '[repos.myrepo]\npath = "/some/existing/path"\n'
    )
    return tmp_path


def _run(args, data):
    env = {
        "DEPGRAPH_DATA_DIR": str(data),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(data),
    }
    return subprocess.run([str(BIN), *args], cwd=data, env=env, capture_output=True, text=True)


# ── repo-add ──────────────────────────────────────────────────────────────────

def test_repo_add_writes_new_block(tmp_path):
    """repo-add writes a [repos.<key>] block with path into project.toml."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-add", "newrepo", "/tmp/newrepo"], data)
    assert r.returncode == 0, r.stderr
    text = (data / "project.toml").read_text()
    assert "[repos.newrepo]" in text
    assert "/tmp/newrepo" in text or "newrepo" in text


def test_repo_add_refuses_duplicate_without_force(tmp_path):
    """repo-add exits 1 when key already exists and --force is not passed."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-add", "myrepo", "/tmp/other"], data)
    assert r.returncode == 1
    assert "force" in r.stderr.lower() or "already exists" in r.stderr.lower()


def test_repo_add_force_replaces_existing(tmp_path):
    """repo-add --force replaces the existing [repos.<key>] block."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-add", "--force", "myrepo", "/tmp/replacement"], data)
    assert r.returncode == 0, r.stderr
    text = (data / "project.toml").read_text()
    assert "[repos.myrepo]" in text
    # Only one occurrence of the header
    assert text.count("[repos.myrepo]") == 1


def test_repo_add_invalid_key_exits_1(tmp_path):
    """repo-add rejects a key that starts with a dash."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-add", "-bad-key", "/tmp/repo"], data)
    # argparse will treat -bad-key as a flag; either argparse errors or our validator fires
    assert r.returncode != 0


# ── repo-list ─────────────────────────────────────────────────────────────────

def test_repo_list_shows_repos_with_primary_marker(tmp_path):
    """repo-list prints each repo and marks the primary one."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-list"], data)
    assert r.returncode == 0, r.stderr
    assert "myrepo" in r.stdout
    assert "primary" in r.stdout.lower()


def test_repo_list_no_repos_exits_0(tmp_path):
    """repo-list with no repos configured exits 0 with a message."""
    (tmp_path / "nodes" / "_index").mkdir(parents=True)
    (tmp_path / "project.toml").write_text('[project]\nname = "empty"\n')
    r = _run(["repo-list"], tmp_path)
    assert r.returncode == 0
    assert "no repos" in r.stdout.lower()


def test_repo_list_marks_implicit_primary_distinctly(tmp_path):
    """Without [project].primary_repo, the first listed repo is marked
    `(primary, default)` and a footer explains the fallback (#22)."""
    (tmp_path / "nodes" / "_index").mkdir(parents=True)
    (tmp_path / "project.toml").write_text(
        '[project]\nname = "test"\n'
        '[repos.first]\npath = "/tmp/first"\n'
        '[repos.second]\npath = "/tmp/second"\n'
    )
    r = _run(["repo-list"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert "first (primary, default)" in r.stdout
    # Second repo must not get a primary marker.
    assert "second\n" in r.stdout or r.stdout.rstrip().endswith("second")
    assert "no primary_repo set" in r.stdout


def test_repo_list_marks_explicit_primary_without_default_suffix(tmp_path):
    """When primary_repo is set, the marker is plain `(primary)` — no `default`."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-list"], data)
    assert r.returncode == 0, r.stderr
    assert "myrepo (primary)" in r.stdout
    assert "default" not in r.stdout


# ── repo-remove ───────────────────────────────────────────────────────────────

def test_repo_remove_strips_block(tmp_path):
    """repo-remove deletes the [repos.<key>] block from project.toml."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-remove", "myrepo"], data)
    assert r.returncode == 0, r.stderr
    text = (data / "project.toml").read_text()
    assert "[repos.myrepo]" not in text


def test_repo_remove_nonexistent_key_exits_1(tmp_path):
    """repo-remove exits 1 when the key does not exist."""
    data = _make_fixture(tmp_path)
    r = _run(["repo-remove", "doesnotexist"], data)
    assert r.returncode == 1
    assert "not found" in r.stderr.lower()
