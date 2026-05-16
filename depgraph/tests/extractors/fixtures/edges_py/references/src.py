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
