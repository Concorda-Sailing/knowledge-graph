"""Pytest fixtures for graphui.

Sets DEPGRAPH_DATA_DIR / LOGIGRAPH_DATA_DIR BEFORE any test module imports
the loader (which resolves env vars at import time). If tests import the
loader, they must use the `loader` fixture below, which reloads the module
to pick up the env vars from this conftest.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# Set env vars at module import time so any subsequent `import app.loader`
# (in a test module, fixture, or app import chain) sees them.
os.environ["DEPGRAPH_DATA_DIR"] = str(FIXTURES / "depgraph")
os.environ["LOGIGRAPH_DATA_DIR"] = str(FIXTURES / "logigraph")

# Make `app` importable when running pytest from the project root.
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@pytest.fixture
def loader():
    """Reload app.loader so a fresh import picks up the conftest env vars
    (in case a prior test module imported it before env was set)."""
    from app import loader as mod
    return importlib.reload(mod)


@pytest.fixture
def client():
    """FastAPI TestClient bound to the app."""
    from fastapi.testclient import TestClient
    from app import main as mainmod
    importlib.reload(mainmod)  # pick up env-resolved loader
    return TestClient(mainmod.app)
