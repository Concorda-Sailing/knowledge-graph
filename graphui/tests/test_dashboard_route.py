def test_index_renders_all_sections(client):
    r = client.get("/graph/")
    assert r.status_code == 200
    body = r.text
    # presence of the new sections — match on stable CSS class names
    for cls in ("activity-strip", "health-tile", "cross-cutting", "repos-section"):
        assert cls in body, f"missing section: {cls}"


def test_index_activity_filter(client):
    r = client.get("/graph/?activity=active")
    assert r.status_code == 200
    assert "repos-filter-active" in r.text


def test_index_sort_param_accepted(client):
    for s in ("activity", "alpha", "inbound", "dead"):
        r = client.get(f"/graph/?sort={s}")
        assert r.status_code == 200, f"sort={s} failed: {r.status_code}"
