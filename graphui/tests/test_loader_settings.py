def test_read_project_toml_returns_dict(loader):
    cfg = loader.read_project_toml()
    assert isinstance(cfg, dict)
    assert cfg["project"]["name"] == "fixture-project"
    assert cfg["project"]["primary_repo"] == "web"
    assert set(cfg["repos"].keys()) >= {"web", "api"}


def test_tracked_repos_settings_shape(loader):
    rows = loader.tracked_repos_settings()
    assert isinstance(rows, list) and len(rows) >= 2
    r = rows[0]
    for k in ("key", "basename", "path", "git_remote", "extractor_cmd",
             "extractor_file", "files_arg"):
        assert k in r, f"missing key: {k}"
    # extractor_cmd is the literal list from project.toml.
    assert isinstance(r["extractor_cmd"], list)
    # files_arg is None for repos without one, a string when set.
    web = next(x for x in rows if x["key"] == "web")
    api = next(x for x in rows if x["key"] == "api")
    assert web["files_arg"] is None
    assert api["files_arg"] == "--only"


def test_extractor_inventory_shape(loader):
    inv = loader.extractor_inventory()
    assert isinstance(inv, list)
    # Should include the fixture's example.py.
    files = [e["filename"] for e in inv]
    assert "example.py" in files
    ex = next(e for e in inv if e["filename"] == "example.py")
    for k in ("filename", "path", "size_bytes", "mtime_iso",
             "sha256_prefix", "scope", "declared_version"):
        assert k in ex, f"missing key: {k}"
    assert ex["scope"] == "project"
    assert ex["declared_version"] == "0.1.0"  # parsed from __extractor_version__
    assert len(ex["sha256_prefix"]) == 12  # short hex
