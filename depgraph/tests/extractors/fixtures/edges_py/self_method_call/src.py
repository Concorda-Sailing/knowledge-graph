"""`self.X()` from inside a method must resolve to the sibling method.

Before #91 (b1), `self` was never seeded into `var_types` for the
function-body walker, so every `self.method(...)` call emitted
`external::unresolved::self.method` — a bug-signal that hid in the
typed-receiver bucket. The fix seeds `var_types[<first-arg>] =
[enclosing_class_id]` for any function whose owner is a class (skipping
explicitly @staticmethod-decorated ones)."""
from __future__ import annotations


class Service:
    def do_work(self) -> None:
        # `self.helper(...)` should resolve to Service.helper, not
        # `external::unresolved::self.helper`.
        self.helper()

    def helper(self) -> None:
        pass

    @staticmethod
    def static_no_seed() -> None:
        # Staticmethods don't get `self`-seeding — the first arg here is
        # not an instance. (Nothing to assert directly; included so the
        # decorator skip path is exercised.)
        pass
