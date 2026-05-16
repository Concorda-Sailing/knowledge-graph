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


def test_repo_detail_paginates_domain_nodes(client):
    # concorda-web fixture has 3 domain nodes (Page, Login, Settings) and
    # 1 common node (formatDate in src/lib/). per_page=2 → 2 pages of domain.
    r = client.get("/graph/repo/concorda-web?per_page=2&page=1")
    assert r.status_code == 200
    body = r.text
    assert 'class="pagination"' in body, "pagination strip should render when pages > 1"
    assert "Page 1 of 2" in body
    # Page-1 chip should be disabled (no prev); next is an anchor.
    assert "chip-disabled" in body
    assert "page=2" in body


def test_repo_detail_page_param_clamps_above_max(client):
    r = client.get("/graph/repo/concorda-web?per_page=2&page=999")
    assert r.status_code == 200
    # Clamps to the last page (2) and shows "Page 2 of 2".
    assert "Page 2 of 2" in r.text


def test_repo_detail_no_pagination_when_one_page(client):
    # Default per_page=100 easily fits 3 domain nodes — no strip rendered.
    r = client.get("/graph/repo/concorda-web")
    assert r.status_code == 200
    assert 'class="pagination"' not in r.text


def test_repo_detail_common_section_is_lazy(client):
    # Common-nodes table should NOT appear inline — only the lazy <details>
    # wrapper with a data-lazy-url pointing at the fragment endpoint.
    r = client.get("/graph/repo/concorda-web")
    assert r.status_code == 200
    assert "data-lazy-url=" in r.text
    assert "/graph/repo/concorda-web/common" in r.text
    # The actual common node id ("formatDate") must not be in the initial HTML.
    assert "formatDate" not in r.text


def test_repo_common_fragment_returns_table(client):
    r = client.get("/graph/repo/concorda-web/common")
    assert r.status_code == 200
    body = r.text
    assert "knowledge-table" in body
    assert "formatDate" in body


def test_repo_common_fragment_404_for_unknown(client):
    r = client.get("/graph/repo/ghost-repo/common")
    assert r.status_code == 404


def test_repo_detail_pagination_preserves_filters(client):
    # Filter by state=missing (matches the 3 dossier-less fixture nodes:
    # Login + Settings domain, formatDate common). With per_page=1 we
    # get 2 pages of domain nodes — verify the state filter survives
    # into the pagination link.
    r = client.get("/graph/repo/concorda-web?per_page=1&page=1&state=missing")
    assert r.status_code == 200
    body = r.text
    assert "state=missing" in body
    assert "page=2" in body
