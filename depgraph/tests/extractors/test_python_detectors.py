import ast
from pathlib import Path

from extractors.generic.python.detector_api import (
    DetectorContext, RelabelNode,
)
from extractors.generic.python.detectors.fastapi import FastAPIDetector
from extractors.generic.python.detectors.pydantic import PydanticDetector
from extractors.generic.python.detectors.sqlalchemy import SQLAlchemyDetector
from extractors.generic.python.extract import emit_primitives


def _run(src: str):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path="a.py")
    ctx = DetectorContext(repo_key="r", file_path="a.py", project_config={})
    return prims, FastAPIDetector().detect(tree, prims, ctx)


def test_fastapi_get_decorator_relabels_function():
    src = (
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/items')\n"
        "def list_items(): pass\n"
    )
    prims, muts = _run(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert len(rl) == 1
    assert rl[0].new_kind == "endpoint"
    assert rl[0].metadata["route"] == "/items"
    assert rl[0].metadata["method"] == "GET"


def test_fastapi_post_decorator():
    src = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.post('/x')\n"
        "def f(): pass\n"
    )
    _, muts = _run(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert rl[0].metadata["method"] == "POST"
    assert rl[0].metadata["route"] == "/x"


def test_fastapi_ignores_unrelated_decorators():
    src = "@property\ndef f(self): pass\n"
    _, muts = _run(src)
    assert muts == []


def test_fastapi_handles_async_endpoints():
    src = (
        "from fastapi import APIRouter\n"
        "r = APIRouter()\n"
        "@r.get('/x')\n"
        "async def f(): pass\n"
    )
    _, muts = _run(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert rl[0].new_kind == "endpoint"


def _run_sa(src: str):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path="a.py")
    ctx = DetectorContext(repo_key="r", file_path="a.py", project_config={})
    return prims, SQLAlchemyDetector().detect(tree, prims, ctx)


def test_sqlalchemy_declarative_base_subclass_relabeled_model():
    src = (
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase): pass\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
    )
    _, muts = _run_sa(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    user = next(m for m in rl if m.node_id.endswith(":User"))
    assert user.new_kind == "model"
    assert user.metadata["tablename"] == "users"


def test_sqlalchemy_ignores_plain_class():
    src = "class Plain: pass\n"
    _, muts = _run_sa(src)
    assert muts == []


def _run_pd(src: str):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path="a.py")
    ctx = DetectorContext(repo_key="r", file_path="a.py", project_config={})
    return prims, PydanticDetector().detect(tree, prims, ctx)


def test_pydantic_basemodel_subclass_relabeled_schema():
    src = (
        "from pydantic import BaseModel\n"
        "class UserIn(BaseModel):\n"
        "    name: str\n"
        "    age: int\n"
    )
    _, muts = _run_pd(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert len(rl) == 1
    assert rl[0].new_kind == "schema"
    assert sorted(rl[0].metadata["fields"]) == ["age", "name"]


from extractors.generic.python.detectors.pytest import PytestDetector


def _run_pt(src: str, rel="test_a.py"):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path=rel)
    ctx = DetectorContext(repo_key="r", file_path=rel, project_config={})
    return prims, PytestDetector().detect(tree, prims, ctx)


def test_pytest_function_relabeled_test():
    src = "def test_x(): pass\ndef helper(): pass\n"
    _, muts = _run_pt(src)
    rl = [m for m in muts if isinstance(m, RelabelNode) and m.new_kind == "test"]
    ids = [m.node_id for m in rl]
    assert any(i.endswith(":test_x") for i in ids)
    assert not any(i.endswith(":helper") for i in ids)


def test_pytest_test_class_methods_relabeled():
    src = "class TestThing:\n    def test_m(self): pass\n    def helper(self): pass\n"
    _, muts = _run_pt(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    names = [m.node_id.split(":")[-1] for m in rl]
    assert "TestThing.test_m" in names
    assert "TestThing.helper" not in names


def test_pytest_only_fires_in_test_files():
    src = "def test_x(): pass\n"
    _, muts = _run_pt(src, rel="mymodule.py")
    assert muts == []


def test_pytest_fires_in_underscore_test_suffix():
    src = "def test_y(): pass\n"
    _, muts = _run_pt(src, rel="api_test.py")
    rl = [m for m in muts if isinstance(m, RelabelNode) and m.new_kind == "test"]
    assert any(m.node_id.endswith(":test_y") for m in rl)
