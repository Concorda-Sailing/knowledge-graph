def test_search_renders_empty_query(client):
    r = client.get("/graph/search")
    assert r.status_code == 200
    body = r.text
    assert "search-form" in body or "search-empty" in body


def test_search_returns_hits_for_query(client):
    r = client.get("/graph/search?q=landing+page")
    assert r.status_code == 200
    body = r.text
    # The fixture has a dossier_body row with text_preview "Landing page component."
    assert "concorda-web::app/page.tsx::Page" in body or "Landing page" in body


def test_search_scope_chip_param_accepted(client):
    for s in ("rules", "domain", "processes", "code", "dossiers"):
        r = client.get(f"/graph/search?q=example&scope={s}")
        assert r.status_code == 200, f"scope={s} failed: {r.status_code}"


def test_search_mode_param_accepted(client):
    for m in ("semantic", "dep", "knowledge"):
        r = client.get(f"/graph/search?q=example&mode={m}")
        assert r.status_code == 200, f"mode={m} failed: {r.status_code}"
        body = r.text
        # The active tab class should appear for the requested mode.
        assert "search-tab-active" in body
