from extractors.generic.python.canonical import (
    slugify_id_py, structural_hash, canonical_path,
    canonical_id_for_endpoint, canonical_id_for_repo_symbol,
)


def test_slugify_id_py_matches_pre_flip():
    # From real pre-flip: endpoint dossier filename
    assert slugify_id_py("DELETE::/api/admin/email-templates/{0}") \
        == "DELETE___api_admin_email-templates_0"
    # Service dossier filename
    assert slugify_id_py("concorda-api::services/approvals.py::cast_vote") \
        == "concorda-api__services_approvals.py__cast_vote"


def test_structural_hash_endpoint_reproduces_pre_flip():
    # From DELETE /api/admin/email-templates/{template_id}
    payload = {
        "method": "DELETE",
        "path": "/api/admin/email-templates/{0}",
        "auth": "none",
        "request": None,
        "response": None,
    }
    assert structural_hash(payload) == \
        "dc232955b0ec6500ba3c7be14af012393377816b145ae350757ef09d79523a6a"


def test_structural_hash_model_reproduces_pre_flip():
    payload = {"name": "AccountSetupToken", "kind": "model",
               "tablename": "account_setup_tokens"}
    assert structural_hash(payload) == \
        "ffb3adef2bc6a3423c51e35cfa069d3fec41f5614e3bb0e798031d31d175235a"


def test_structural_hash_schema_reproduces_pre_flip():
    payload = {"name": "ApprovalRequestCreate", "kind": "schema",
               "fields": ["request_type", "subject_uuid", "target_state"]}
    assert structural_hash(payload) == \
        "3e9823a12a6c2272bbec9c9f6e020ab9d66ea3a9f2287a0ba2d057583f728593"


def test_canonical_path():
    assert canonical_path("/users/{id}") == "/users/{0}"
    assert canonical_path("/users/{user_id}/posts/{post_id}") \
        == "/users/{0}/posts/{1}"
    assert canonical_path("/health") == "/health"


def test_canonical_id_for_endpoint():
    assert canonical_id_for_endpoint("DELETE", "/api/admin/email-templates/{template_id}") \
        == "DELETE::/api/admin/email-templates/{0}"


def test_canonical_id_for_repo_symbol():
    assert canonical_id_for_repo_symbol("concorda-api", "models/user.py", "User") \
        == "concorda-api::models/user.py::User"
