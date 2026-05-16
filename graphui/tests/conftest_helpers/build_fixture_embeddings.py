#!/usr/bin/env python3
"""Run once to (re)generate the test fixture embedding indexes.

Embeds a small set of synthetic strings for the depgraph + logigraph
test fixtures and writes embeddings.{bin,jsonl} to each fixture's
_index/ dir. Commit the result alongside the fixture node JSON.

Why not generate at test time? Tests can then read the indexes without
needing fastembed installed in the test environment. Same trick as
test_smoke.py reading the fixture node JSON directly.
"""
import sys
from pathlib import Path

# Reuse depgraph's lib via the framework root.
HERE = Path(__file__).resolve().parent
GRAPHUI = HERE.parent.parent
FRAMEWORK_ROOT = GRAPHUI.parent  # ~/tools/knowledge-graph
sys.path.insert(0, str(FRAMEWORK_ROOT))
from depgraph.lib.embeddings import embed_chunks, write_index  # noqa: E402


def build_depgraph_fixture():
    base = GRAPHUI / "tests" / "fixtures" / "depgraph" / "nodes" / "_index"
    base.mkdir(parents=True, exist_ok=True)
    rows = [
        {"row": 0, "node_id": "concorda-web::app/page.tsx::Page",
         "chunk_index": 0, "content_hash": "sha256:fixture-page-0",
         "text_preview": "Landing page component.",
         "source_field": "dossier_body"},
    ]
    vecs = embed_chunks(["Landing page component. Renders the dashboard."])
    write_index(base / "embeddings.bin", base / "embeddings.jsonl", vecs, rows)
    print(f"depgraph fixture: 1 row written to {base}")


def build_logigraph_fixture():
    base = GRAPHUI / "tests" / "fixtures" / "logigraph" / "nodes" / "_index"
    base.mkdir(parents=True, exist_ok=True)
    rows = [
        {"row": 0, "node_id": "rule::category::example",
         "chunk_index": 0, "content_hash": "sha256:fixture-rule-0",
         "text_preview": "Always do the right thing.",
         "source_field": "rule_statement"},
    ]
    vecs = embed_chunks(["Always do the right thing. This is a rule about correctness."])
    write_index(base / "embeddings.bin", base / "embeddings.jsonl", vecs, rows)
    print(f"logigraph fixture: 1 row written to {base}")


if __name__ == "__main__":
    build_depgraph_fixture()
    build_logigraph_fixture()
    print("fixture embeddings rebuilt")
