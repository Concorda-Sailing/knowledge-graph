"""Dunder-heavy class: descriptor protocol hooks, __slots__, property pair."""


class DescriptorMixin:
    """Uses descriptor protocol dunders + property getter/setter pair."""

    __slots__ = ["_value", "_name"]

    def __init_subclass__(cls, **kwargs):
        """Called when a class is subclassed from this one."""
        super().__init_subclass__(**kwargs)

    def __set_name__(cls, owner, name):
        """Called by type.__new__ when a descriptor is assigned as a class attr."""
        cls._name = name

    def __class_getitem__(cls, item):
        """Makes cls[item] work without a metaclass."""
        return item

    @property
    def value(self):
        """Getter half of the property pair."""
        return self._value

    @value.setter
    def value(self, new_val):
        """Setter half — emits same id as getter (v0 pinned behavior)."""
        self._value = new_val
