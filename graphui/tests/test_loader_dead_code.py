def test_dead_code_returns_list_of_dicts(loader):
    rows = loader.repo_dead_code("concorda-web")
    assert isinstance(rows, list)
    for r in rows:
        for k in ("id", "title", "kind", "area", "href", "state"):
            assert k in r, f"missing key: {k}"


def test_dead_code_unknown_repo_empty(loader):
    assert loader.repo_dead_code("ghost") == []


def test_dead_code_excludes_nodes_with_inbound(loader):
    """The fixture has concorda-api::CrewService with 1 inbound dep.
    repo_dead_code on concorda-api must NOT include CrewService."""
    rows = loader.repo_dead_code("concorda-api")
    ids = [r["id"] for r in rows]
    assert "concorda-api::services/crew.py::CrewService" not in ids
