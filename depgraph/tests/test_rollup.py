"""Tests for depgraph.lib.rollup — anchor resolution + BFS + formatting."""
from __future__ import annotations

from lib.rollup import resolve_anchor, AnchorResult


# Minimal fixture: two model nodes, a few domain nodes, no dependents needed
# at this stage (anchor resolution is read-only on the depgraph node set).

DEPGRAPH_NODES_FIXTURE = [
    {
        "id": "concorda-api::models/boat_crew.py::BoatCrew",
        "kind": "model",
        "signature": {"kind": "model", "name": "BoatCrew", "tablename": "boat_crew"},
        "source": {"repo": "concorda-api", "path": "models/boat_crew.py", "line": 12},
        "title": "BoatCrew",
    },
    {
        "id": "concorda-api::models/approval_vote.py::ApprovalVote",
        "kind": "model",
        "signature": {"kind": "model", "name": "ApprovalVote", "tablename": "approval_votes"},
        "source": {"repo": "concorda-api", "path": "models/approval_vote.py", "line": 8},
        "title": "ApprovalVote",
    },
    {
        "id": "concorda-api::models/sailing_event.py::SailingEvent",
        "kind": "model",
        "signature": {"kind": "model", "name": "SailingEvent", "tablename": "sailing_events"},
        "source": {"repo": "concorda-api", "path": "models/sailing_event.py", "line": 18},
        "title": "SailingEvent",
    },
]


def _depgraph_index():
    """Tiny in-memory index — by_id dict matches what compute_rollup expects."""
    return {n["id"]: n for n in DEPGRAPH_NODES_FIXTURE}


# --- Resource subkind ---------------------------------------------------------

def test_resolve_anchor_resource_by_table_match():
    domain_node = {
        "id": "resource::concorda::boat_crew",
        "subkind": "resource",
        "source": {
            "kind": "db_resource",
            "table": "boat_crew",
            "defined_in": "concorda-api/models/boat_crew.py",
        },
    }
    result = resolve_anchor(domain_node, _depgraph_index())
    assert result.model_id == "concorda-api::models/boat_crew.py::BoatCrew"
    assert result.reason == "table_match"


def test_resolve_anchor_resource_falls_back_to_defined_in_when_table_missing():
    domain_node = {
        "id": "resource::concorda::boat_crew",
        "subkind": "resource",
        "source": {
            "kind": "db_resource",
            "defined_in": "concorda-api/models/boat_crew.py",
        },
    }
    result = resolve_anchor(domain_node, _depgraph_index())
    assert result.model_id == "concorda-api::models/boat_crew.py::BoatCrew"
    assert result.reason == "defined_in"


# --- Role subkind: class-name match, NOT tablename ---------------------------

def test_resolve_anchor_role_matches_by_signature_name():
    domain_node = {
        "id": "role::relational::approval_voter",
        "subkind": "role",
        "source": {
            "kind": "relational",
            "table": "ApprovalVote",  # PascalCase class name
            "defined_in": "concorda-api/models/approval_vote.py",
        },
    }
    result = resolve_anchor(domain_node, _depgraph_index())
    assert result.model_id == "concorda-api::models/approval_vote.py::ApprovalVote"
    assert result.reason == "class_name_match"


# --- Attribute subkind: defined_in only --------------------------------------

def test_resolve_anchor_attribute_by_defined_in():
    domain_node = {
        "id": "attribute::sailing_event::accept_crew_requests",
        "subkind": "attribute",
        "source": {
            "kind": "conceptual",
            "predicate": "SailingEvent.accept_crew_requests == True",
            "defined_in": "concorda-api/models/sailing_event.py",
        },
    }
    result = resolve_anchor(domain_node, _depgraph_index())
    assert result.model_id == "concorda-api::models/sailing_event.py::SailingEvent"
    assert result.reason == "defined_in"


# --- Relationship subkind: recurse via mediated_by ---------------------------

def test_resolve_anchor_relationship_recurses_via_mediated_by():
    boat_crew_resource = {
        "id": "resource::concorda::boat_crew",
        "subkind": "resource",
        "source": {"kind": "db_resource", "table": "boat_crew", "defined_in": "concorda-api/models/boat_crew.py"},
    }
    rel = {
        "id": "relationship::boat::is_crewed_by",
        "subkind": "relationship",
        "mediated_by": "resource::concorda::boat_crew",
    }
    logigraph_index = {
        "resource::concorda::boat_crew": boat_crew_resource,
        "relationship::boat::is_crewed_by": rel,
    }
    result = resolve_anchor(rel, _depgraph_index(), logigraph_index=logigraph_index)
    assert result.model_id == "concorda-api::models/boat_crew.py::BoatCrew"
    assert result.reason == "via_mediated_by"


# --- No anchor found ---------------------------------------------------------

def test_resolve_anchor_returns_none_when_nothing_matches():
    domain_node = {
        "id": "resource::concorda::nonexistent_table",
        "subkind": "resource",
        "source": {
            "kind": "db_resource",
            "table": "nonexistent_table",
            "defined_in": "concorda-api/models/nonexistent.py",
        },
    }
    result = resolve_anchor(domain_node, _depgraph_index())
    assert result.model_id is None
    assert result.reason == "not_found"


import pytest


def test_resolve_anchor_relationship_raises_when_logigraph_index_omitted():
    rel = {
        "id": "relationship::boat::is_crewed_by",
        "subkind": "relationship",
        "mediated_by": "resource::concorda::boat_crew",
    }
    with pytest.raises(ValueError, match="logigraph_index is required"):
        resolve_anchor(rel, _depgraph_index())


from lib.rollup import compute_rollup, Rollup, Entry


# Reverse-dependents index — same shape as nodes/_index/dependents.json's
# by_target. Keys are *target* ids (what is depended on); values are lists of
# {source, via, confidence, where} entries describing each direct dependent.
DEPENDENTS_INDEX_FIXTURE = {
    # BoatCrew model is directly used by two services and one endpoint.
    "concorda-api::models/boat_crew.py::BoatCrew": [
        {"source": "concorda-api::services/boat_crew_invites.py::create_invite", "via": "import", "where": "services/boat_crew_invites.py:14"},
        {"source": "concorda-api::services/boat_crew_invites.py::accept_invite", "via": "import", "where": "services/boat_crew_invites.py:42"},
        {"source": "concorda-api::routes/boat_crew.py::POST /boats/{id}/crew/invites", "via": "import", "where": "routes/boat_crew.py:20"},
    ],
    # An endpoint that uses one of the services (transitive path to BoatCrew).
    "concorda-api::services/boat_crew_invites.py::create_invite": [
        {"source": "concorda-api::routes/boat_crew.py::POST /boats/{id}/crew/invites", "via": "call", "where": "routes/boat_crew.py:35"},
    ],
}

# Extend depgraph_index with the dependent nodes so compute_rollup can resolve
# their kind/title/path for rendering.
EXTRA_DEPGRAPH_NODES = [
    {
        "id": "concorda-api::services/boat_crew_invites.py::create_invite",
        "kind": "service",
        "signature": {"kind": "service", "name": "create_invite"},
        "source": {"repo": "concorda-api", "path": "services/boat_crew_invites.py", "line": 14},
        "title": "create_invite",
    },
    {
        "id": "concorda-api::services/boat_crew_invites.py::accept_invite",
        "kind": "service",
        "signature": {"kind": "service", "name": "accept_invite"},
        "source": {"repo": "concorda-api", "path": "services/boat_crew_invites.py", "line": 42},
        "title": "accept_invite",
    },
    {
        "id": "concorda-api::routes/boat_crew.py::POST /boats/{id}/crew/invites",
        "kind": "endpoint",
        "signature": {"kind": "endpoint", "method": "POST", "path": "/boats/{id}/crew/invites"},
        "source": {"repo": "concorda-api", "path": "routes/boat_crew.py", "line": 20},
        "title": "POST /boats/{id}/crew/invites",
    },
]


def _full_index():
    return {n["id"]: n for n in DEPGRAPH_NODES_FIXTURE + EXTRA_DEPGRAPH_NODES}


def test_compute_rollup_direct_only():
    rollup = compute_rollup(
        anchor_id="concorda-api::models/boat_crew.py::BoatCrew",
        depgraph_index=_full_index(),
        dependents_index=DEPENDENTS_INDEX_FIXTURE,
        depth=1,
    )
    # Anchor (the model itself) goes under "model".
    assert len(rollup.by_kind["model"]) == 1
    assert rollup.by_kind["model"][0].id == "concorda-api::models/boat_crew.py::BoatCrew"
    assert rollup.by_kind["model"][0].direct is True

    # Two direct services.
    service_ids = [e.id for e in rollup.by_kind["service"]]
    assert "concorda-api::services/boat_crew_invites.py::create_invite" in service_ids
    assert "concorda-api::services/boat_crew_invites.py::accept_invite" in service_ids
    for e in rollup.by_kind["service"]:
        assert e.direct is True
        assert e.via == ()

    # One direct endpoint.
    assert len(rollup.by_kind["endpoint"]) == 1
    assert rollup.by_kind["endpoint"][0].direct is True


def test_compute_rollup_depth_2_includes_transitive_via_chain():
    rollup = compute_rollup(
        anchor_id="concorda-api::models/boat_crew.py::BoatCrew",
        depgraph_index=_full_index(),
        dependents_index=DEPENDENTS_INDEX_FIXTURE,
        depth=2,
    )
    # The endpoint appears both directly AND transitively. De-dup: direct wins;
    # only the direct entry is kept.
    endpoint_entries = [e for e in rollup.by_kind["endpoint"]
                        if e.id == "concorda-api::routes/boat_crew.py::POST /boats/{id}/crew/invites"]
    assert len(endpoint_entries) == 1
    assert endpoint_entries[0].direct is True


def test_compute_rollup_empty_when_anchor_not_in_index():
    rollup = compute_rollup(
        anchor_id="bogus::id",
        depgraph_index=_full_index(),
        dependents_index=DEPENDENTS_INDEX_FIXTURE,
        depth=3,
    )
    assert rollup.total == 0
    assert all(v == [] for v in rollup.by_kind.values())


def test_compute_rollup_groups_sorted_alpha_within_kind():
    rollup = compute_rollup(
        anchor_id="concorda-api::models/boat_crew.py::BoatCrew",
        depgraph_index=_full_index(),
        dependents_index=DEPENDENTS_INDEX_FIXTURE,
        depth=1,
    )
    # accept_invite < create_invite alphabetically — should be sorted.
    service_titles = [e.title for e in rollup.by_kind["service"]]
    assert service_titles == sorted(service_titles)


def test_compute_rollup_handles_cycle_in_dependents_index():
    # A → B → A cycle. BFS must terminate via `seen`, not loop forever.
    a = {
        "id": "concorda-api::models/a.py::A",
        "kind": "model",
        "signature": {"kind": "model", "name": "A"},
        "source": {"repo": "concorda-api", "path": "models/a.py"},
        "title": "A",
    }
    b = {
        "id": "concorda-api::services/b.py::B",
        "kind": "service",
        "signature": {"kind": "service", "name": "B"},
        "source": {"repo": "concorda-api", "path": "services/b.py"},
        "title": "B",
    }
    depgraph = {a["id"]: a, b["id"]: b}
    deps = {
        a["id"]: [{"source": b["id"], "via": "import"}],
        b["id"]: [{"source": a["id"], "via": "import"}],  # cycle back
    }
    rollup = compute_rollup(
        anchor_id=a["id"],
        depgraph_index=depgraph,
        dependents_index=deps,
        depth=3,
    )
    # Anchor A + dependent B == 2 entries, no infinite loop.
    assert rollup.total == 2
    assert any(e.id == a["id"] for e in rollup.by_kind["model"])
    assert any(e.id == b["id"] for e in rollup.by_kind["service"])


from lib.rollup import format_rollup_text


def test_format_rollup_text_summary_caps_each_kind_at_3():
    # Build a rollup with 5 services.
    extra_services = [
        {
            "id": f"concorda-api::services/x.py::svc_{name}",
            "kind": "service",
            "signature": {"kind": "service", "name": f"svc_{name}"},
            "source": {"repo": "concorda-api", "path": "services/x.py", "line": 1},
            "title": f"svc_{name}",
        }
        for name in ("alpha", "bravo", "charlie", "delta", "echo")
    ]
    deps_idx = {
        "concorda-api::models/boat_crew.py::BoatCrew": [
            {"source": s["id"], "via": "import"} for s in extra_services
        ],
    }
    depgraph_index = {n["id"]: n for n in DEPGRAPH_NODES_FIXTURE + extra_services}
    rollup = compute_rollup(
        "concorda-api::models/boat_crew.py::BoatCrew",
        depgraph_index,
        deps_idx,
        depth=1,
    )
    out = format_rollup_text(rollup, summary=True)
    # Summary mode caps each kind at 3.
    assert "Service   (5)" in out
    assert "top 3 of 5" in out
    # The first three (alpha, bravo, charlie) appear; later ones do not.
    assert "svc_alpha" in out
    assert "svc_bravo" in out
    assert "svc_charlie" in out
    assert "svc_delta" not in out
    assert "svc_echo" not in out


def test_format_rollup_text_summary_no_truncation_marker_when_kind_under_cap():
    rollup = compute_rollup(
        "concorda-api::models/boat_crew.py::BoatCrew",
        _full_index(),
        DEPENDENTS_INDEX_FIXTURE,
        depth=1,
    )
    out = format_rollup_text(rollup, summary=True)
    # Two services fit under cap (3) — no "top X of Y" marker.
    assert "Service   (2)" in out
    assert "top" not in out.split("Service")[1].split("Endpoint")[0]


def test_format_rollup_text_no_anchor_renders_one_line_signal():
    from lib.rollup import _KIND_ORDER
    rollup = Rollup(
        anchor=AnchorResult(None, "not_found"),
        by_kind={k: [] for k in _KIND_ORDER},
        total=0,
    )
    out = format_rollup_text(rollup, summary=True)
    assert "no anchor" in out.lower()
    # Should not render empty kind headers.
    assert "Service" not in out
