"""Subprocess test for the TS route-call extractor.

Runs `npx tsx <extractor> --scan <fixture-dir> --repo-key fake-web` and
asserts the emitted JSON-Lines output contains one route_call node per
fetch() site, with method and url_pattern extracted correctly."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTOR = REPO_ROOT / "extractors" / "generic" / "typescript" / "route-calls.ts"
EXTRACTOR_DIR = REPO_ROOT / "extractors" / "generic" / "typescript"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "typescript_extractor"


def _have_tsx() -> bool:
    return shutil.which("npx") is not None and (EXTRACTOR_DIR / "node_modules" / "tsx").exists()


@pytest.mark.skipif(not _have_tsx(), reason="tsx not installed (run npm install in extractors/generic/typescript)")
def test_extractor_emits_three_route_calls():
    result = subprocess.run(
        ["npx", "tsx", str(EXTRACTOR), "--scan", str(FIXTURE_DIR), "--repo-key", "fake-web"],
        cwd=str(EXTRACTOR_DIR),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"extractor failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    nodes = [json.loads(l) for l in lines]

    # Three resolvable fetch sites in sample.ts (the bare-variable one is skipped).
    assert len(nodes) == 3, f"expected 3 route_call nodes, got {len(nodes)}: {nodes}"
    by_url = {n["signature"]["url_pattern"]: n for n in nodes}

    # Health endpoint: template literal with only the base var → / path remains
    assert "/health" in by_url, f"missing /health; saw {sorted(by_url)}"
    assert by_url["/health"]["signature"]["method"] == "GET"
    assert by_url["/health"]["kind"] == "route_call"
    assert by_url["/health"]["source"]["repo"] == "fake-web"

    # Variable in path → tokenized to <var>
    assert "/api/events/<var>/import" in by_url
    assert by_url["/api/events/<var>/import"]["signature"]["method"] == "POST"

    # Plain string literal first arg
    assert "/api/organizations" in by_url
    assert by_url["/api/organizations"]["signature"]["method"] == "GET"
