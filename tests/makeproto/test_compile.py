import unittest
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, Dict, List, Set, Union

from grpcAPI.types import BaseMessage
from grpcAPI.types.base import Metadata, OneOf, ProtoOption
from grpcAPI.types.interfaces import IMethod, IModule, IService
from grpcAPI.types.message import BaseEnum, _NoPackage


class Proto1(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "proto1"

    @classmethod
    def package(cls) -> str:
        return "pack1"


class Hello(Proto1):
    a: Annotated[str, OneOf(key="choice")]
    aa: Annotated[int, OneOf(key="choice")]
    d: str
    e: int
    j: List[str]
    m: Dict[int, bytes] = Metadata(description='Comment for "m"')
    y: int = OneOf(key="outro")
    zzz: str = OneOf(key="outro")


def method1(req: Hello) -> Hello:
    return


@dataclass
class TesteMethod:
    method: Callable[..., Any]


testemethod = TesteMethod(method=method1)


@dataclass
class TesteService:
    methods: List[IMethod]
    name: str = "service1"
    module: str = "proto1"
    package: Union[str, _NoPackage] = "pack1"


testeservice = TesteService(methods=[testemethod])


@dataclass
class TestModule(IModule):
    name: str = "proto1"
    package: Union[_NoPackage, str] = "pack1"

    @property
    def services(self) -> List[IService]:
        return [testeservice]

    @property
    def objects(self) -> Set[type[Union[BaseMessage, BaseEnum]]]:
        return set([Hello])


testemodule = TestModule()


@dataclass
class TestePackage:
    name = "pack1"

    @property
    def modules(self) -> List[IModule]:
        return [testemodule]


pack = TestePackage()


class TestBlockNameValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.packages = [pack]

    def test_compiler_basic(self) -> None:
        print(self.packages[0])
