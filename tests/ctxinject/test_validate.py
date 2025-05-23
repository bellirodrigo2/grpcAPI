import unittest
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from grpcAPI.ctxinject.exceptions import (
    InvalidInjectableDefinition,
    InvalidModelFieldType,
    UnInjectableError,
)
from grpcAPI.ctxinject.model import (
    ArgsInjectable,
    ConstrArgInject,
    Depends,
    DependsInject,
    ModelFieldInject,
)
from grpcAPI.ctxinject.validate import (
    check_all_injectables,
    check_all_typed,
    check_depends_types,
    check_modefield_types,
    check_single_injectable,
    func_signature_validation,
)
from grpcAPI.mapclass import get_func_args


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
        check_all_typed(func1_args)
        with self.assertRaises(TypeError):
            check_all_typed(get_func_args(func2))

    def test_check_all_injectable(self) -> None:
        check_all_injectables(func1_args, [])

        def func2_inner(
            arg1: Annotated[UUID, 123, ConstrArgInject(...)],
            arg2: Annotated[datetime, ConstrArgInject(...)],
            arg3: Path,
            argn: datetime = ArgsInjectable(...),
            dep: Any = DependsInject(get_db),
        ) -> None:
            pass

        check_all_injectables(get_func_args(func2_inner), [Path])

        with self.assertRaises(UnInjectableError):
            check_all_injectables(get_func_args(func2_inner), [])

    def test_model_field_type_mismatch(self) -> None:
        class Model:
            x: int

        def func(y: Annotated[int, ModelFieldInject(model=Model)]) -> None:
            pass

        with self.assertRaises(InvalidModelFieldType):
            check_modefield_types(get_func_args(func))

    def test_invalid_modelfield(self) -> None:
        def func(a: Annotated[str, ModelFieldInject(model=123)]) -> str:
            return a

        with self.assertRaises(InvalidInjectableDefinition):
            check_modefield_types(get_func_args(func))

    def test_depends_type(self) -> None:
        # Check success case
        check_depends_types(func1_args)

        for f in [func3, func4, func5, func6]:
            with self.assertRaises(TypeError):
                check_depends_types(get_func_args(f))

    def test_multiple_injectables_error(self) -> None:
        class MyInject1(ArgsInjectable):
            pass

        class MyInject2(ArgsInjectable):
            pass

        def func(x: Annotated[str, MyInject1(...), MyInject2(...)]) -> None:
            pass

        with self.assertRaises(TypeError) as cm:
            check_single_injectable(get_func_args(func))
        self.assertIn("multiple injectables", str(cm.exception))

    def test_func_signature_validation_success(self) -> None:
        def valid_func(
            arg1: Annotated[UUID, 123, ConstrArgInject(...)],
            arg2: Annotated[datetime, ConstrArgInject(...)],
            arg3: str = ConstrArgInject(..., min_length=3),
            arg4: MyEnum = ConstrArgInject(...),
            arg5: list[str] = ConstrArgInject(..., max_length=5),
        ) -> None:
            return None

        # Should pass without exception
        func_signature_validation(valid_func, [])

    def test_func_signature_validation_untyped(self) -> None:
        def untyped_func(arg1, arg2: int) -> None:
            pass

        with self.assertRaises(TypeError):
            func_signature_validation(untyped_func, [])

    def test_func_signature_validation_uninjectable(self) -> None:
        def uninjectable_func(arg1: Path) -> None:
            pass

        with self.assertRaises(UnInjectableError):
            func_signature_validation(uninjectable_func, [])

    def test_func_signature_validation_invalid_model(self) -> None:
        def invalid_model_field_func(
            arg: Annotated[str, ModelFieldInject(model=123)],
        ) -> None:
            pass

        with self.assertRaises(InvalidInjectableDefinition):
            func_signature_validation(invalid_model_field_func, [])

    def test_func_signature_validation_bad_depends(self) -> None:
        def get_dep():
            return "value"

        def bad_dep_func(arg: Annotated[str, Depends(get_dep)]) -> None:
            pass

        with self.assertRaises(TypeError):
            func_signature_validation(bad_dep_func, [])

    def test_func_signature_validation_conflicting_injectables(self) -> None:
        def bad_multiple_inject_func(
            arg: Annotated[str, ConstrArgInject(...), ModelFieldInject(model=str)],
        ) -> None:
            pass

        with self.assertRaises(Exception):  # Ajuste conforme exceção real, se souber
            func_signature_validation(bad_multiple_inject_func, [])


if __name__ == "__main__":
    unittest.main()
