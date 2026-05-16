"""Metaclass patterns: ABCMeta keyword arg, type subclass, dynamic __new__."""
from abc import ABCMeta, abstractmethod


class AbstractBase(metaclass=ABCMeta):
    """Class using metaclass= keyword syntax."""

    @abstractmethod
    def run(self) -> None: ...

    @abstractmethod
    def status(self) -> str: ...


class TypeSubclass(type):
    """A metaclass that itself subclasses type."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        return super().__new__(mcs, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)


class ConcreteWithMeta(AbstractBase):
    """Uses the metaclass indirectly through inheritance."""

    def run(self) -> None:
        pass

    def status(self) -> str:
        return "ok"
