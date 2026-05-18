GLOBAL = 0

def reader():
    return GLOBAL

def writer():
    global GLOBAL
    GLOBAL = 1

import functools
@functools.lru_cache()
def decorated():
    pass

def local_dec(fn):
    return fn

@local_dec
def locally_decorated():
    pass


# Framework-style decorator-method-call pattern: a module-level variable
# whose `.method(...)` returns a decorator. The extractor anchors the
# `decorates` edge to the variable (#30).
class _Router:
    def get(self, path):
        def deco(fn):
            return fn
        return deco

router = _Router()

@router.get("/login")
def framework_decorated():
    pass
