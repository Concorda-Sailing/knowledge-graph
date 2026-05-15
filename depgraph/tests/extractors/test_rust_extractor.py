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


def test_rust_chained_call_target_is_single_line(tmp_repo, tmp_data_dir):
    """Multi-line method chains used to inflate the callee target with raw
    source bytes (including newlines), which then overflowed the on-disk
    filename limit when ids were slugified."""
    (tmp_repo / "a.rs").write_text(
        "fn parse(headers: &Headers) -> Option<&str> {\n"
        "    headers\n"
        "        .get(\"x-api-key\")\n"
        "        .and_then(|v| v.to_str().ok())\n"
        "        .or_else(|| headers.get(\"authorization\").and_then(|v| v.to_str().ok()))\n"
        "}\n"
    )
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    calls = _read(tmp_data_dir, "calls")
    assert calls, "expected at least one call_edge for the chain"
    for c in calls:
        target = c.get("target") or ""
        assert "\n" not in target, f"call target leaked newline: {target!r}"
        assert "\n" not in c["id"], f"call id leaked newline: {c['id']!r}"


def test_rust_filename_safe_for_long_ids(tmp_repo, tmp_data_dir):
    """A pathologically long use-declaration must not overflow the filename
    length limit (255 bytes on ext4/btrfs)."""
    long_target = "::".join(f"segment_{i}" for i in range(60))
    (tmp_repo / "a.rs").write_text(f"use {long_target};\nfn hi(){{}}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    import_dir = tmp_data_dir / "nodes" / "imports"
    files = list(import_dir.iterdir())
    assert files, "expected at least one import file"
    assert all(len(f.name) <= 255 for f in files), [f.name for f in files]
