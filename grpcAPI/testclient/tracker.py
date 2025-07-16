import inspect
from unittest.mock import MagicMock

from typing_extensions import Any, Dict, Type


class Tracker:
    def __init__(self, interface_type: Type[Any]) -> None:
        self._methods: Dict[str, MagicMock] = {}

        for name, member in inspect.getmembers(
            interface_type, predicate=inspect.isfunction
        ):
            self._methods[name] = MagicMock(name=name)

    def reset_mock(self) -> None:
        for mock in self._methods.values():
            mock.reset_mock()

    def __getattr__(self, name: str) -> MagicMock:
        if name in self._methods:
            return self._methods[name]
        raise AttributeError(f"'Tracker' object has no attribute '{name}'")
