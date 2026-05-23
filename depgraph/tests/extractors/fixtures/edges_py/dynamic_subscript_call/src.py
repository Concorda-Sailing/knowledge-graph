"""Dynamic dispatch via subscript-as-callee — issue #90.

`obj[key](...)` where `key` is a variable (not a constant string) is
pure runtime dispatch. The common case is a registry dict.
"""


def dispatch(registry, name):
    return registry[name]()


def dispatch_method_table(self, name: str):
    # The registry lives on the instance; key is a runtime name.
    return self.handlers[name]()
