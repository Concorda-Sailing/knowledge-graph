"""Annotation walker edge cases: string forward refs, builtin receivers,
typing.* aliasing. Each function exercises a single annotation shape so
the test can assert exactly one mapping."""
from __future__ import annotations
from typing import List, Dict
import typing
from sqlalchemy.orm import Session


def string_forward_ref(db: "Session"):
    """`db: 'Session'` — AST is ast.Constant; walker should ast.parse the
    string and resolve like the unquoted form."""
    db.flush()


def string_forward_ref_wrapped(db: "Optional[Session]"):
    """Forward ref with a wrapper: walker should parse and unwrap."""
    db.commit()


def builtin_list(xs: list):
    """`xs: list` — annotation is the lowercase builtin; method calls
    should attribute to `external::builtins::list`."""
    xs.append(object())


def builtin_dict(m: dict):
    """`m: dict` — `m.get(...)` should attribute to builtins.dict."""
    m.get("k")


def pep585_generic(xs: list[int]):
    """`xs: list[int]` (PEP 585) — non-transparent generic; container
    type is `list`, not the element type."""
    xs.append(1)


def typing_list_from_import(xs: List[int]):
    """`from typing import List; xs: List[int]` — `typing.List` is a
    deprecated alias for `list`; method calls should attribute to `list`,
    not `typing.List`."""
    xs.append(1)


def typing_dict_from_import(m: Dict[str, int]):
    """`from typing import Dict; m: Dict[str, int]` — same as above for Dict."""
    m.get("k")


def typing_list_via_attribute(xs: typing.List[int]):
    """`import typing; xs: typing.List[int]` — attribute-access form of
    the typing alias; walker should still resolve to the builtin."""
    xs.append(1)
