"""Smoke test: fixtures load, loader imports, env is wired."""
def test_loader_imports_with_fixtures(loader):
    assert loader.DEPGRAPH.name == "depgraph"
    assert loader.LOGIGRAPH.name == "logigraph"
    nodes = loader.load_depgraph_nodes()
    assert any(n["id"] == "concorda-web::app/page.tsx::Page" for n in nodes)


def test_client_renders_index(client):
    r = client.get("/graph/")
    assert r.status_code == 200
    assert "graphui" in r.text.lower()
