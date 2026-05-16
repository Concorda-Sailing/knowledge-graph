import functools


def my_decorator(fn):
    """A locally-defined decorator."""
    return fn


@my_decorator
def local_target():
    pass


@functools.lru_cache(maxsize=128)
def external_target():
    pass


def my_class_decorator(cls):
    return cls


@my_class_decorator
class LocalClass:
    pass
