import pytest
from typing_extensions import Any

from grpcAPI.singleton import SingletonMeta


class SingletonExample(metaclass=SingletonMeta):
    def __init__(self, value: Any) -> None:
        self.value = value


def test_singleton_instance_is_same() -> None:
    a = SingletonExample(123)
    b = SingletonExample(456)

    # Deve ser a mesma instância
    assert a is b
    # O valor permanece o do primeiro
    assert a.value == 123
    assert b.value == 123


def test_singleton_reset_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    # monkeypatch a dict para simular limpeza
    SingletonMeta._instances = {}  # reset manual
    SingletonExample("foo")
    SingletonMeta._instances = {}  # forçar limpeza (simula reinício da app)

    class AnotherSingleton(metaclass=SingletonMeta):
        def __init__(self):
            self.x = 42

    b = AnotherSingleton()
    c = AnotherSingleton()

    assert b is c
    assert b.x == 42
