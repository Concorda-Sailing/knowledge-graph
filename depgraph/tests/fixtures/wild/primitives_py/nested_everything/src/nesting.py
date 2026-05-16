"""Nesting: class-in-class recurses; class/func inside function does not."""


class Outer:
    """Top-level class."""

    class Inner:
        """Nested class — extracted recursively with qualname Outer.Inner."""

        class Deepest:
            """Three levels deep: Outer.Inner.Deepest."""

            def deep_method(self) -> None:
                pass

        def inner_method(self) -> int:
            return 42

    x: int = 0

    def outer_method(self) -> str:
        # Everything defined inside this function body is function-local.
        # The extractor does NOT recurse into FunctionDef bodies, so
        # LocalClass, local_helper, and their members are NOT extracted.
        class LocalClass:
            def local_method(self): pass

        def local_helper(): pass

        return "outer"


def top_func() -> None:
    """Module-level function. Its local nested class is NOT extracted."""

    class FuncLocal:
        """Only exists at runtime inside top_func — not a module primitive."""
        value: int = 1

        def method(self): pass

    def nested_def() -> None:
        pass
