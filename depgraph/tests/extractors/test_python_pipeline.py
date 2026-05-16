"""Pipeline smoke test — guards against forgotten attach passes.

After extract_repo returns, every documented edge kind must have at least
one instance somewhere in the corpus. This is the regression gate against
"forgot to wire in a pass" (L5/L6 failure mode).
"""
from __future__ import annotations

from pathlib import Path

from depgraph.extractors.python.extract import extract_repo


def test_extract_repo_runs_all_edge_passes(tmp_path):
    """Sanity check: after extract_repo returns, every documented edge
    kind has at least one instance somewhere in the corpus. Catches the
    case where a future refactor forgets to wire in one of the attach
    passes."""
    repo = tmp_path / "fixture"
    repo.mkdir()
    (repo / "models.py").write_text(
        "class Base: pass\n\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
    )
    (repo / "service.py").write_text(
        "from .models import User\n"
        "import functools\n\n"
        "GLOBAL = 0\n\n"
        "def local_dec(fn): return fn\n\n"
        "@local_dec\n"
        "def read_global() -> int:\n"
        "    return GLOBAL\n\n"
        "def write_global():\n"
        "    global GLOBAL\n"
        "    GLOBAL = 1\n\n"
        "def make_user():\n"
        "    u = User()\n"
        "    return u\n"
    )
    (repo / "test_service.py").write_text(
        "from .service import read_global\n"
        "def test_read():\n"
        "    assert read_global() == 0\n"
    )

    prims = list(extract_repo(repo_key="fixture", repo_path=repo))
    edge_kinds = {e["kind"] for p in prims for e in p["edges_out"]}
    expected_kinds = {"defines", "extends", "imports", "calls",
                      "instantiates", "reads", "assigns", "decorates",
                      "tests"}
    missing = expected_kinds - edge_kinds
    assert not missing, f"extract_repo missed edge passes: {missing}"
