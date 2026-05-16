"""Tests for kg.shared.git."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from kg.shared.git import git_commit_if_changed, default_actor


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    # Initial commit so HEAD exists
    (tmp_path / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path


def test_commit_if_changed_returns_true_when_staging_diff_exists(repo: Path) -> None:
    p = repo / "new.txt"
    p.write_text("new\n")
    rc = git_commit_if_changed(repo, [p], "test commit")
    assert rc is True


def test_commit_if_changed_returns_false_when_nothing_staged(repo: Path) -> None:
    # Empty paths list = nothing staged
    rc = git_commit_if_changed(repo, [], "test commit")
    assert rc is False


def test_commit_message_appears_in_log(repo: Path) -> None:
    p = repo / "x.txt"
    p.write_text("x\n")
    git_commit_if_changed(repo, [p], "my commit message")
    log = subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()
    assert log == "my commit message"


def test_default_actor_returns_nonempty_string() -> None:
    assert isinstance(default_actor(), str)
    assert default_actor()
