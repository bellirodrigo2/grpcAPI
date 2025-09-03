from typing import Iterable, List

from ctxinject import DependsInject, ModelFieldInject


class BaseClass:
    pass


class DerivedClass(BaseClass):
    pass


class MyClass:
    def __init__(self, list1: List[str]):
        self.list1 = list1


def get_class() -> DerivedClass:
    return DerivedClass()


def func(
    list1: Iterable[str] = ModelFieldInject(MyClass),
    db: BaseClass = DependsInject(get_class),
):
    pass


myclass = MyClass(list1=["a", "b", "c"])
ctx = {MyClass: myclass}
