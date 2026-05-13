import datetime as dt
import os
from pathlib import Path


def test_activity_summary_shape(loader):
    s = loader.activity_summary()
    assert set(s.keys()) >= {"today", "week_sparkline", "thirty_day"}

    today = s["today"]
    assert set(today.keys()) >= {"nodes_added", "drafts_authored", "drift_events", "rules_authored"}
    for k in ("nodes_added", "drafts_authored", "drift_events", "rules_authored"):
        assert isinstance(today[k], int)

    spark = s["week_sparkline"]
    assert isinstance(spark, list) and len(spark) == 7
    assert all(isinstance(x, int) for x in spark)

    td = s["thirty_day"]
    assert set(td.keys()) >= {"nodes_added", "drafts_reviewed", "drift_events"}


def test_activity_counts_recent_node_file_as_added_today(loader, tmp_path, monkeypatch):
    # Touch one of the fixture node files to make it "added today" by mtime.
    fixture_node = loader.DEPGRAPH_NODES / "components" / "web__app__page_tsx__Page.json"
    now = dt.datetime.now().timestamp()
    os.utime(fixture_node, (now, now))
    s = loader.activity_summary()
    assert s["today"]["nodes_added"] >= 1
