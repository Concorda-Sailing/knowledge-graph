COUNTER = 0
NAME = "default"


def get_counter() -> int:
    return COUNTER


def get_name() -> str:
    return NAME


def increment():
    global COUNTER
    COUNTER += 1


def reset():
    global COUNTER
    global NAME
    COUNTER = 0
    NAME = "default"
