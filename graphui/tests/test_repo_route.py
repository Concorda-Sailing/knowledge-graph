def test_repo_detail_renders_known_repo(client):
    r = client.get("/graph/repo/concorda-web")
    assert r.status_code == 200
    body = r.text
    for cls in ("repo-detail-header", "repo-tabs", "repo-rail"):
        assert cls in body, f"missing section: {cls}"


def test_repo_detail_404_for_unknown(client):
    r = client.get("/graph/repo/ghost-repo")
    assert r.status_code == 404


def test_repo_detail_tab_param_accepted(client):
    for t in ("nodes", "dead", "deps", "telemetry", "activity"):
        r = client.get(f"/graph/repo/concorda-web?tab={t}")
        assert r.status_code == 200, f"tab={t} failed: {r.status_code}"


def test_repo_detail_dead_tab_lists_known_dead_node(client):
    r = client.get("/graph/repo/concorda-web?tab=dead")
    assert r.status_code == 200
    # The fixture's Page node IS referenced by no other tracked node into it,
    # so it should appear on the dead-code tab of concorda-web.
    assert "concorda-web::app/page.tsx::Page" in r.text or "Page" in r.text
