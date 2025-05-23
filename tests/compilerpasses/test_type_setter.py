import unittest
from enum import Enum
from typing import Union

from grpcAPI.makeproto.compiler import CompilerContext, TypeSetter
from grpcAPI.makeproto.compiler.compiler import list_ctx_error_code
from grpcAPI.types import NO_PACKAGE, BaseMessage, Bool, Bytes, Int32, Stream, String
from tests.compilerpasses.test_helpers import (
    make_enumfield,
    make_field,
    make_message_block,
    make_method,
)


class Enum1(Enum):
    @classmethod
    def prototype(cls) -> str:
        return "bar"

    @classmethod
    def qualified_prototype(cls) -> str:
        return f"{cls.package()}.{cls.prototype()}"

    @classmethod
    def package(cls) -> str:
        return "foo"


class Enum2(Enum1):
    @classmethod
    def prototype(cls) -> str:
        return "world"

    @classmethod
    def package(cls) -> str:
        return "hello"


class Proto1(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "file1"

    @classmethod
    def package(cls) -> Union[str, object]:
        return NO_PACKAGE


class Proto2(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "file1"

    @classmethod
    def package(cls) -> Union[str, object]:
        return "test.package"


class Proto3(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "file1"

    @classmethod
    def package(cls) -> Union[str, object]:
        return "pack"


class WrongEnum(Enum):
    pass


class TestTypeSetter(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_message_block(
            "ValidBlock",
        )
        self.context = CompilerContext()
        self.setter = TypeSetter()

    def test_field_primary_types_ok(self) -> None:
        make_field("field1", block=self.block, ftype=int)
        make_field("field2", block=self.block, ftype=Int32)
        make_field("field3", block=self.block, ftype=String)
        make_field("field4", block=self.block, ftype=Bool)
        make_field("field5", block=self.block, ftype=Bytes)
        make_field("field6", block=self.block, ftype=bytes)
        make_field("field7", block=self.block, ftype=str)
        make_field("field8", block=self.block, ftype=bool)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_fields_w_pack(self) -> None:

        make_field("field1", block=self.block, ftype=Enum2)
        make_field("field2", block=self.block, ftype=Enum1)

        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields]
        types = [list(rdict.values())[0] for rdict in render_dicts]
        self.assertIn("hello.world", types)
        self.assertIn("foo.bar", types)

    def test_field_enum_types_ok(self) -> None:

        make_enumfield("field1", block=self.block)
        make_enumfield("field2", block=self.block)

        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields]
        types = [list(rdict.values())[0] for rdict in render_dicts]
        self.assertEqual(["", ""], types)

    def test_field_message_types_ok(self) -> None:
        make_field("field1", block=self.block, ftype=Proto1)
        make_field("field2", block=self.block, ftype=Proto2)
        make_field("field3", block=self.block, ftype=Proto3)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields]
        types = [list(rdict.values())[0] for rdict in render_dicts]
        self.assertIn("Proto1", types)
        self.assertIn("Proto2", types)
        self.assertIn("pack.Proto3", types)

    def test_field_enum_types_wrong(self) -> None:
        make_field("field1", block=self.block, ftype=WrongEnum)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        # validator should pick this error - no attribute 'prototype'
        self.assertTrue(any(msg == "E901" for msg in list_ctx_error_code(self.context)))

    def test_method_types_unary(self) -> None:
        make_method(
            "Method1",
            request_type=[Proto1],
            block=self.block,
            response_type=Proto1,
        )
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields][0]
        self.assertEqual(render_dicts["request_type"], "Proto1")
        self.assertEqual(render_dicts["request_stream"], False)
        self.assertEqual(render_dicts["response_type"], "Proto1")
        self.assertEqual(render_dicts["response_stream"], False)

    def test_method_types_client_stream(self) -> None:
        make_method(
            "Method1",
            request_type=[Stream[Proto1]],
            block=self.block,
            response_type=Proto1,
        )
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields][0]
        self.assertEqual(render_dicts["request_type"], "Proto1")
        self.assertEqual(render_dicts["request_stream"], True)
        self.assertEqual(render_dicts["response_type"], "Proto1")
        self.assertEqual(render_dicts["response_stream"], False)

    def test_method_types_server_stream(self) -> None:
        make_method(
            "Method1",
            request_type=[Proto1],
            block=self.block,
            response_type=Stream[Proto1],
        )
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields][0]
        self.assertEqual(render_dicts["request_type"], "Proto1")
        self.assertEqual(render_dicts["request_stream"], False)
        self.assertEqual(render_dicts["response_type"], "Proto1")
        self.assertEqual(render_dicts["response_stream"], True)

    def test_method_types_bidirectional_stream(self) -> None:
        make_method(
            "Method1",
            request_type=[Stream[Proto1]],
            block=self.block,
            response_type=Stream[Proto1],
        )
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields][0]
        self.assertEqual(render_dicts["request_type"], "Proto1")
        self.assertEqual(render_dicts["request_stream"], True)
        self.assertEqual(render_dicts["response_type"], "Proto1")
        self.assertEqual(render_dicts["response_stream"], True)


if __name__ == "__main__":
    unittest.main()
