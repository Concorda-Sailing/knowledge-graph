"""Dynamic dispatch via importlib.import_module / __import__ —
issue #90. Both shapes return a module value at runtime; calling
it (`importlib.import_module("foo")(...)`) is pure dynamic dispatch.
"""

import importlib


def via_importlib(name):
    return importlib.import_module(name)()


def via_dunder(name):
    return __import__(name)()
