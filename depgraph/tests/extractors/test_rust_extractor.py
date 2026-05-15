import json
import subprocess
import sys
from pathlib import Path

EXTRACTOR = (
    Path(__file__).resolve().parents[3]
    / "depgraph" / "extractors" / "generic" / "rust" / "extract.py"
)


def _run(repo, data, detectors=""):
    return subprocess.run(
        [sys.executable, str(EXTRACTOR),
         "--repo-key", "r", "--repo-path", str(repo),
         "--data-dir", str(data), "--detectors", detectors],
        capture_output=True, text=True,
    )


def _read(data: Path, sub: str) -> list[dict]:
    d = data / "nodes" / sub
    return [json.loads(p.read_text()) for p in d.iterdir()] if d.exists() else []


def test_rust_emits_function(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.rs").write_text("fn hi() {}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(f["name"] == "hi" for f in _read(tmp_data_dir, "functions"))


def test_rust_emits_struct_as_class(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.rs").write_text("struct User { name: String }\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(c["name"] == "User" for c in _read(tmp_data_dir, "classes"))


def test_rust_emits_use_as_import(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.rs").write_text("use std::collections::HashMap;\nfn hi(){}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    imports = _read(tmp_data_dir, "imports")
    assert any("HashMap" in (e.get("target") or "") for e in imports)
