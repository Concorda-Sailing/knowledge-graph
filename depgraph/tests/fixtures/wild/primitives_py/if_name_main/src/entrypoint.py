"""Module with if __name__ == '__main__' guard and a dynamic class via type()."""

# These are genuine module-level primitives — always extracted.
APP_NAME: str = "myapp"
DEBUG: bool = False


class Config:
    """Public class — extracted."""
    host: str = "localhost"
    port: int = 8080


def setup_logging(level: str = "INFO") -> None:
    """Public function — extracted."""
    pass


def main() -> int:
    """Entry point function — extracted (it's a FunctionDef at module scope)."""
    return 0


# Dynamic class via type() — NOT extracted.
# The extractor only handles ClassDef nodes; type() calls are Assign nodes
# whose value is a Call, not a ClassDef. `DynConfig` appears as a variable.
DynConfig = type("DynConfig", (), {"host": "localhost"})


# Everything inside this if block is NOT extracted.
# _walk_module_body iterates tree.body; If nodes are not
# ClassDef / FunctionDef / Assign / AnnAssign so they are skipped entirely.
if __name__ == "__main__":
    GUARDED_CONSTANT = "never a primitive"

    class GuardedClass:
        """This class is invisible to the extractor."""
        value: int = 0

    def guarded_helper() -> None:
        """This function is invisible to the extractor."""
        pass

    raise SystemExit(main())
