import json
import subprocess
import sys
from pathlib import Path
import pytest

EXTRACTOR = (
    Path(__file__).resolve().parents[3]
    / "depgraph" / "extractors" / "generic" / "go" / "extract.py"
)


def _run(repo: Path, data: Path, detectors=""):
    return subprocess.run(
        [sys.executable, str(EXTRACTOR),
         "--repo-key", "r", "--repo-path", str(repo),
         "--data-dir", str(data), "--detectors", detectors],
        capture_output=True, text=True,
    )


def _read(data: Path, sub: str) -> list[dict]:
    d = data / "nodes" / sub
    return [json.loads(p.read_text()) for p in d.iterdir()] if d.exists() else []


def test_go_emits_function(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.go").write_text("package x\nfunc Hi() {}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(f["name"] == "Hi" for f in _read(tmp_data_dir, "functions"))


def test_go_emits_struct_as_class(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.go").write_text("package x\ntype User struct { Name string }\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(c["name"] == "User" for c in _read(tmp_data_dir, "classes"))


def test_go_emits_import_edge(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.go").write_text('package x\nimport "fmt"\nfunc Hi() { fmt.Println("hi") }\n')
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    imports = _read(tmp_data_dir, "imports")
    assert any(e["target"] == "fmt" for e in imports)
