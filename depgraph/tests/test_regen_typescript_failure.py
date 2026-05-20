"""Unit tests for `_extract_typescript`'s failure-surfacing contract.

After the #28 fix, the function returns (prims, error_msg) rather than
just `prims`, so the regen loop can summarize failures at end-of-run
instead of burying them as a single WARN line.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from depgraph.lib.cli.regen import _extract_typescript


def _completed(rc: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["npx"], returncode=rc, stdout=stdout, stderr=stderr,
    )


def test_returns_prims_and_none_on_success(tmp_path: Path) -> None:
    tool_root = tmp_path / "tools"
    (tool_root / "extractors" / "typescript").mkdir(parents=True)
    (tool_root / "extractors" / "typescript" / "extract.ts").write_text("// stub\n")

    stdout = '{"id": "x", "primitive": "module"}\n{"id": "y", "primitive": "module"}\n'
    with patch(
        "depgraph.lib.cli.regen.subprocess.run",
        return_value=_completed(0, stdout=stdout),
    ):
        prims, err = _extract_typescript(
            "web", tmp_path, tool_root=tool_root,
        )
    assert err is None
    assert [p["id"] for p in prims] == ["x", "y"]


def test_returns_empty_and_error_on_nonzero_exit(tmp_path: Path) -> None:
    """Non-zero exit (OOM, syntax error, etc.) yields ([], '...') so the
    regen loop tracks the failure and surfaces it at end-of-run."""
    tool_root = tmp_path / "tools"
    (tool_root / "extractors" / "typescript").mkdir(parents=True)
    (tool_root / "extractors" / "typescript" / "extract.ts").write_text("// stub\n")

    stderr = (
        "<--- Last few GCs --->\n"
        "FATAL ERROR: Ineffective mark-compacts near heap limit "
        "Allocation failed - JavaScript heap out of memory\n"
    )
    with patch(
        "depgraph.lib.cli.regen.subprocess.run",
        return_value=_completed(134, stderr=stderr),
    ):
        prims, err = _extract_typescript(
            "web", tmp_path, tool_root=tool_root,
        )
    assert prims == []
    assert err is not None
    assert "exit=134" in err


def test_missing_extractor_returns_error(tmp_path: Path) -> None:
    """If extract.ts is missing entirely, return an error rather than
    silently producing zero primitives."""
    tool_root = tmp_path / "tools"
    tool_root.mkdir()
    # No extractors/typescript/extract.ts planted.

    prims, err = _extract_typescript("web", tmp_path, tool_root=tool_root)
    assert prims == []
    assert err is not None
    assert "TS extractor not found" in err
