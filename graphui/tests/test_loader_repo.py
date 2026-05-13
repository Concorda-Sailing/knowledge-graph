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
