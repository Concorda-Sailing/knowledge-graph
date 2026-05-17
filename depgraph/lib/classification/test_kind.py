"""Test classifier — functions that are test framework primitives.

KIND is "test" (not "test_kind") to avoid collision with pytest's
file-discovery pattern for files named test_*.py.

A function is classified as test iff any of:
  (a) has a `tests` edge outgoing (placed by Phase 3.6 edge extractor), OR
  (b) has a decorator starting with "pytest." (e.g. pytest.fixture,
      pytest.mark.parametrize), OR
  (c) lives in a test-named file (test_*.py, *_test.py, *.test.ts/js/tsx)
      AND its name starts with "test".
"""
from __future__ import annotations

KIND = "test"

_TEST_PREFIXES = ("test_", "test")


def _in_test_file(path: str) -> bool:
    filename = path.split("/")[-1]
    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or ".test." in filename
    )


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue

        has_tests_edge = any(
            e["kind"] == "tests" for e in by_source.get(p["id"], [])
        )
        decs = p["signature"].get("decorators", [])
        is_pytest_decorated = any(d.startswith("pytest.") for d in decs)
        in_test_file = _in_test_file(p["source"]["path"])
        name_starts_test = p["name"].startswith(_TEST_PREFIXES)

        if has_tests_edge or is_pytest_decorated or (in_test_file and name_starts_test):
            reasons = []
            if has_tests_edge:
                reasons.append("has_tests_edge")
            if is_pytest_decorated:
                reasons.append("pytest_decorator")
            if in_test_file and name_starts_test:
                reasons.append("test_filename_and_name")
            decisions[p["id"]] = {
                "rule": "test_framework_primitive",
                "evidence": [{"reasons": reasons}],
            }
    return decisions
