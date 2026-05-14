def test_settings_renders_200(client):
    r = client.get("/graph/settings")
    assert r.status_code == 200


def test_settings_includes_all_sections(client):
    r = client.get("/graph/settings")
    body = r.text
    for marker in ("Project", "Tracked repos", "Extractors"):
        assert marker in body, f"missing section header: {marker}"


def test_settings_lists_fixture_repos(client):
    r = client.get("/graph/settings")
    body = r.text
    # Fixture project.toml declares repos.web and repos.api.
    assert "concorda-web" in body
    assert "concorda-api" in body


def test_settings_lists_fixture_extractor(client):
    r = client.get("/graph/settings")
    body = r.text
    assert "example.py" in body
    # The fixture declared __extractor_version__ = "0.1.0".
    assert "0.1.0" in body
