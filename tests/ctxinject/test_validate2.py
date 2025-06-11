import unittest
from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from grpcAPI.ctxinject.model import ConstrArgInject, Depends
from grpcAPI.ctxinject.validate2 import check_all_typed
from grpcAPI.typemapping import get_func_args


class MyEnum(Enum):
    VALID = 0
    INVALID = 1


def get_db() -> str:
    return "sqlite://"


def func1(
    arg1: Annotated[UUID, 123, ConstrArgInject(...)],
    arg2: Annotated[datetime, ConstrArgInject(...)],
    dep1: Annotated[str, Depends(get_db)],
    arg3: str = ConstrArgInject(..., min_length=3),
    arg4: MyEnum = ConstrArgInject(...),
    arg5: list[str] = ConstrArgInject(..., max_length=5),
    dep2: str = Depends(get_db),
) -> None:
    return None


func1_args = get_func_args(func1)


def func2(arg1: str, arg2) -> None:
    return None


def func3(arg1: Annotated[int, Depends(get_db)]) -> None:
    pass


def get_db2() -> None:
    pass


def func4(arg1: Annotated[str, Depends(get_db2)]) -> None:
    pass


def func5(arg: str = Depends(...)) -> str:
    return ""


def dep() -> int:
    pass


def func6(x: str = Depends(dep)) -> None:
    pass


class TestValidation(unittest.TestCase):

    def test_check_all_typed(self) -> None:
        errors = check_all_typed(func1_args)
        # with self.assertRaises(TypeError):
        # check_all_typed(get_func_args(func2))
