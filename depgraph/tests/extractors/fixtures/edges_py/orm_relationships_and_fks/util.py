"""Non-ORM module — the helper class here must NOT get walked by the
ORM pass, even though it calls something *named* `relationship` (we
shadow the symbol locally to make sure the pass keys off class
inheritance, not callee name)."""


class _LocalHelper:
    """Stand-in callable so we can name the call `relationship(...)` in
    the body of `NonOrmClass` without importing SQLAlchemy."""

    def __call__(self, *args, **kwargs):  # pragma: no cover - fixture stub
        return None


relationship = _LocalHelper()


class NonOrmClass:
    """No SQLAlchemy base — must not accumulate `references_orm` /
    `references_table` edges even though the body uses the keyword
    `relationship(...)`."""

    related = relationship("Account")
