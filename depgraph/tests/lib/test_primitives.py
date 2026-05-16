from depgraph.lib.primitives import (
    Primitive, PrimitiveKind, Source, Signature, Attributes,
    canonical_id, validate_primitive,
)


def test_canonical_id_top_level_function():
    assert canonical_id("concorda-api", "routers/events.py", "create_event") == \
        "concorda-api::routers/events.py::create_event"


def test_canonical_id_class_method_uses_dot():
    assert canonical_id("concorda-api", "services/users.py", "UserService.fetch") == \
        "concorda-api::services/users.py::UserService.fetch"


def test_primitive_kind_enum_values():
    assert {k.value for k in PrimitiveKind} == {"module", "package", "class", "function", "variable"}


def test_validate_primitive_accepts_minimal_function():
    p = Primitive(
        id="concorda-api::routers/events.py::create_event",
        primitive=PrimitiveKind.FUNCTION,
        name="create_event",
        owner=None,
        source=Source(repo="concorda-api", path="routers/events.py", language="python", line=10, end_line=20),
        signature=Signature(parameters=[], return_type=None, is_async=False, decorators=[]),
        attributes=Attributes(),
        edges_out=[],
        structural_hash="0" * 64,
        kind=None,
        extractor="test",
    )
    errors = validate_primitive(p.to_dict())
    assert errors == [], errors


def test_external_terminal_format():
    from depgraph.lib.primitives import external_terminal, is_external_terminal
    tid = external_terminal(ecosystem="pypi", package="sqlalchemy",
                              symbol="DeclarativeBase")
    assert tid == "external::pypi::sqlalchemy::DeclarativeBase"
    assert is_external_terminal(tid)
    assert not is_external_terminal("concorda-api::routers/events.py::create_event")


def test_structural_hash_payload_includes_body():
    from depgraph.lib.primitives import structural_hash_payload, compute_hash
    a = compute_hash(structural_hash_payload(
        primitive="function", name="f", signature={}, body_text="return 1"))
    b = compute_hash(structural_hash_payload(
        primitive="function", name="f", signature={}, body_text="return 2"))
    assert a != b, "body change must shift hash per spec"


def test_validate_primitive_rejects_method_without_owner():
    """A function with a `.` in its symbol must have owner set."""
    p_dict = {
        "schema_version": 2,
        "id": "concorda-api::services/users.py::UserService.fetch",
        "primitive": "function",
        "name": "UserService.fetch",
        "owner": None,
        "source": {"repo": "concorda-api", "path": "services/users.py", "language": "python", "line": 10, "end_line": 20},
        "signature": {"parameters": [], "return_type": None, "is_async": False, "decorators": []},
        "attributes": {},
        "edges_out": [],
        "structural_hash": "0" * 64,
        "kind": None,
        "extractor": "test",
    }
    errors = validate_primitive(p_dict)
    assert any("owner" in e for e in errors), f"expected owner-missing error, got: {errors}"


def test_slug_collision_helper():
    from depgraph.lib.primitives import check_slug_collisions
    # Two ids that slugify identically (the `:` and `-` both → `_`)
    primitives = [
        {"id": "r::a.b::x"},
        {"id": "r::a_b::x"},
    ]
    errors = check_slug_collisions(primitives)
    assert errors, "expected a collision report"
    assert any("a_b" in e or "a:b" in e or "collision" in e.lower() for e in errors)


def test_slug_collision_helper_clean_corpus():
    from depgraph.lib.primitives import check_slug_collisions
    primitives = [
        {"id": "r::foo.py::A"},
        {"id": "r::foo.py::B"},
    ]
    assert check_slug_collisions(primitives) == []
