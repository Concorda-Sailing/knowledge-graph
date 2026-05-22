from depgraph.lib.primitives import (
    Primitive, PrimitiveKind, Source, Signature, Attributes,
    canonical_id, validate_primitive,
)


def test_canonical_id_top_level_function():
    assert canonical_id("acme-api", "routers/events.py", "create_event") == \
        "acme-api::routers/events.py::create_event"


def test_canonical_id_class_method_uses_dot():
    assert canonical_id("acme-api", "services/users.py", "UserService.fetch") == \
        "acme-api::services/users.py::UserService.fetch"


def test_primitive_kind_enum_values():
    assert {k.value for k in PrimitiveKind} == {"module", "package", "class", "function", "variable"}


def test_validate_primitive_accepts_minimal_function():
    p = Primitive(
        id="acme-api::routers/events.py::create_event",
        primitive=PrimitiveKind.FUNCTION,
        name="create_event",
        owner=None,
        source=Source(repo="acme-api", path="routers/events.py", language="python", line=10, end_line=20),
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
    assert not is_external_terminal("acme-api::routers/events.py::create_event")


def test_external_terminal_no_package_3_segment():
    """For ecosystems without packages (DB-API, unresolved), produce a
    3-segment id rather than collapsing to malformed external::eco::::sym."""
    from depgraph.lib.primitives import external_terminal
    assert external_terminal(ecosystem="unresolved", symbol="Foo") == \
        "external::unresolved::Foo"
    assert external_terminal(ecosystem="python-dbapi", package=None,
                              symbol="Cursor.execute") == \
        "external::python-dbapi::Cursor.execute"
    assert external_terminal(ecosystem="unresolved", package="",
                              symbol="Foo") == \
        "external::unresolved::Foo"


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
        "id": "acme-api::services/users.py::UserService.fetch",
        "primitive": "function",
        "name": "UserService.fetch",
        "owner": None,
        "source": {"repo": "acme-api", "path": "services/users.py", "language": "python", "line": 10, "end_line": 20},
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


def test_slug_collision_ignores_duplicate_ids():
    """Duplicate ids aren't slug collisions — they're a separate concern
    (duplicate primitives), surfaced elsewhere."""
    from depgraph.lib.primitives import check_slug_collisions
    primitives = [
        {"id": "r::a.py::Foo"},
        {"id": "r::a.py::Foo"},  # duplicate
    ]
    assert check_slug_collisions(primitives) == []


def test_slugify_pattern_1_dash_vs_slash_disambiguated():
    """#87 Pattern 1: `r::v4-mini` and `r::v4/mini` are distinct directory
    layouts that both used to slugify to `r__v4_mini` (the bare slug rewrites
    `-` and `/` identically). With the per-id hash suffix on lossy ids the
    two get distinct on-disk filenames."""
    from depgraph.lib.primitives import slugify_id_for_filename
    a = slugify_id_for_filename("r::pkg/v4-mini")
    b = slugify_id_for_filename("r::pkg/v4/mini")
    assert a != b, f"expected distinct slugs, both got {a!r}"


def test_slugify_pattern_2_trailing_dollar_disambiguated():
    """#87 Pattern 2: `r::pkg/index.ts` and `r::pkg/index.ts::$` both stripped
    trailing non-alphanumeric chars and collapsed to the same slug. The `$`
    here is a real symbol in TS code (e.g. zod's `const $ = execa(...)`), so
    it's load-bearing — the slug helper has to disambiguate, not the upstream
    extractor."""
    from depgraph.lib.primitives import slugify_id_for_filename
    a = slugify_id_for_filename("r::pkg/index.ts")
    b = slugify_id_for_filename("r::pkg/index.ts::$")
    assert a != b, f"expected distinct slugs, both got {a!r}"


def test_slugify_stable_across_calls():
    """The hash is deterministic in the id alone — a given id always maps to
    the same filename. Required so the writer and the reader (pre-edit hook)
    converge on the same on-disk path without sharing corpus state."""
    from depgraph.lib.primitives import slugify_id_for_filename
    a1 = slugify_id_for_filename("acme-api::pkg/foo.ts::Bar")
    a2 = slugify_id_for_filename("acme-api::pkg/foo.ts::Bar")
    assert a1 == a2


def test_slugify_bare_for_canonical_safe_ids():
    """The common case — a canonical `<repo>::<path>::<symbol>` whose only
    non-alphanumeric chars are `::`, `/`, and `.` — keeps a bare slug.
    Existing filenames don't shift for the typical Python module."""
    from depgraph.lib.primitives import slugify_id_for_filename
    assert slugify_id_for_filename("acmeapi::routers/events.py::create_event") == \
        "acmeapi__routers_events_py__create_event"


def test_slugify_appends_hash_for_lossy_ids():
    """Ids containing characters outside the safe set (`-`, `$`, space, …) get
    an 8-char sha1 suffix so the slug stays injective."""
    from depgraph.lib.primitives import slugify_id_for_filename
    slug = slugify_id_for_filename("acme-api::routers/events.py::create_event")
    assert slug.startswith("acme_api__routers_events_py__create_event_")
    suffix = slug.rsplit("_", 1)[-1]
    assert len(suffix) == 8
    assert all(c in "0123456789abcdef" for c in suffix)


def test_slugify_handles_id_that_is_only_lossy_chars():
    """Edge: an id like `$` (entirely non-alphanumeric) strips to empty and
    would otherwise produce a zero-length filename. The hash suffix becomes
    the whole slug in that case."""
    from depgraph.lib.primitives import slugify_id_for_filename
    slug = slugify_id_for_filename("$")
    # No leading underscore on the bare-empty form.
    assert slug and not slug.startswith("_")
    assert len(slug) == 8
