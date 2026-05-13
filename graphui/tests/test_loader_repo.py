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
