"""pytest plugin.

Activates when `pytest` is a Python dependency, or a `pytest.ini` /
`pyproject.toml` configures pytest. Contributes the test-framework
primitives the classifier checks decorator prefixes against.

Module is named `pytest_plugin` (not `pytest`) to avoid shadowing the
actual `pytest` package on import.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_marker_file, has_pypi_dep


def _detect(repo_path) -> bool:
    if has_pypi_dep(repo_path, "pytest"):
        return True
    if has_marker_file(repo_path, "pytest.ini", "setup.cfg"):
        # setup.cfg false-positives a bit, but a project that ships
        # one alongside Python sources is very likely using pytest.
        return True
    # `pyproject.toml` with a `[tool.pytest]` section also counts.
    pyproject = repo_path / "pyproject.toml"
    if pyproject.is_file():
        try:
            return "[tool.pytest" in pyproject.read_text()
        except OSError:
            return False
    return False


PLUGIN = Plugin(
    name="pytest",
    detect=_detect,
    cues={
        "python": LanguageCues(
            test_framework_primitives={
                "pytest.fixture", "pytest.mark", "pytest.raises",
                "pytest.parametrize", "pytest.skip", "pytest.xfail",
            },
        ),
    },
)
