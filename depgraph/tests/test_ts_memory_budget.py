"""Peak-RSS smoke test for the TypeScript extractor — guards against
re-regression of the memory blow-up fixed in d759e1e (#44).

That commit replaced materializing AST walks (`getDescendants()`,
`getDescendantsOfKind(CallExpression)`) with streaming `forEachDescendant`
traversals. The existing unit tests stayed green either way, so a future
refactor could silently undo the win and the next signal would be a
production OOM-kill on a large corpus. See #81 for the motivation.

This test runs the extractor as a subprocess wrapped in `/usr/bin/time -v`,
parses the `Maximum resident set size` line from stderr, and asserts the
peak RSS stayed under a generous budget. It runs only where GNU time is
available (Linux CI) and is marked `memory_budget` so a quick local
`pytest -m 'not memory_budget'` can skip it.

Note on fixture size: the only TypeScript fixture currently in-tree large
enough to exercise the extractor across many files is `kitchen_sink/web`,
which is well under 50 source files. The 512 MB budget is correspondingly
generous — it's tight enough that re-materializing the AST descendant
arrays on the kitchen_sink fixture would still trip it (the pre-d759e1e
extractor on this fixture allocated ~5x the post-fix steady-state RSS),
but it WILL need to be re-tightened once a larger TS fixture lands.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

# Repo layout: this file lives at depgraph/tests/test_ts_memory_budget.py.
TESTS_DIR = Path(__file__).resolve().parent
DEPGRAPH_ROOT = TESTS_DIR.parent
TS_EXTRACTOR = DEPGRAPH_ROOT / "extractors" / "typescript" / "extract.ts"
FIXTURE = TESTS_DIR / "fixtures" / "wild" / "kitchen_sink" / "web"

# 512 MB. Steady-state RSS for the kitchen_sink/web fixture sits around
# 200 MB on a stock Node 20 + ts-morph; the pre-fix materializing walks
# would push past this on the same fixture. Re-calibrate downward once a
# larger TS fixture is available (issue #81 acceptance criterion).
MAX_RSS_KB = 512_000

_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\):\s*(\d+)")


def _parse_max_rss_kb(stderr: str) -> int:
    """Pull the `Maximum resident set size (kbytes): N` line out of GNU
    time -v stderr. Raises AssertionError with the full stderr captured
    if the line isn't present — that means the wrapper didn't run as
    expected and the test would otherwise pass silently."""
    match = _RSS_RE.search(stderr)
    assert match is not None, (
        "Could not find 'Maximum resident set size' line in /usr/bin/time -v "
        f"stderr — the wrapper likely didn't run. Full stderr:\n{stderr}"
    )
    return int(match.group(1))


@pytest.mark.memory_budget
def test_ts_extractor_peak_rss_under_budget():
    """Extractor on kitchen_sink/web must stay under MAX_RSS_KB peak RSS.

    Skips on platforms that don't ship GNU time with `-v` (macOS by
    default, most Windows envs); the gate runs on Linux CI where the
    pre-d759e1e regression originally surfaced.
    """
    if shutil.which("/usr/bin/time") is None:
        pytest.skip("/usr/bin/time (GNU time -v) not available on this platform")
    if not TS_EXTRACTOR.exists():
        pytest.skip(f"TS extractor missing at {TS_EXTRACTOR}")
    if not FIXTURE.exists():
        pytest.skip(f"kitchen_sink/web fixture missing at {FIXTURE}")

    cmd = [
        "/usr/bin/time", "-v",
        "npx", "tsx", str(TS_EXTRACTOR),
        "--repo-key", "kitchen-sink-web",
        "--repo-path", str(FIXTURE),
        "--format", "ndjson",
    ]
    # cwd at the extractor dir so its local node_modules (ts-morph etc.)
    # resolve. Mirrors test_typescript_primitives.run_extractor().
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(TS_EXTRACTOR.parent),
        timeout=180,
    )
    # /usr/bin/time -v writes the resource-usage block AFTER the wrapped
    # command finishes; on a non-zero child exit it still prints the
    # block then propagates the exit code. We fail loudly so a regression
    # in extractor exit behavior doesn't masquerade as "memory fine".
    assert proc.returncode == 0, (
        f"TS extractor exited {proc.returncode}; cannot trust memory reading.\n"
        f"--- stderr (tail) ---\n{proc.stderr[-2000:]}"
    )
    peak_rss_kb = _parse_max_rss_kb(proc.stderr)
    assert peak_rss_kb < MAX_RSS_KB, (
        f"TS extractor peak RSS {peak_rss_kb} kB exceeds budget {MAX_RSS_KB} kB. "
        f"Did a new edge pass reintroduce a materializing AST walk "
        f"(`getDescendants()` / `getDescendantsOfKind(...)`)? See #44 / #81."
    )
