import json
from pathlib import Path
from depgraph.lib.classification.engine import classify_corpus
from depgraph.lib.classification.writer import write_classified


def _make_primitive(*, id, name, primitive="function", decorators=None, kind=None):
    path_segment = id.split("::")[1]
    return {
        "id": id,
        "primitive": primitive,
        "name": name,
        "owner": None,
        "source": {"path": path_segment, "line": 1, "end_line": 1,
                   "language": "python", "repo": id.split("::")[0]},
        "signature": {"decorators": decorators or []},
        "attributes": {},
        "edges_out": [],
        "structural_hash": "0",
        "kind": kind,
        "extractor": "t",
        "schema_version": 2,
    }


def test_classified_primitive_lands_in_kind_dir(tmp_path):
    p = _make_primitive(
        id="r::p.py::create_event",
        name="create_event",
        decorators=["router.post"],
    )
    write_classified([p], classify_corpus([p]), data_dir=tmp_path)
    expected = tmp_path / "nodes/endpoints/r__p_py__create_event.json"
    assert expected.exists(), f"Expected {expected} to exist"
    written = json.loads(expected.read_text())
    assert written["kind"] == "endpoint"
    # classification metadata must be present
    assert "classification" in written
    assert written["classification"]["rule"] == "route_decorator"


def test_unclassified_primitive_lands_in_primitive_type_dir(tmp_path):
    """When no classifier fires, the writer routes to the primitive-type
    dir AND fills `kind` with the primitive value so the taxonomy stays
    uniform — every node carries a non-null kind, with primitive-level
    kinds at the base of the same hierarchy classified kinds layer onto."""
    p = _make_primitive(
        id="r::p.py::random_helper",
        name="random_helper",
    )
    write_classified([p], classify_corpus([p]), data_dir=tmp_path)
    expected = tmp_path / "nodes/functions/r__p_py__random_helper.json"
    assert expected.exists(), f"Expected {expected} to exist"
    written = json.loads(expected.read_text())
    assert written["kind"] == "function"  # unified taxonomy: default to primitive
    assert "classification" not in written  # no classifier ran — no metadata


def test_unclassified_class_takes_class_kind(tmp_path):
    """Same rule applies to every primitive type — class/module/variable/
    package nodes all get their primitive name as their kind when no
    classifier fires."""
    p = _make_primitive(
        id="r::p.py::Helper",
        name="Helper",
        primitive="class",
    )
    write_classified([p], classify_corpus([p]), data_dir=tmp_path)
    written = json.loads((tmp_path / "nodes/classes/r__p_py__Helper.json").read_text())
    assert written["kind"] == "class"


def test_extractor_set_kind_takes_precedence_over_primitive_default(tmp_path):
    """If the extractor already wrote a kind (e.g. SQL schema primitives),
    leave it alone — don't overwrite with the primitive name."""
    p = _make_primitive(
        id="r::migrations::001.py::users",
        name="users",
        primitive="class",
        kind="schema",
    )
    write_classified([p], classify_corpus([p]), data_dir=tmp_path)
    written = json.loads(
        (tmp_path / "nodes/schemas/r__migrations__001_py__users.json").read_text()
    )
    assert written["kind"] == "schema"
