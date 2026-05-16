class SomeClass:
    def method(self, x: int) -> int:
        return x


# Monkey-patch: replace the method at runtime
SomeClass.method = lambda self, x: x * 2


def use_it(obj: SomeClass) -> int:
    return obj.method(5)
