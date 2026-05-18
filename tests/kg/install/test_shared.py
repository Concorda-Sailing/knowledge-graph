"""Direct tests for kg.cli.install._shared helpers."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from kg.cli.install._shared import backup_file, check_prereqs, require


# ---------------------------------------------------------------------------
# backup_file
# ---------------------------------------------------------------------------

def test_backup_file_creates_single_suffix_bak(tmp_path: Path) -> None:
    """backup_file copies an existing file to <p>.bak (single suffix,
    no timestamp). Older versions used `.bak.<mtime>` which accumulated;
    the new contract is a single `.bak` overwritten on each call."""
    original = tmp_path / "settings.json"
    original.write_text('{"key": "value"}')

    bak = backup_file(original)

    assert bak is not None
    expected_bak = original.with_suffix(original.suffix + ".bak")
    assert bak == expected_bak
    assert bak.exists()
    assert bak.read_text() == '{"key": "value"}'


def test_backup_file_no_op_when_path_missing(tmp_path: Path) -> None:
    """backup_file returns None for a non-existent path without raising."""
    nonexistent = tmp_path / "does_not_exist.json"

    result = backup_file(nonexistent)

    assert result is None


def test_backup_file_overwrites_existing_bak(tmp_path: Path) -> None:
    """A second call to backup_file overwrites the previous `.bak`
    with whatever the original currently holds. Only one `.bak` exists
    at any time — older behaviour accumulated `.bak.<mtime>` files
    across runs and is intentionally abandoned."""
    original = tmp_path / "settings.json"
    original.write_text("first content")
    bak = backup_file(original)
    assert bak is not None and bak.read_text() == "first content"

    original.write_text("second content")
    bak2 = backup_file(original)

    assert bak2 == bak  # same .bak path
    assert bak2.read_text() == "second content"  # overwritten with new pre-modify state
    # No accumulated .bak.<digits> siblings
    assert list(tmp_path.glob("settings.json.bak.*")) == []


def test_backup_file_prunes_legacy_timestamped_backups(tmp_path: Path) -> None:
    """Leftover `.bak.<digits>` files from older install runs are
    deleted on the next call — the cleanup is self-healing so
    re-bootstrapping a project sweeps the old cruft without manual
    intervention."""
    original = tmp_path / "settings.json"
    original.write_text("current content")
    # Pre-seed legacy timestamped backups (simulating prior installs).
    (tmp_path / "settings.json.bak.1700000000").write_text("old1")
    (tmp_path / "settings.json.bak.1700000001").write_text("old2")
    (tmp_path / "settings.json.bak.1700000002").write_text("old3")

    backup_file(original)

    # All legacy timestamped backups are gone; only the single .bak remains.
    assert (tmp_path / "settings.json.bak").exists()
    assert list(tmp_path.glob("settings.json.bak.*")) == []


# ---------------------------------------------------------------------------
# check_prereqs
# ---------------------------------------------------------------------------

def test_check_prereqs_passes_with_git_and_python_3_10_plus(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """check_prereqs() should succeed when git is present and Python >= 3.10."""
    # If git is not installed this test will fail, which is the correct behavior.
    check_prereqs()  # must not raise
    out = capsys.readouterr().out
    # Should confirm python + git were checked.
    assert "git" in out


# ---------------------------------------------------------------------------
# color helpers — _USE_COLOR flag captured at import time
# ---------------------------------------------------------------------------

def test_color_helpers_produce_plain_text_when_use_color_false() -> None:
    """When _USE_COLOR is False, the color wrappers return the text unchanged.

    _USE_COLOR is captured at module import time based on sys.stdout.isatty()
    and os.environ['NO_COLOR']. In the test environment stdout is not a TTY,
    so _USE_COLOR is False and wrappers return plain text. We verify the
    actual behavior rather than mutating the captured flag.
    """
    from kg.cli.install._shared import _USE_COLOR, color_dim, color_green, color_red, color_yellow

    if _USE_COLOR:
        # Running in a real TTY (unlikely in CI). Verify codes are present.
        assert "\033[" in color_red("x")
        assert "\033[" in color_green("x")
    else:
        # Normal test environment: no color codes injected.
        assert color_red("hello") == "hello"
        assert color_green("hello") == "hello"
        assert color_yellow("hello") == "hello"
        assert color_dim("hello") == "hello"


# ---------------------------------------------------------------------------
# require
# ---------------------------------------------------------------------------

def test_require_raises_systemexit_for_missing_cmd() -> None:
    """require("nonexistent-binary-xyz") must raise SystemExit."""
    with pytest.raises(SystemExit):
        require("nonexistent-binary-xyz-qwerty")


def test_require_passes_for_existing_cmd() -> None:
    """require("git") must not raise when git is on PATH."""
    require("git")  # must not raise
