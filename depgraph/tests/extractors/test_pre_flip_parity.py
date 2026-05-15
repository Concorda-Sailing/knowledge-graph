"""Gate test: framework canonical output must match committed pre-flip
samples byte-for-byte on id, structural_hash, signature, dossier path,
and source block.

Each sample fixture is a real pre-flip Concorda node. The test runs the
framework extractor against the corresponding upstream source file in
~/concorda-{api,web,test}/, extracts the matching canonical node, and
asserts equality on the load-bearing fields.

depends_on is checked separately (compared as sets, since order is
non-deterministic) — see test_pre_flip_depends_on.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pre_flip_nodes"
KG_ROOT = Path(__file__).resolve().parents[3]


def _run_extractor(repo_key: str, repo_path: Path, detectors: list[str],
                   data_dir: Path, only: Path | None = None) -> None:
    lang_dir = {
        "concorda-api": "python",
        "concorda-web": "typescript",
        "concorda-test": "typescript",
    }[repo_key]
    if lang_dir == "python":
        cmd = [
            sys.executable, "-m", "extractors.generic.python.extract",
            "--repo-key", repo_key, "--repo-path", str(repo_path),
            "--data-dir", str(data_dir),
            "--detectors", ",".join(detectors),
        ]
    else:
        cmd = [
            "npx", "tsx",
            str(KG_ROOT / "depgraph" / "extractors" / "generic" / "typescript" / "extract.ts"),
            "--repo-key", repo_key, "--repo-path", str(repo_path),
            "--data-dir", str(data_dir),
            "--detectors", ",".join(detectors),
        ]
    if only:
        cmd += ["--only", str(only)]
    subprocess.run(cmd, check=True, cwd=KG_ROOT / "depgraph")


def _load_node(data_dir: Path, kind_dir: str, slug: str) -> dict:
    return json.loads((data_dir / "nodes" / kind_dir / f"{slug}.json").read_text())


@pytest.fixture(scope="module")
def regen_concorda(tmp_path_factory):
    """Regen with framework extractors into a scratch dir, once per module."""
    out = tmp_path_factory.mktemp("scratch") / "depgraph"
    out.mkdir(parents=True)
    _run_extractor("concorda-api", Path.home() / "concorda-api",
                   ["fastapi", "sqlalchemy", "pydantic", "service"], out)
    _run_extractor("concorda-web", Path.home() / "concorda-web",
                   ["react", "route-calls", "service"], out)
    _run_extractor("concorda-test", Path.home() / "concorda-test",
                   ["vitest"], out)
    return out


def _assert_equivalent(expected: dict, actual: dict, exclude=("depends_on",)) -> None:
    """Compare two nodes for byte-level equality on load-bearing fields."""
    for field in ("schema_version", "id", "kind", "title", "feature",
                  "source", "signature", "structural_hash",
                  "dossier", "extractor"):
        if field in exclude:
            continue
        if field not in expected:
            continue  # outlier kinds (route_call) lack some fields
        assert actual.get(field) == expected[field], (
            f"field {field!r} mismatch:\n"
            f"  expected: {expected.get(field)!r}\n"
            f"  actual:   {actual.get(field)!r}"
        )


# One test per kind — easier to triage individual failures.

def test_endpoint_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "endpoint__sample.json").read_text())
    # The slug is derivable from id via slugify_id_py
    from extractors.generic.python.canonical import slugify_id_py
    slug = slugify_id_py(expected["id"])
    actual = _load_node(regen_concorda, "endpoints", slug)
    _assert_equivalent(expected, actual)


def test_model_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "model__sample.json").read_text())
    from extractors.generic.python.canonical import slugify_id_py
    actual = _load_node(regen_concorda, "models", slugify_id_py(expected["id"]))
    _assert_equivalent(expected, actual)


def test_schema_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "schema__sample.json").read_text())
    from extractors.generic.python.canonical import slugify_id_py
    actual = _load_node(regen_concorda, "schemas", slugify_id_py(expected["id"]))
    _assert_equivalent(expected, actual)


def test_service_py_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "service_py__sample.json").read_text())
    from extractors.generic.python.canonical import slugify_id_py
    actual = _load_node(regen_concorda, "services", slugify_id_py(expected["id"]))
    _assert_equivalent(expected, actual)


def test_component_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "component__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "components", slugify_id_ts(expected["id"]))
    _assert_equivalent(expected, actual)


def test_hook_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "hook__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "hooks", slugify_id_ts(expected["id"]))
    _assert_equivalent(expected, actual)


def test_test_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "test__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "tests", slugify_id_ts(expected["id"]))
    _assert_equivalent(expected, actual)


def test_route_call_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "route_call__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "route_calls", slugify_id_ts(expected["id"]))
    # route_call lacks several fields — exclude them
    _assert_equivalent(expected, actual)


def test_depends_on_taxonomy(regen_concorda):
    """depends_on entries can be reordered; compare as sets of tuples."""
    for kind_file in ("endpoint__sample.json", "component__sample.json",
                      "hook__sample.json"):
        expected = json.loads((FIXTURE_DIR / kind_file).read_text())
        if not expected.get("depends_on"):
            continue
        kind_dir = {"endpoint": "endpoints", "component": "components",
                    "hook": "hooks"}[expected["kind"]]
        from extractors.generic.python.canonical import slugify_id_py
        from extractors.generic.typescript.canonical import slugify_id_ts
        slug = slugify_id_py(expected["id"]) if expected["kind"] == "endpoint" \
            else slugify_id_ts(expected["id"])
        actual = _load_node(regen_concorda, kind_dir, slug)
        expected_set = {(e["target"], e["via"]) for e in expected["depends_on"]}
        actual_set = {(e["target"], e["via"]) for e in actual.get("depends_on", [])}
        # Every pre-flip edge must be reproduced. Extra edges allowed
        # (architecture may detect more in future), but never fewer.
        missing = expected_set - actual_set
        assert not missing, (
            f"{kind_file}: missing depends_on edges: {missing}"
        )
