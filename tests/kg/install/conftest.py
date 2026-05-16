import pytest
from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """tmp_path/myproject — destination for `kg install init <path>`."""
    return tmp_path / "myproject"
