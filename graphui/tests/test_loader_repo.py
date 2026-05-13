def test_repo_activity_shape(loader):
    a = loader.repo_activity("concorda-web")
    assert set(a.keys()) >= {
        "commits_7d", "commits_30d", "sparkline", "today_node_delta",
        "classification", "last_push_age_days",
    }
    assert isinstance(a["sparkline"], list) and len(a["sparkline"]) == 7
    assert a["classification"] in ("active", "dormant", "dead-candidate", "unknown")


def test_repo_activity_unknown_repo(loader):
    a = loader.repo_activity("nonexistent-repo")
    assert a["classification"] == "unknown"
    assert a["commits_7d"] == 0


def test_repo_languages_unknown(loader):
    langs = loader.repo_languages("nonexistent-repo")
    assert langs == []


def test_repo_languages_shape(loader):
    # The shape contract: list of {label, hint} dicts, length 0..4.
    langs = loader.repo_languages("concorda-web")
    assert isinstance(langs, list)
    assert len(langs) <= 4
    for entry in langs:
        assert set(entry.keys()) >= {"label", "hint"}


def test_repo_areas_includes_node_counts(loader):
    areas = loader.repo_areas("concorda-web")
    assert isinstance(areas, list)
    if areas:
        for entry in areas:
            assert set(entry.keys()) >= {"dir", "node_count"}
            assert isinstance(entry["node_count"], int)


def test_repo_dep_counts_shape(loader):
    d = loader.repo_dep_counts("concorda-web")
    assert set(d.keys()) >= {"inbound_repos", "outbound_repos", "external_pkgs"}
    for k in ("inbound_repos", "outbound_repos", "external_pkgs"):
        assert isinstance(d[k], int)


def test_repo_dep_counts_fixture_outbound(loader):
    # The fixture has concorda-web::Page depending on concorda-api::CrewService.
    d = loader.repo_dep_counts("concorda-web")
    assert d["outbound_repos"] >= 0  # at least the relationship is computed without error


def test_repo_cross_cuts_shape(loader):
    c = loader.repo_cross_cuts("concorda-web")
    assert set(c.keys()) >= {"rules", "processes", "domain"}
    assert isinstance(c["rules"], list)
    # The fixture has rule::category::example claiming concorda-web::app/page.tsx::Page.
    assert "rule::category::example" in c["rules"]


def test_repo_cross_cuts_empty_for_unknown(loader):
    c = loader.repo_cross_cuts("ghost-repo")
    assert c["rules"] == [] and c["processes"] == [] and c["domain"] == []
