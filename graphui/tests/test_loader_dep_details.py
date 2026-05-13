def test_inbound_deps_detail_shape(loader):
    rows = loader.repo_inbound_deps_detail("concorda-api")
    # The fixture has concorda-web::Page → concorda-api::CrewService.
    assert isinstance(rows, list)
    if rows:
        r = rows[0]
        for k in ("from_repo", "from_id", "to_id"):
            assert k in r, f"missing key: {k}"


def test_inbound_deps_detail_for_unknown_repo_is_empty(loader):
    assert loader.repo_inbound_deps_detail("ghost") == []


def test_outbound_deps_detail_shape(loader):
    rows = loader.repo_outbound_deps_detail("concorda-web")
    assert isinstance(rows, list)
    if rows:
        r = rows[0]
        for k in ("to_repo", "from_id", "to_id"):
            assert k in r, f"missing key: {k}"


def test_dep_detail_skips_self_references(loader):
    inbound = loader.repo_inbound_deps_detail("concorda-web")
    # No row should have from_repo == basename
    assert all(r["from_repo"] != "concorda-web" for r in inbound)
    outbound = loader.repo_outbound_deps_detail("concorda-web")
    assert all(r["to_repo"] != "concorda-web" for r in outbound)


def test_repo_external_pkgs_shape(loader):
    pkgs = loader.repo_external_pkgs("concorda-web")
    assert isinstance(pkgs, list)
    for entry in pkgs:
        assert set(entry.keys()) >= {"name", "source"}
        assert entry["source"] in ("npm", "python")


def test_repo_external_pkgs_unknown_is_empty(loader):
    assert loader.repo_external_pkgs("ghost") == []
