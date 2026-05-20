"""Convention gate: extractor unit tests live under depgraph/tests/extractors/.

The repo splits its Python test trees by purpose:

* ``tests/depgraph/`` is the CLI-test root (sibling of ``test_cli_*.py`` with
  a conftest providing a ``data_dir`` fixture for CLI command tests).
* ``depgraph/tests/extractors/`` is where extractor unit tests live — the
  ones that drive ``extract_repo`` (or a sibling extractor entry point)
  directly and assert on the primitives/edges it emits.

Issue #80 was filed after an extractor-shape test landed under
``tests/depgraph/`` and had to be relocated by hand. Without a structural
gate, that drift recurs silently because pytest does not care where files
live. This test pins the convention by failing if any file matching an
extractor-shape filename pattern lives outside ``depgraph/tests/extractors/``.
"""
from __future__ import annotations

from pathlib import Path

# Filename patterns associated with extractor unit tests. Anything matching
# these globs is expected to live under depgraph/tests/extractors/.
EXTRACTOR_TEST_PATTERNS = (
    "test_extract*.py",
    "test_python_*.py",
    "test_typescript_*.py",
)

# Repo subtrees that should be ignored entirely (vendored / generated /
# harness-managed). `.claude/` holds isolated agent worktrees that mirror
# the repo tree — without exclusion the gate would re-flag any
# pre-existing offender inside each worktree on top of the real offender
# in the main worktree.
EXCLUDED_DIR_NAMES = {".venv", "node_modules", ".git", ".claude"}

# The single allowed home for extractor unit tests.
ALLOWED_DIR = Path("depgraph") / "tests" / "extractors"


def _repo_root() -> Path:
    # tests/test_extractor_test_location.py -> repo root
    return Path(__file__).resolve().parent.parent


def _is_excluded(path: Path, repo_root: Path) -> bool:
    rel_parts = path.relative_to(repo_root).parts
    return any(part in EXCLUDED_DIR_NAMES for part in rel_parts)


def test_extractor_tests_live_under_depgraph_tests_extractors() -> None:
    repo_root = _repo_root()
    allowed = (repo_root / ALLOWED_DIR).resolve()

    self_path = Path(__file__).resolve()

    offenders: list[Path] = []
    for pattern in EXTRACTOR_TEST_PATTERNS:
        for match in repo_root.rglob(pattern):
            if _is_excluded(match, repo_root):
                continue
            resolved = match.resolve()
            if resolved == self_path:
                # The gate file itself matches `test_extract*.py`; skip it.
                continue
            # Files directly in the allowed dir (not subdirs) are fine; any
            # extractor that needs subdirectories can still nest under it.
            try:
                resolved.relative_to(allowed)
            except ValueError:
                offenders.append(match.relative_to(repo_root))

    assert not offenders, (
        "Extractor-shape test files must live under "
        f"{ALLOWED_DIR.as_posix()}/ (see issue #80). Offending paths:\n  "
        + "\n  ".join(sorted(str(p) for p in offenders))
    )
