from extractors.generic.python.detector_api import (
    RelabelNode, AddEdge, AddNode, DetectorContext, Detector,
)


def test_relabel_node_carries_id_kind_metadata():
    m = RelabelNode(node_id="repo:foo.py:bar", new_kind="endpoint",
                    metadata={"route": "/x"})
    assert m.node_id == "repo:foo.py:bar"
    assert m.new_kind == "endpoint"
    assert m.metadata == {"route": "/x"}


def test_add_edge_carries_from_to_kind():
    e = AddEdge(from_id="a", to_id="b", kind="calls")
    assert (e.from_id, e.to_id, e.kind) == ("a", "b", "calls")


def test_add_node_carries_kind_payload():
    n = AddNode(kind="route_call", payload={"url": "/x"})
    assert n.kind == "route_call"
    assert n.payload == {"url": "/x"}


def test_detector_context_dataclass():
    ctx = DetectorContext(repo_key="api", file_path="foo.py",
                          project_config={"detectors": ["fastapi"]})
    assert ctx.repo_key == "api"


def test_detector_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        Detector()
