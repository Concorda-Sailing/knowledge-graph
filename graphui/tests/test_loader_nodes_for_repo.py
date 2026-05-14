def test_nodes_for_repo_returns_flat_list(loader):
    rows = loader.nodes_for_repo("concorda-web")
    assert isinstance(rows, list)
    assert rows, "fixture should yield at least one node"
    r = rows[0]
    # Universal node-list shape: title, kind, fan_out, state, href, id, area
    for k in ("id", "title", "kind", "fan_out", "state", "href", "area"):
        assert k in r, f"missing key: {k}"


def test_nodes_for_repo_filters_kind(loader):
    rows = loader.nodes_for_repo("concorda-web", kind="component")
    assert all(r["kind"] == "component" for r in rows)


def test_nodes_for_repo_filters_area(loader):
    # The fixture node is under "app/page.tsx" → area "app"
    rows = loader.nodes_for_repo("concorda-web", area="app")
    assert all(r["area"] == "app" for r in rows)


def test_nodes_for_repo_filters_tier(loader):
    rows = loader.nodes_for_repo("concorda-web", tier="C")  # fan_out=5 → tier B; expect 0 of C in fixture
    # Just verify the filter is applied; do not pin a count.
    assert all(r.get("tier") == "C" for r in rows)


def test_nodes_for_repo_sorts_by_fan_out_desc_by_default(loader):
    rows = loader.nodes_for_repo("concorda-web")
    fan_outs = [r["fan_out"] for r in rows]
    assert fan_outs == sorted(fan_outs, reverse=True)


def test_nodes_for_repo_unknown_repo_returns_empty(loader):
    assert loader.nodes_for_repo("ghost-repo") == []
