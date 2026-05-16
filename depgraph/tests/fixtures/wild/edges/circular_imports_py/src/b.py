from .a import hello


def greet(name: str) -> str:
    return f"hello {name}"


def call_back():
    return hello()
