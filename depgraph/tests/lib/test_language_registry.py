from pathlib import Path
from depgraph.lib.language_registry import (
    load_languages, Language,
)

FRAMEWORK_TOML = Path(__file__).resolve().parents[2] / "languages.toml"


def test_load_shipped_languages_includes_ts_py_sql():
    langs = load_languages(FRAMEWORK_TOML)
    names = {l.name for l in langs}
    assert "typescript" in names
    assert "python" in names
    assert "sql" in names


def test_typescript_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    ts = langs["typescript"]
    assert ts.extensions == [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]


def test_python_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    py = langs["python"]
    assert py.extensions == [".py"]


def test_sql_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    s = langs["sql"]
    assert s.extensions == [".sql"]


def test_extractor_path_resolves_under_framework_root():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    for name in ("typescript", "python", "sql"):
        l = langs[name]
        assert l.extractor.exists(), f"{name} extractor missing: {l.extractor}"


def test_per_project_language_adds_new_language(tmp_path):
    """A project.toml can register an entirely new language extractor."""
    project_toml = tmp_path / "project.toml"
    (tmp_path / "extract_yaml.py").touch()
    project_toml.write_text("""
[languages.yaml]
extensions = [".yaml", ".yml"]
extractor = "extract_yaml.py"
runtime = "python"
""")
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML, project_toml)}
    assert "yaml" in langs
    assert "typescript" in langs  # framework langs still present
    assert langs["yaml"].extensions == [".yaml", ".yml"]


def test_per_project_language_overrides_framework_by_name(tmp_path):
    """Project entry with the same name as a framework one replaces it."""
    project_toml = tmp_path / "project.toml"
    (tmp_path / "custom_python.py").touch()
    project_toml.write_text("""
[languages.python]
extensions = [".py", ".pyi"]
extractor = "custom_python.py"
runtime = "python"
""")
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML, project_toml)}
    py = langs["python"]
    assert py.extensions == [".py", ".pyi"]   # overridden
    assert py.extractor.name == "custom_python.py"
