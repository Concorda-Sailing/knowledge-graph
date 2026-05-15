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


def test_react_component_relabeled(tmp_repo, tmp_data_dir):
    (tmp_repo / "C.tsx").write_text(
        "export function MyButton() { return <button>hi</button> }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert any(c["name"] == "MyButton" for c in comps)


def test_react_hook_relabeled(tmp_repo, tmp_data_dir):
    (tmp_repo / "h.ts").write_text(
        "import { useState } from 'react'\n"
        "export function useThing() { const [x, set] = useState(0); return x }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    hooks = _read_nodes(tmp_data_dir, "hooks")
    assert any(h["name"] == "useThing" for h in hooks)


def test_react_ignores_lowercase_function(tmp_repo, tmp_data_dir):
    (tmp_repo / "u.ts").write_text("export function helper() { return 1 }\n")
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    hooks = _read_nodes(tmp_data_dir, "hooks")
    assert not any(c["name"] == "helper" for c in comps + hooks)


def test_vitest_describe_emits_test_node(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.test.ts").write_text(
        "import { describe, it, expect } from 'vitest'\n"
        "describe('thing', () => { it('works', () => { expect(1).toBe(1) }) })\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    assert any(t.get("name") == "works" for t in tests)


def test_vitest_only_fires_in_test_files(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text(
        "describe('x', () => { it('y', () => {}) })\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    assert tests == []


def test_route_calls_detector_emits_route_call(tmp_repo, tmp_data_dir):
    (tmp_repo / "client.ts").write_text(
        "async function load() { return fetch('/api/items') }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="route-calls")
    assert r.returncode == 0, r.stderr
    calls = _read_nodes(tmp_data_dir, "route_calls")
    assert any(c.get("url") == "/api/items" for c in calls)


def test_react_component_forwardref(tmp_repo, tmp_data_dir):
    (tmp_repo / "Button.tsx").write_text(
        'import * as React from "react"\n'
        'export const Button = React.forwardRef<HTMLButtonElement, {x:number}>('
        '({ x }, ref) => <button ref={ref}>{x}</button>'
        ')\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert any(c["name"] == "Button" for c in comps)


def test_react_component_alias(tmp_repo, tmp_data_dir):
    (tmp_repo / "Popover.tsx").write_text(
        'import * as PopoverPrimitive from "@radix-ui/react-popover"\n'
        'export const Popover = PopoverPrimitive.Root\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert any(c["name"] == "Popover" for c in comps)


def test_react_ignores_lowercase_variable(tmp_repo, tmp_data_dir):
    (tmp_repo / "x.ts").write_text(
        'export const helper = someLib.thing\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert not any(c["name"] == "helper" for c in comps)


def test_vitest_deduplicates_same_test_name(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.test.ts").write_text(
        'import { describe, it } from "vitest"\n'
        'describe("g", () => {\n'
        '  it("works", () => {})\n'
        '  it("works", () => {})\n'
        '})\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    works = [t for t in tests if t.get("name") == "works"]
    assert len(works) == 1, f"expected dedup; got {[t.get('name') for t in tests]}"


def test_vitest_handles_property_access_verbs(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.test.ts").write_text(
        'import { describe, test } from "vitest"\n'
        'describe("g", () => {\n'
        '  test.skip("skipped", () => {})\n'
        '  test.only("only", () => {})\n'
        '})\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    names = sorted(t.get("name") for t in tests)
    assert names == ["only", "skipped"]


def test_service_relabels_function_in_lib(tmp_repo, tmp_data_dir):
    (tmp_repo / "lib").mkdir()
    (tmp_repo / "lib" / "api.ts").write_text(
        "export function fetchUsers() { return [] }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    assert any(s["name"] == "fetchUsers" for s in svcs)


def test_service_relabels_function_in_pages(tmp_repo, tmp_data_dir):
    (tmp_repo / "pages").mkdir()
    (tmp_repo / "pages" / "dashboard.ts").write_text(
        "export function navigateToDashboard() { return null }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    assert any(s["name"] == "navigateToDashboard" for s in svcs)


def test_service_skips_underscore_prefix(tmp_repo, tmp_data_dir):
    (tmp_repo / "lib").mkdir()
    (tmp_repo / "lib" / "helpers.ts").write_text(
        "function _internal() {}\nexport function pub() {}\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    names = [s["name"] for s in svcs]
    assert "pub" in names
    assert "_internal" not in names


def test_service_ignores_non_service_path(tmp_repo, tmp_data_dir):
    (tmp_repo / "components").mkdir()
    (tmp_repo / "components" / "x.ts").write_text("export function foo() {}\n")
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    assert not any(s["name"] == "foo" for s in svcs)
