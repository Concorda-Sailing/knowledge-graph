def test_cross_cutting_shape(loader):
    cc = loader.cross_cutting_summary()
    assert set(cc.keys()) >= {"rules", "domain", "processes"}

    r = cc["rules"]
    assert set(r.keys()) >= {"count", "claimed_repos", "namespaces"}
    assert r["count"] == 1
    assert isinstance(r["namespaces"], list)
    assert "category" in r["namespaces"]
    assert r["claimed_repos"] == 1  # the fixture rule claims one repo (concorda-web)

    d = cc["domain"]
    assert set(d.keys()) >= {"count", "subkinds", "referenced_by"}

    p = cc["processes"]
    assert set(p.keys()) >= {"count", "names", "spans_repos"}
