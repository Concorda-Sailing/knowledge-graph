"""Membership — defined in the same file as Account so we can use a
real `Account | None` BinOp annotation without a circular import.

Mirrors the SQLModel pattern where mutually-referencing models live
in one module. The annotation walker descends into the BinOp,
filters out `None`, and resolves `Account` via the file's
top-level symbol table.
"""
from models.base import HybridBase, Relationship


class Account(HybridBase):
    __tablename__ = "accounts"

    # `list[Membership]` — Subscript wrapping a Name candidate.
    memberships: list["Membership"] = Relationship(back_populates="account")
    # Forward-ref string lookup across files (resolves via the
    # corpus-wide classname index).
    orders: list["Order"] = Relationship(back_populates="account")


class Membership(HybridBase):
    __tablename__ = "memberships"

    # `Account | None = Relationship(...)` — BinOp annotation; the
    # walker descends both sides, drops `None`, and resolves
    # `Account` against the file's top-level symbol table.
    account: Account | None = Relationship(back_populates="memberships")
