"""Drives the TS extractor via tsx subprocess. Asserts on emitted JSON.

After Task 6 (framework-canonicalization), the TS extractor writes only
canonical nodes (component / hook / service / test / route_call) — the
primitive kinds (module, class, function, import_edge, call_edge) are
dropped post-canonicalize per the contract in
docs/superpowers/plans/2026-05-15-framework-canonicalization.md.
"""
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


def _symbols(nodes: list[dict]) -> list[str]:
    """Return source.symbol for each canonical node (or `title` as fallback
    for outlier kinds without a symbol field, e.g. route_call)."""
    return [n.get("source", {}).get("symbol") or n.get("title") for n in nodes]


# --------------------------------------------------------------------------- #
# Smoke: extractor runs without errors on a trivial repo. Canonical-only
# output means a repo with no canonical-kind candidates emits zero nodes.
# --------------------------------------------------------------------------- #

def test_ts_runs_with_no_detectors(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("export const x = 1\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert "wrote" in r.stdout


def test_ts_runs_on_imports_without_error(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("import { x } from './b'\n")
    (tmp_repo / "b.ts").write_text("export const x = 1\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr


# --------------------------------------------------------------------------- #
# React detector — components & hooks (canonical kinds).
# --------------------------------------------------------------------------- #

def test_react_component_relabeled(tmp_repo, tmp_data_dir):
    (tmp_repo / "C.tsx").write_text(
        "export function MyButton() { return <button>hi</button> }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert "MyButton" in _symbols(comps)


def test_react_hook_relabeled(tmp_repo, tmp_data_dir):
    (tmp_repo / "h.ts").write_text(
        "import { useState } from 'react'\n"
        "export function useThing() { const [x, set] = useState(0); return x }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    hooks = _read_nodes(tmp_data_dir, "hooks")
    assert "useThing" in _symbols(hooks)


def test_react_ignores_lowercase_function(tmp_repo, tmp_data_dir):
    # Non-React names (lowercase, non-`use<Capital>`) are not the react
    # detector's responsibility. They should not appear in any kind dir.
    # Service-kind nodes for these names come from the dedicated `service`
    # detector (path-filtered), not from `react`.
    (tmp_repo / "u.ts").write_text("export function helper() { return 1 }\n")
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    hooks = _read_nodes(tmp_data_dir, "hooks")
    svcs = _read_nodes(tmp_data_dir, "services")
    assert "helper" not in _symbols(comps + hooks + svcs)


def test_react_does_not_emit_object_literal_api_clients(tmp_repo, tmp_data_dir):
    # `export const profileApi = { get: () => ... }` used to emit
    # `profileApi.get` as a service from `react`. That belonged in a
    # path-aware detector; `react` is components and hooks only.
    (tmp_repo / "client.ts").write_text(
        "export const profileApi = { get: () => 1, post: () => 2 }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    syms = _symbols(svcs)
    assert "profileApi.get" not in syms
    assert "profileApi.post" not in syms


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
    assert "Button" in _symbols(comps)


def test_react_component_alias(tmp_repo, tmp_data_dir):
    (tmp_repo / "Popover.tsx").write_text(
        'import * as PopoverPrimitive from "@radix-ui/react-popover"\n'
        'export const Popover = PopoverPrimitive.Root\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert "Popover" in _symbols(comps)


def test_react_ignores_lowercase_variable(tmp_repo, tmp_data_dir):
    (tmp_repo / "x.ts").write_text(
        'export const helper = someLib.thing\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert "helper" not in _symbols(comps)


# --------------------------------------------------------------------------- #
# Vitest / Playwright detector — emits test nodes (only in .spec.ts files).
# --------------------------------------------------------------------------- #

def test_vitest_emits_test_node(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.spec.ts").write_text(
        "import { test } from '@playwright/test'\n"
        "test('works', () => { })\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    assert any(t.get("title") == "works" for t in tests)


def test_vitest_only_fires_in_spec_files(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text(
        "test('y', () => {})\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    assert tests == []


def test_vitest_handles_property_access_verbs(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.spec.ts").write_text(
        'import { test } from "@playwright/test"\n'
        'test.skip("skipped", () => {})\n'
        'test.only("only", () => {})\n'
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    titles = sorted(t.get("title") for t in tests)
    assert titles == ["only", "skipped"]


# --------------------------------------------------------------------------- #
# Route-calls detector — emits route_call nodes for fetch()/api.<verb> calls.
# --------------------------------------------------------------------------- #

def test_route_calls_detector_emits_route_call(tmp_repo, tmp_data_dir):
    (tmp_repo / "client.ts").write_text(
        "async function load() { return fetch('/api/items') }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="route-calls")
    assert r.returncode == 0, r.stderr
    calls = _read_nodes(tmp_data_dir, "route_calls")
    # route_call's signature carries the canonicalized url pattern.
    assert any(c.get("signature", {}).get("url_pattern") == "/api/items"
               for c in calls)


# --------------------------------------------------------------------------- #
# Service detector — emits service nodes for top-level non-private exports
# in lib/, pages/, services/, utils/.
# --------------------------------------------------------------------------- #

def test_service_relabels_function_in_lib(tmp_repo, tmp_data_dir):
    (tmp_repo / "lib").mkdir()
    (tmp_repo / "lib" / "api.ts").write_text(
        "export function fetchUsers() { return [] }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    assert "fetchUsers" in _symbols(svcs)


def test_service_relabels_function_in_pages(tmp_repo, tmp_data_dir):
    (tmp_repo / "pages").mkdir()
    (tmp_repo / "pages" / "dashboard.ts").write_text(
        "export function navigateToDashboard() { return null }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    assert "navigateToDashboard" in _symbols(svcs)


def test_service_skips_underscore_prefix(tmp_repo, tmp_data_dir):
    (tmp_repo / "lib").mkdir()
    (tmp_repo / "lib" / "helpers.ts").write_text(
        "function _internal() {}\nexport function pub() {}\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    syms = _symbols(svcs)
    assert "pub" in syms
    assert "_internal" not in syms


def test_service_ignores_non_service_path(tmp_repo, tmp_data_dir):
    (tmp_repo / "components").mkdir()
    (tmp_repo / "components" / "x.ts").write_text("export function foo() {}\n")
    r = _run(tmp_repo, tmp_data_dir, detectors="service")
    assert r.returncode == 0, r.stderr
    svcs = _read_nodes(tmp_data_dir, "services")
    assert "foo" not in _symbols(svcs)
