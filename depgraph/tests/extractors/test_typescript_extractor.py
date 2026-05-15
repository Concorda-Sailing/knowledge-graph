"""Drives the TS extractor via tsx subprocess. Asserts on emitted JSON."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

EXTRACTOR = (
    Path(__file__).resolve().parents[3]
    / "depgraph" / "extractors" / "generic" / "typescript" / "extract.ts"
)
# Use the locally-installed tsx so it resolves 'typescript' from the local
# node_modules rather than a cached global npx copy.
TSX = EXTRACTOR.parent / "node_modules" / ".bin" / "tsx"


pytestmark = pytest.mark.skipif(
    not TSX.exists() and not shutil.which("npx"),
    reason="tsx (local) or npx required for TS extractor tests",
)


def _tsx_cmd() -> list[str]:
    if TSX.exists():
        return [str(TSX)]
    return ["npx", "tsx"]


def _run(repo: Path, data: Path, detectors: str = ""):
    r = subprocess.run(
        [*_tsx_cmd(), str(EXTRACTOR),
         "--repo-key", "r", "--repo-path", str(repo),
         "--data-dir", str(data), "--detectors", detectors],
        capture_output=True, text=True,
        cwd=EXTRACTOR.parent,
    )
    return r


def _read_nodes(data: Path, kind_subdir: str) -> list[dict]:
    d = data / "nodes" / kind_subdir
    if not d.exists():
        return []
    return [json.loads(p.read_text()) for p in d.iterdir()]


def test_ts_emits_module_per_file(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("export const x = 1\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    mods = _read_nodes(tmp_data_dir, "modules")
    assert any(m["file"] == "a.ts" for m in mods)


def test_ts_emits_function_primitive(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("export function f(){ return 1 }\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    fns = _read_nodes(tmp_data_dir, "functions")
    assert any(f["name"] == "f" for f in fns)


def test_ts_emits_import_edge(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("import { x } from './b'\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    imports = _read_nodes(tmp_data_dir, "imports")
    assert any(e["target"] == "./b" for e in imports)
