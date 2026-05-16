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

def test_backup_file_creates_bak_with_mtime(tmp_path: Path) -> None:
    """backup_file copies an existing file to <p>.bak.<mtime> and returns the path."""
    original = tmp_path / "settings.json"
    original.write_text('{"key": "value"}')

    bak = backup_file(original)

    assert bak is not None
    mtime = int(original.stat().st_mtime)
    expected_bak = original.with_suffix(original.suffix + f".bak.{mtime}")
    assert bak == expected_bak
    assert bak.exists()
    assert bak.read_text() == '{"key": "value"}'


def test_backup_file_no_op_when_path_missing(tmp_path: Path) -> None:
    """backup_file returns None for a non-existent path without raising."""
    nonexistent = tmp_path / "does_not_exist.json"

    result = backup_file(nonexistent)

    assert result is None


def test_backup_file_does_not_clobber_existing_bak(tmp_path: Path) -> None:
    """If <p>.bak.<mtime> already exists, backup_file does not overwrite it."""
    original = tmp_path / "settings.json"
    original.write_text("first content")

    # Compute what the bak path will be and pre-create it with different content.
    mtime = int(original.stat().st_mtime)
    pre_existing_bak = original.with_suffix(original.suffix + f".bak.{mtime}")
    pre_existing_bak.write_text("pre-existing backup content")

    bak = backup_file(original)

    # Should still return the bak path.
    assert bak == pre_existing_bak
    # The pre-existing backup should not have been overwritten.
    assert pre_existing_bak.read_text() == "pre-existing backup content"


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
