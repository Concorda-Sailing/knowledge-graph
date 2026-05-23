"""Dynamic dispatch via getattr — issue #90.

`getattr(obj, name)(...)` and the 3-arg form with a default are pure
runtime dispatch: no static pass can resolve `name` to a method id
without dataflow we don't have. Stamp confidence=dynamic.
"""


class Handler:
    def run(self):
        return "ok"


def dispatch(obj: Handler, name: str):
    return getattr(obj, name)()


def dispatch_with_default(obj: Handler, name: str):
    return getattr(obj, name, lambda: None)()
