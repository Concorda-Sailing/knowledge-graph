"""Shared fixtures for extractor tests."""
from pathlib import Path
import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create an empty repo dir; tests populate source files into it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create an empty data dir with nodes/ subdir."""
    data = tmp_path / "data"
    (data / "nodes").mkdir(parents=True)
    (data / "extractors" / "detectors").mkdir(parents=True)
    return data
