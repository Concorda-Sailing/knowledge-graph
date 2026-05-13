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
