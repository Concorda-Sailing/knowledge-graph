"""General / language-baseline plugins. Always active.

These plugins carry cues that aren't tied to any specific framework — the
things every Python / TS / JS codebase tends to use regardless of the web
framework, ORM, or test runner picked. Anything framework-specific lives
in its own plugin (react/, fastapi/, sqlalchemy/, etc.).
"""
from depgraph.plugins.general.python import PLUGIN as python_plugin
from depgraph.plugins.general.typescript import PLUGIN as typescript_plugin

__all__ = ["python_plugin", "typescript_plugin"]
