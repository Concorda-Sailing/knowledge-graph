"""Dynamic dispatch via globals()/locals()/vars() lookup — issue #90.

`globals()[name](...)` is the classic plugin-lookup pattern; locals
and vars are rarer but structurally identical.
"""


def call_global(name):
    return globals()[name]()


def call_local(name):
    helper = lambda: "ok"  # noqa: E731
    return locals()[name]()


def call_via_vars(obj, name):
    return vars(obj)[name]()
