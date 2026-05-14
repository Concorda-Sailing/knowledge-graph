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


def test_query_string_stripped():
    assert _normalize_url_pattern("/api/media/upload?on_duplicate=skip") == "/api/media/upload"
    # Query string with <var> placeholder (from a ternary in a template literal)
    assert _normalize_url_pattern("/api/media/upload<var>") == "/api/media/upload"
    # Real-world case: query string with template substitution
    assert _normalize_url_pattern("/api/admin/users/import?on_duplicate=<var>") == "/api/admin/users/import"
    # Already query-free path with path-var stays as-is
    assert _normalize_url_pattern("/api/events/{id}/import") == "/api/events/<var>/import"
