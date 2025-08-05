import pytest
from typing_extensions import Any

from grpcAPI.singleton import SingletonMeta


class SingletonExample(metaclass=SingletonMeta):
    def __init__(self, value: Any) -> None:
        self.value = value


@pytest.fixture(autouse=True)
def reset_singleton():
    """
    Fixture that cleans singleton state before each test.
    autouse=True ensures it runs automatically.
    """
    # Setup: clear before test
    SingletonMeta._instances.clear()
    if hasattr(SingletonMeta, "_lock"):
        # If there's a lock, ensure it's clean
        with SingletonMeta._lock:
            SingletonMeta._instances.clear()

    yield  # Run the test

    # Teardown: clear after test as well
    SingletonMeta._instances.clear()


def test_singleton_instance_is_same():
    """Tests if multiple calls return the same instance."""
    a = SingletonExample(123)
    b = SingletonExample(456)
    c = SingletonExample("ignored")

    # All should be the same instance
    assert a is b
    assert b is c
    assert a is c

    # Value remains from the first one (123)
    assert a.value == 123
    assert b.value == 123
    assert c.value == 123


def test_singleton_preserves_first_initialization():
    """Tests if only the first initialization is respected."""
    first = SingletonExample("first_value")
    second = SingletonExample("second_value")
    third = SingletonExample(999)

    assert first is second is third
    assert first.value == "first_value"
    assert second.value == "first_value"  # Didn't change
    assert third.value == "first_value"  # Didn't change


def test_singleton_different_classes_are_independent():
    """Tests if different classes have independent singletons."""

    class AnotherSingleton(metaclass=SingletonMeta):
        def __init__(self, name: str):
            self.name = name

    class ThirdSingleton(metaclass=SingletonMeta):
        def __init__(self, data: int):
            self.data = data

    # Each class has its own singleton
    example1 = SingletonExample("test")
    example2 = SingletonExample("ignored")

    another1 = AnotherSingleton("first")
    another2 = AnotherSingleton("ignored")

    third1 = ThirdSingleton(100)
    third2 = ThirdSingleton(200)

    # Same class = same instance
    assert example1 is example2
    assert another1 is another2
    assert third1 is third2

    # Different classes = different instances
    assert example1 is not another1
    assert another1 is not third1
    assert example1 is not third1

    # Values preserved from first init
    assert example1.value == "test"
    assert another1.name == "first"
    assert third1.data == 100


def test_singleton_with_no_args():
    """Tests singleton with classes that don't need arguments."""

    class NoArgsSingleton(metaclass=SingletonMeta):
        def __init__(self):
            self.created_count = getattr(self.__class__, "_count", 0) + 1
            self.__class__._count = self.created_count

    a = NoArgsSingleton()
    b = NoArgsSingleton()
    c = NoArgsSingleton()

    assert a is b is c
    assert a.created_count == 1  # __init__ called only once


def test_singleton_inheritance():
    """Tests behavior with inheritance."""

    class Parent(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value

    class Child(Parent):
        def __init__(self, value, extra):
            super().__init__(value)
            self.extra = extra

    # Parent and child are independent singletons
    parent1 = Parent("parent_value")
    parent2 = Parent("ignored")

    child1 = Child("child_value", "extra1")
    child2 = Child("ignored", "ignored")

    assert parent1 is parent2
    assert child1 is child2
    assert parent1 is not child1  # Different classes

    assert parent1.value == "parent_value"
    assert child1.value == "child_value"
    assert child1.extra == "extra1"


def test_singleton_thread_safety():
    """Tests basic thread safety (if implemented with lock)."""
    import threading
    import time

    results = []

    def create_singleton(value):
        # Simulate some delay in creation
        time.sleep(0.01)
        instance = SingletonExample(value)
        results.append(instance)

    # Create multiple threads trying to create singleton
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_singleton, args=(i,))
        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all to finish
    for thread in threads:
        thread.join()

    # All should be the same instance
    first_instance = results[0]
    for instance in results:
        assert instance is first_instance

    # Value should be from one of the first threads
    assert first_instance.value in range(5)


@pytest.mark.parametrize(
    "values",
    [
        [1, 2, 3],
        ["a", "b", "c"],
        [{"key": "value"}, {"ignored": "data"}],
        [None, "something", 42],
    ],
)
def test_singleton_with_different_value_types(values):
    """Tests singleton with different value types."""
    instances = [SingletonExample(value) for value in values]

    # All are the same instance
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first

    # Value remains the first one
    assert first.value == values[0]
