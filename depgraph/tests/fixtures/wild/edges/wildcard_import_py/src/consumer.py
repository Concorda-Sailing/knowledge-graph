"""`from helpers import *` pulls in every public name; the extractor can't
statically enumerate what's bound, so it emits a single module-level edge
with confidence "fuzzy" and `via: "wildcard_import"`.
"""
from helpers import *  # noqa: F401, F403


def use_them():
    return util_a() + util_b()
