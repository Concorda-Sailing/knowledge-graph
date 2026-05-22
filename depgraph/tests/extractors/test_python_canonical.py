from depgraph.extractors.python.canonical import (
    canonical_id, slugify_id, structural_hash,
)


def test_canonical_id_top_level():
    assert canonical_id("acme-api", "routers/events.py", "create_event") == \
        "acme-api::routers/events.py::create_event"


def test_canonical_id_method():
    assert canonical_id("acme-api", "services/users.py", "UserService.fetch") == \
        "acme-api::services/users.py::UserService.fetch"


def test_slugify_safe_chars_stays_bare():
    """Ids whose only special chars are `/`, `.`, and `::` keep a bare slug —
    these are the common case (canonical `<repo>::<path>::<symbol>` for
    alphanumeric repo names)."""
    assert slugify_id("acmeapi::routers/events.py::create_event") == \
        "acmeapi__routers_events_py__create_event"


def test_slugify_lossy_chars_gets_hash_suffix():
    """Ids containing characters outside the safe set (e.g., `-` in a repo
    name) get an 8-char sha1 suffix so distinct ids stay distinct on disk
    (#87 — Pattern 1: `v4-mini` vs `v4/mini` would otherwise collide)."""
    slug = slugify_id("acme-api::routers/events.py::create_event")
    # Bare body stays readable; hash suffix appended.
    assert slug.startswith("acme_api__routers_events_py__create_event_")
    # 8-char hex suffix.
    suffix = slug.rsplit("_", 1)[-1]
    assert len(suffix) == 8 and all(c in "0123456789abcdef" for c in suffix)


def test_structural_hash_stable_on_dict_key_order():
    a = structural_hash({"a": 1, "b": 2})
    b = structural_hash({"b": 2, "a": 1})
    assert a == b
    assert len(a) == 64
