import unittest
from enum import Enum
from typing import Annotated, Dict, List, Optional, Union

from grpcAPI.app import MethodPack, ServicePack
from grpcAPI.makeproto.makeblock import (
    make_enumblock,
    make_method,
    make_msgblock,
    make_service,
)
from grpcAPI.makeproto.protoblock import Method, OneOfBlock
from grpcAPI.types import BaseMessage, Metadata, OneOf, ProtoOption


class Proto1(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "proto"

    @classmethod
    def package(cls) -> str:
        return "pack1"


class MyEnum(Proto1, Enum):
    VALID = 0
    INVALID = 1


class Enum2(Proto1, Enum):
    FOO = 0
    BAR = 1


class Hello(Proto1):
    @classmethod
    def description(cls) -> str:
        return "Hello Comment"

    @classmethod
    def options(cls) -> ProtoOption:
        return {"foo": "bar"}

    a: Annotated[str, OneOf(key="choice")]
    aa: Annotated[int, OneOf(key="choice")]
    bb: Annotated[str, OneOf(key="choice")]
    b: Annotated[bytes, 123, "helloworld", OneOf(key="choice")]
    c: str
    d: str
    e: int
    f: Annotated[int, Metadata(options={"deprecated": True, "json_name": "f_alias"})]
    g: MyEnum
    h: Annotated[Enum2, "helloworld"]
    i: Annotated[int, 1234]
    j: List[str]
    k: Annotated[
        List[bool], 1, Metadata(options={"deprecated": True, "json_name": "k_alias"})
    ]
    li: Dict[str, MyEnum]
    m: Dict[int, bytes] = Metadata(description='Comment for "m"')
    y: int = OneOf(key="outro")
    z: bool = OneOf(key="outro")
    zz: str = OneOf(key="outro")
    zzz: str = OneOf(key="outro")


class Fail(Proto1):
    a: Annotated[str, OneOf(key=3)]
    b: Annotated[str, 123]
    c: Annotated[str, Metadata(index=-1)]
    d: Annotated[bytes, 123, "helloworld", OneOf(key="choice", index="4")]
    e: Optional[str]
    f: Dict[bytes, str]
    g: List[str]
    h: Dict[int, Union[str, int]]
    i: int = Metadata(description=[], index=45)
    j: str = Metadata(options={3: "bar"}, index=45)
    k: str = Metadata(options={"3": 3})
    lee: str = Metadata(options=[1])


class Base(Proto1):
    @classmethod
    def description(cls) -> str:
        return "Base Comment"

    @classmethod
    def options(cls) -> ProtoOption:
        return {"base": "foo"}

    b1: Annotated[str, OneOf(key="choice")]
    b2: Annotated[int, OneOf(key="choice")]


class Derived1(Base):
    @classmethod
    def description(cls) -> str:
        return "Derived1 Comment"

    @classmethod
    def options(cls) -> ProtoOption:
        return {"der1": "base"}

    fromder1: int


class Derived2(Derived1):
    @classmethod
    def description(cls) -> str:
        return "Derived2 Comment"

    @classmethod
    def options(cls) -> ProtoOption:
        return {}

    fromder2: bool


class TestMakeBlocks(unittest.TestCase):

    def test_make_msgblock_ok(self) -> None:
        block = make_msgblock(Hello)
        self.assertEqual(block.name, "Hello")
        self.assertEqual(block.description, "Hello Comment")
        self.assertEqual(block.options["foo"], "bar")
        oneofs = [f for f in block.fields if isinstance(f, OneOfBlock)]
        self.assertEqual(len(oneofs), 2)
        self.assertTrue(all(len(f.fields) == 4 for f in oneofs))

    def test_make_msgblock_fail(self) -> None:
        block = make_msgblock(Fail)
        self.assertEqual(block.name, "Fail")
        self.assertTrue(len(block.fields) >= 10)

    def test_make_msgblock_inheritance(self) -> None:
        base_block = make_msgblock(Base)
        self.assertEqual(base_block.name, "Base")
        self.assertEqual(base_block.description, "Base Comment")
        self.assertEqual(base_block.options["base"], "foo")
        base_oneofs = [f for f in base_block.fields if isinstance(f, OneOfBlock)]
        self.assertEqual(len(base_oneofs), 1)
        self.assertEqual(len(base_oneofs[0].fields), 2)
        self.assertEqual(base_oneofs[0].name, "choice")

        der1_block = make_msgblock(Derived1)
        self.assertEqual(der1_block.description, "Derived1 Comment")
        self.assertEqual(der1_block.options["der1"], "base")
        self.assertTrue(any(f.name == "fromder1" for f in der1_block.fields))

        der2_block = make_msgblock(Derived2)
        self.assertEqual(der2_block.description, "Derived2 Comment")
        self.assertEqual(der2_block.options, {})
        self.assertTrue(any(f.name == "fromder2" for f in der2_block.fields))

    def test_make_enumblock(self) -> None:
        enum_block = make_enumblock(MyEnum)
        self.assertEqual(enum_block.name, "MyEnum")
        names = {f.name for f in enum_block.fields}
        self.assertEqual(names, {"VALID", "INVALID"})

    def test_make_enumblock_2(self) -> None:
        enum_block = make_enumblock(Enum2)
        self.assertEqual(enum_block.name, "Enum2")
        names = {f.name for f in enum_block.fields}
        self.assertEqual(names, {"FOO", "BAR"})


class ReqMessage(BaseMessage):
    a: int
    b: Annotated[str, Metadata(description="Campo b")]


class ResMessage(BaseMessage):
    x: int
    y: str


class AnotherReq(BaseMessage):
    p: float
    q: Annotated[List[int], Metadata(description="lista q")]


def my_method(
    req: Annotated[ReqMessage, Metadata(description="request metadata")],
) -> ResMessage: ...


def another_method(req: AnotherReq, extra: str) -> ResMessage: ...


def simple_method(req: ReqMessage) -> ResMessage: ...


def ignored_method(req: ReqMessage) -> ResMessage: ...


class TestMakeMethodService(unittest.TestCase):

    def test_make_method_basic(self) -> None:
        method = make_method(my_method)
        self.assertEqual(method.name, "my_method")
        self.assertEqual(method.response_type, ResMessage)
        self.assertEqual(len(method.request_type), 1)
        self.assertEqual(method.request_type[0], ReqMessage)
        self.assertIs(method.method_func, my_method)

    def test_make_method_multiple_args(self) -> None:
        method = make_method(
            another_method,
        )
        self.assertEqual(method.name, "another_method")
        self.assertEqual(len(method.request_type), 2)
        self.assertIn(AnotherReq, method.request_type)
        self.assertIn(str, method.request_type)

    def test_make_service_basic(self) -> None:
        my_method_p = MethodPack(my_method, "", {})
        another_method_p = MethodPack(another_method, "", {})
        ignored_method_p = MethodPack(ignored_method, "", {})
        methods = [my_method_p, another_method_p, ignored_method_p]
        pack = ServicePack(
            name="TestService",
            description="Test service",
            options={"deprecated": False},
            module="test.proto",
            package="testpkg",
            methods=methods,
        )
        service = make_service(pack)

        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.protofile, "test.proto")
        self.assertEqual(service.package, "testpkg")
        self.assertEqual(service.description, "Test service")
        self.assertEqual(service.options["deprecated"], False)
        self.assertEqual(len(service.fields), len(methods))

        for method in service.fields:
            self.assertIsInstance(method, Method)
            self.assertIs(method.block, service)
            self.assertTrue(callable(method.method_func))
            if method.name == "ignored_method":
                self.assertEqual(len(method.request_type), 1)

    def test_make_service_empty(self) -> None:
        pack = ServicePack(
            name="EmptyService",
            description="Empty service",
            options={},
            module="empty.proto",
            package="emptypkg",
            methods=[],
        )
        service = make_service(pack)
        self.assertEqual(service.name, "EmptyService")
        self.assertEqual(len(service.fields), 0)


if __name__ == "__main__":
    unittest.main()
