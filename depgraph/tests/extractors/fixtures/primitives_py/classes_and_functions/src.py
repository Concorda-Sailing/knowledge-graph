def top_level(x: int) -> str:
    return str(x)

async def async_fn():
    pass

class Foo:
    field: int = 0
    CONST = "hi"

    def method(self, x: int) -> str:
        return str(x)

    async def async_method(self):
        pass

    @staticmethod
    def static_m(): pass

class GenericFoo[T, U]:
    pass

class Abstract(metaclass=ABCMeta):
    pass

class Outer:
    """Nested classes must produce primitives with dotted qualnames and
    owner pointing at the parent class id."""
    class Inner:
        def inner_method(self) -> int:
            return 1
