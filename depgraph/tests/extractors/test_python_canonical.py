from depgraph.extractors.python.canonical import (
    canonical_id, slugify_id, structural_hash,
)


def test_canonical_id_top_level():
    assert canonical_id("concorda-api", "routers/events.py", "create_event") == \
        "concorda-api::routers/events.py::create_event"


def test_canonical_id_method():
    assert canonical_id("concorda-api", "services/users.py", "UserService.fetch") == \
        "concorda-api::services/users.py::UserService.fetch"


def test_slugify():
    assert slugify_id("concorda-api::routers/events.py::create_event") == \
        "concorda_api__routers_events_py__create_event"


def test_structural_hash_stable_on_dict_key_order():
    a = structural_hash({"a": 1, "b": 2})
    b = structural_hash({"b": 2, "a": 1})
    assert a == b
    assert len(a) == 64
