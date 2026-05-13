"""URL-pattern normalization makes route_call URLs (from JS template literals)
join cleanly against endpoint paths (from Python framework decorators).

Normalization rule: collapse every variable segment to the literal token <var>.
"""
from extractors.reconcile import _normalize_url_pattern


def test_fastapi_braces():
    assert _normalize_url_pattern("/api/events/{id}/import") == "/api/events/<var>/import"


def test_fastapi_typed_braces():
    assert _normalize_url_pattern("/api/events/{id:int}/import") == "/api/events/<var>/import"
    assert _normalize_url_pattern("/api/files/{path:path}") == "/api/files/<var>"


def test_express_colon_prefix():
    assert _normalize_url_pattern("/api/events/:id/import") == "/api/events/<var>/import"


def test_already_tokenized_passthrough():
    assert _normalize_url_pattern("/api/events/<var>/import") == "/api/events/<var>/import"


def test_static_path_unchanged():
    assert _normalize_url_pattern("/api/health") == "/api/health"
    assert _normalize_url_pattern("/api/events/import/csv") == "/api/events/import/csv"


def test_multiple_variables():
    assert _normalize_url_pattern("/api/orgs/{org_id}/users/:user_id") == "/api/orgs/<var>/users/<var>"


def test_trailing_slash_preserved():
    assert _normalize_url_pattern("/api/events/") == "/api/events/"


def test_empty_and_none():
    assert _normalize_url_pattern("") == ""
    assert _normalize_url_pattern(None) is None
