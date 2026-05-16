"""TS primitive extractor end-to-end tests.

Each test runs the extractor against a small fixture project under
fixtures/primitives_ts/<scenario>/ and asserts on the primitive set
emitted.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "primitives_ts"
EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def run_extractor(fixture_name: str) -> list[dict]:
    """Run the extractor against the named fixture; return primitives list."""
    fixture_root = FIXTURE_DIR / fixture_name
    cmd = ["npx", "tsx", str(EXTRACTOR),
           "--repo-key", "fixture",
           "--repo-path", str(fixture_root),
           "--format", "ndjson"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=EXTRACTOR.parent, check=True)
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def test_module_primitive_for_each_source_file():
    prims = run_extractor("module_only")
    modules = [p for p in prims if p["primitive"] == "module"]
    assert len(modules) == 1
    m = modules[0]
    assert m["id"] == "fixture::src/hello.ts"
    assert m["source"]["language"] == "typescript"
    assert m["source"]["path"] == "src/hello.ts"
