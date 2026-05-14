def test_graph_health_shape(loader):
    h = loader.graph_health()
    assert set(h.keys()) >= {"telemetry", "calibration", "hottest_rules"}

    t = h["telemetry"]
    assert set(t.keys()) >= {"injections_30d", "ack_rate_pct", "dead_rules", "never_acked_dossiers", "trend_pct"}
    assert t["injections_30d"] == 3  # all three fixture injections are within 30 days
    assert 0 <= t["ack_rate_pct"] <= 100

    c = h["calibration"]
    assert set(c.keys()) >= {"accuracy_pct", "regressions", "last_run_id", "drifted_rules"}
    assert c["accuracy_pct"] == 100  # the fixture run has 1 pass / 0 fail
    assert c["last_run_id"] == "20260512-090000"
    assert c["regressions"] == 0

    hr = h["hottest_rules"]
    assert isinstance(hr, list)
    if hr:
        assert set(hr[0].keys()) >= {"id", "count"}
