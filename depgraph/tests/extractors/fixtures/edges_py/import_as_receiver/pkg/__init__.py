"""In-corpus package that exposes both a directly-defined function
(`do_thing`) and a re-exported one (`echo`, from .utils)."""
from __future__ import annotations

from .utils import echo as echo


def do_thing() -> int:
    return 42
