import unittest
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional, Union

from typemapping.typemapping import NO_DEFAULT, map_class_fields, map_func_args

# --- Classes auxiliares para metadados em Annotated ---


@dataclass(frozen=True)
class Meta1:
    pass


@dataclass(frozen=True)
class Meta2:
    pass


# --- Definições de classes usadas nos testes --- #

# Dataclasses


@dataclass
class SimpleDefault:
    x: int = 10


@dataclass
class WithDefaultFactory:
    y: List[int] = field(default_factory=list)


@dataclass
class NoDefault:
    z: str


@dataclass
class AnnotatedSingle:
    a: Annotated[int, Meta1()] = 5


@dataclass
class AnnotatedMultiple:
    b: Annotated[str, Meta1(), Meta2()] = "hello"


@dataclass
class OptionalNoDefault:
    c: Optional[int]


@dataclass
class OptionalDefaultNone:
    d: Optional[int] = None


@dataclass
class AnnotatedOptional:
    e: Annotated[Optional[str], Meta1()] = None


@dataclass
class WithUnion:
    f: Union[int, str] = 42


# Classes com __init__


class ClassSimpleDefault:
    def __init__(self, x: int = 10):
        self.x = x


class ClassAnnotatedMultiple:
    def __init__(self, b: Annotated[str, Meta1(), Meta2()] = "hello"):
        self.b = b


class ClassOptionalNoDefault:
    def __init__(self, c: Optional[int]):
        self.c = c


class ClassWithUnion:
    def __init__(self, f: Union[int, str] = 42):
        self.f = f


class ClassAnnotatedOptional:
    def __init__(self, e: Annotated[Optional[str], Meta1()] = None):
        self.e = e


# Classes só com annotations (sem init nem dataclass)


class OnlyClassSimple:
    x: int = 10


class OnlyClassAnnotated:
    a: Annotated[int, Meta1()] = 5


class OnlyClassAnnotatedMultiple:
    b: Annotated[str, Meta1(), Meta2()] = "hello"


class OnlyClassOptional:
    c: Optional[int]


class OnlyClassOptionalDefaultNone:
    d: Optional[int] = None


class OnlyClassAnnotatedOptional:
    e: Annotated[Optional[str], Meta1()] = None


class OnlyClassUnion:
    f: Union[int, str] = 42


class OnlyClassNoDefault:
    g: str


# --- Testes para map_class_fields (mapclass) --- #


class TestMapClassFields(unittest.TestCase):
    def check_fields(self, cls, expected):
        result = map_class_fields(cls)
        self.assertEqual(len(result), len(expected))
        for res, exp in zip(result, expected):
            name, argtype, basetype, default, has_default, extras = exp
            with self.subTest(field=name):
                self.assertEqual(res.name, name)
                self.assertEqual(res.argtype, argtype)
                self.assertEqual(res.basetype, basetype)
                self.assertEqual(res.default, default)
                self.assertEqual(res.has_default, has_default)
                self.assertEqual(res.extras, extras)

    def test_dataclass_cases(self) -> None:
        cases = [
            (SimpleDefault, [("x", int, int, 10, True, None)]),
            (WithDefaultFactory, [("y", List[int], List[int], list, True, None)]),
            (NoDefault, [("z", str, str, NO_DEFAULT, False, None)]),
            (
                AnnotatedSingle,
                [("a", Annotated[int, Meta1()], int, 5, True, (Meta1(),))],
            ),
            (
                AnnotatedMultiple,
                [
                    (
                        "b",
                        Annotated[str, Meta1(), Meta2()],
                        str,
                        "hello",
                        True,
                        (Meta1(), Meta2()),
                    )
                ],
            ),
            (
                OptionalNoDefault,
                [("c", Optional[int], Optional[int], NO_DEFAULT, False, None)],
            ),
            (
                OptionalDefaultNone,
                [("d", Optional[int], Optional[int], None, True, None)],
            ),
            (
                AnnotatedOptional,
                [
                    (
                        "e",
                        Annotated[Optional[str], Meta1()],
                        Optional[str],
                        None,
                        True,
                        (Meta1(),),
                    )
                ],
            ),
            (WithUnion, [("f", Union[int, str], Union[int, str], 42, True, None)]),
        ]
        for cls, expected in cases:
            with self.subTest(cls=cls):
                self.check_fields(cls, expected)

    def test_class_init_cases(self) -> None:
        cases = [
            (ClassSimpleDefault, [("x", int, int, 10, True, None)]),
            (
                ClassAnnotatedMultiple,
                [
                    (
                        "b",
                        Annotated[str, Meta1(), Meta2()],
                        str,
                        "hello",
                        True,
                        (Meta1(), Meta2()),
                    )
                ],
            ),
            (
                ClassOptionalNoDefault,
                [("c", Optional[int], Optional[int], NO_DEFAULT, False, None)],
            ),
            (ClassWithUnion, [("f", Union[int, str], Union[int, str], 42, True, None)]),
            (
                ClassAnnotatedOptional,
                [
                    (
                        "e",
                        Annotated[Optional[str], Meta1()],
                        Optional[str],
                        None,
                        True,
                        (Meta1(),),
                    )
                ],
            ),
        ]
        for cls, expected in cases:
            with self.subTest(cls=cls):
                self.check_fields(cls, expected)

    def test_class_fields_simple_annotations(self) -> None:
        cases = [
            (OnlyClassSimple, [("x", int, int, 10, True, None)]),
            (
                OnlyClassAnnotated,
                [("a", Annotated[int, Meta1()], int, 5, True, (Meta1(),))],
            ),
            (
                OnlyClassAnnotatedMultiple,
                [
                    (
                        "b",
                        Annotated[str, Meta1(), Meta2()],
                        str,
                        "hello",
                        True,
                        (Meta1(), Meta2()),
                    )
                ],
            ),
            (
                OnlyClassOptional,
                [("c", Optional[int], Optional[int], NO_DEFAULT, False, None)],
            ),
            (
                OnlyClassOptionalDefaultNone,
                [("d", Optional[int], Optional[int], None, True, None)],
            ),
            (
                OnlyClassAnnotatedOptional,
                [
                    (
                        "e",
                        Annotated[Optional[str], Meta1()],
                        Optional[str],
                        None,
                        True,
                        (Meta1(),),
                    )
                ],
            ),
            (OnlyClassUnion, [("f", Union[int, str], Union[int, str], 42, True, None)]),
            (OnlyClassNoDefault, [("g", str, str, NO_DEFAULT, False, None)]),
        ]
        for cls, expected in cases:
            with self.subTest(cls=cls):
                self.check_fields(cls, expected)

    def test_nested_dataclass(self) -> None:
        @dataclass
        class Base:
            frombase: str

        @dataclass
        class Derived1(Base):
            fromder1: int

        @dataclass
        class Derived2(Derived1):
            fromder2: List[int]

        base_map = map_class_fields(Base)
        self.assertEqual(len(base_map), 1)
        self.assertEqual(base_map[0].name, "frombase")

        der1_map = map_class_fields(Derived1)
        self.assertEqual(len(der1_map), 2)
        self.assertEqual(der1_map[0].name, "frombase")
        self.assertEqual(der1_map[1].name, "fromder1")

        der2_map = map_class_fields(Derived2)
        self.assertEqual(len(der2_map), 3)
        self.assertEqual(der2_map[0].name, "frombase")
        self.assertEqual(der2_map[1].name, "fromder1")
        self.assertEqual(der2_map[2].name, "fromder2")

    def test_nested_class(self) -> None:
        class Base:
            def __init__(self, frombase: str):
                self.frombase = frombase

        class Derived1(Base):
            def __init__(self, frombase: str, fromder1: int):
                self.fromder1 = fromder1
                super().__init__(frombase)

        class Derived2(Derived1):
            def __init__(self, frombase: str, fromder1: int, fromder2: List[int]):
                self.fromder2 = fromder2
                super().__init__(frombase, fromder1)

        base_map = map_class_fields(Base)
        self.assertEqual(len(base_map), 1)
        self.assertEqual(base_map[0].name, "frombase")

        der1_map = map_class_fields(Derived1)
        self.assertEqual(len(der1_map), 2)
        self.assertEqual(der1_map[0].name, "frombase")
        self.assertEqual(der1_map[1].name, "fromder1")

        der2_map = map_class_fields(Derived2)
        self.assertEqual(len(der2_map), 3)
        self.assertEqual(der2_map[0].name, "frombase")
        self.assertEqual(der2_map[1].name, "fromder1")
        self.assertEqual(der2_map[2].name, "fromder2")

    def test_special_method(self) -> None:
        class Special:
            @classmethod
            def test(cls) -> str:
                return "foobar"

        mapped = map_class_fields(Special)
        self.assertFalse(mapped)


# --- Testes básicos para map_class_fields e map_func_args (mapclass e mapfunc) --- #


class TestBasicMappings(unittest.TestCase):
    def test_plain_class_with_annotations(self) -> None:
        class Model:
            fa: int
            fb: str = "default"
            fc: Optional[float]

        fields = map_class_fields(Model)
        names = [f.name for f in fields]
        self.assertIn("fa", names)
        self.assertIn("fb", names)
        self.assertIn("fc", names)


def test_function_args(self) -> None:
    def foo(x: int, y: str = "abc", z: Any = None) -> None:
        pass

    args = map_func_args(foo)
    self.assertEqual(len(args), 2)  # mudar de 3 para 2
    self.assertEqual(args[0].name, "x")
    self.assertEqual(args[1].default, "abc")


if __name__ == "__main__":
    unittest.main()
