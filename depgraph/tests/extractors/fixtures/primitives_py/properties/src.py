class Widget:
    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int) -> None:
        self._value = v

    @value.deleter
    def value(self) -> None:
        del self._value
