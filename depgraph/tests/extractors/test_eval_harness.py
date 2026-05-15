import json
import os
from pathlib import Path

import pytest

from extractors.eval.harness import (
    EvalCase, load_case, run_deterministic,
)


def test_load_case_parses_files(tmp_path: Path):
    case = tmp_path / "case1"
    (case / "source").mkdir(parents=True)
    (case / "source" / "a.py").write_text("def hi(): pass\n")
    (case / "expected.json").write_text(json.dumps({
        "nodes": {"function": ["r:a.py:hi"]},
    }))
    (case / "case.toml").write_text('detectors = []\nlanguage = "python"\n')
    c = load_case(case)
    assert isinstance(c, EvalCase)
    assert c.language == "python"
    assert c.expected["nodes"]["function"] == ["r:a.py:hi"]


def test_run_deterministic_reports_precision_recall(tmp_path: Path):
    case = tmp_path / "c"
    (case / "source").mkdir(parents=True)
    (case / "source" / "a.py").write_text("def hi(): pass\ndef ho(): pass\n")
    (case / "expected.json").write_text(json.dumps({
        "nodes": {"function": ["r:a.py:hi"]},  # intentionally incomplete
    }))
    (case / "case.toml").write_text('detectors = []\nlanguage = "python"\n')
    report = run_deterministic(case, repo_key="r")
    assert report["passed"] is True  # superset is OK; only declared expectations are checked
    assert report["precision"]["function"] == 1.0
    assert report["recall"]["function"] == 1.0


from extractors.eval.judge import write_judgment_package


def test_judgment_package_contains_source_and_emitted_nodes(tmp_path: Path):
    case = tmp_path / "c"
    (case / "source").mkdir(parents=True)
    (case / "source" / "a.py").write_text("def hi(): pass\n")
    (case / "expected.json").write_text("{}")
    (case / "case.toml").write_text('detectors = []\nlanguage = "python"\n')
    (case / "judgments").mkdir(exist_ok=True)
    out = write_judgment_package(case)
    assert out.name == "pending.md"
    text = out.read_text()
    assert "def hi(): pass" in text
    assert "## Emitted nodes" in text
    assert "## Judgment prompt" in text


@pytest.mark.skipif(
    not os.environ.get("KG_EVAL"),
    reason="KG_EVAL=1 to run full eval corpus",
)
def test_all_seed_cases_pass():
    from extractors.eval.harness import run_deterministic
    corpus = Path(__file__).resolve().parents[3] / "depgraph" / "extractors" / "eval" / "corpus"
    failures = []
    for lang_dir in corpus.iterdir():
        if not lang_dir.is_dir():
            continue
        for case_dir in lang_dir.iterdir():
            if not case_dir.is_dir():
                continue
            rpt = run_deterministic(case_dir)
            if not rpt["passed"]:
                failures.append((case_dir.name, rpt))
    assert not failures, f"eval regressions: {failures}"
