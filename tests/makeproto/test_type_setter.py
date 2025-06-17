import unittest
from typing import Dict, List, Union

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.setters.type import TypeSetter
from grpcAPI.types import (
    NO_PACKAGE,
    BaseEnum,
    BaseMessage,
    Bool,
    Bytes,
    Int32,
    Stream,
    String,
)
from tests.makeproto.test_helpers import (
    make_enum_block,
    make_enumfield,
    make_field,
    make_message_block,
    make_method,
)


class Enum1(BaseEnum):
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

    def test_field_list(self) -> None:
        make_field("field1", block=self.block, ftype=List[int])
        make_field("field2", block=self.block, ftype=List[Int32])
        make_field("field3", block=self.block, ftype=List[Enum1])
        self.setter.execute([self.block], self.context)
        render_dict = self.block.get_render_dict()
        self.assertEqual(
            [field["ftype"] for field in render_dict["fields"]],
            ["repeated int64", "repeated int32", "repeated foo.bar"],
        )

    def test_field_dict(self) -> None:
        make_field("field1", block=self.block, ftype=Dict[str, int])
        make_field("field2", block=self.block, ftype=Dict[int, Int32])
        make_field("field3", block=self.block, ftype=Dict[bool, Enum1])
        self.setter.execute([self.block], self.context)
        render_dict = self.block.get_render_dict()
        self.assertEqual(
            [field["ftype"] for field in render_dict["fields"]],
            ["map<string, int64>", "map<int64, int32>", "map<bool, foo.bar>"],
        )

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

        make_field("field1", block=self.block, ftype=Enum2)
        make_field("field2", block=self.block, ftype=Enum1)

        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        render_dicts = [field.render_dict for field in self.block.fields]
        types = [list(rdict.values())[0] for rdict in render_dicts]
        self.assertIn("hello.world", types)
        self.assertIn("foo.bar", types)

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

    def test_enum_block(self) -> None:
        enumblock = make_enum_block("enum1")
        make_enumfield("VALID", block=enumblock, number=0)
        make_enumfield("INVALID", block=enumblock, number=1)
        self.setter.execute([enumblock], self.context)
        render_dict = enumblock.get_render_dict()
        self.assertEqual(render_dict["fields"][0]["ftype"], "")
        self.assertEqual(render_dict["fields"][1]["ftype"], "")


if __name__ == "__main__":
    unittest.main()
