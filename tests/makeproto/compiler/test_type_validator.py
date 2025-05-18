import unittest
from enum import Enum
from pathlib import Path

from grpcAPI.makeproto.compiler import TypeValidator
from grpcAPI.makeproto.compiler.compiler import CompilerContext
from grpcAPI.types import DEFAULT_PRIMITIVES, BaseMessage, BaseProto
from grpcAPI.types.method import Stream
from tests.makeproto.compiler.test_helpers import make_block, make_field, make_method


# Dummy protobuf subclass para testes
class DummyProto(BaseProto):
    pass


async def agen():  # type: ignore
    yield "hello"


def not_async():  # type: ignore
    yield "hello"


async def not_gen():  # type: ignore
    return "hello"


class TestTypeValidator(unittest.TestCase):
    def test_enum_field_with_type(self) -> None:
        block = make_block("MyEnum", block_type="enum")
        field = make_field("field1", block=block, ftype=int)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E620" for e in report.errors))

    def test_enum_field_without_type(self) -> None:
        block = make_block("MyEnum", block_type="enum")
        field = make_field("field1", block=block, ftype=None)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_field_no_type(self) -> None:
        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=None)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))
        self.assertIn("no type annotation", report.errors[0].message.lower())

    def test_field_valid_primitive_type(self) -> None:
        block = make_block("MyMessage")
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        for prim in DEFAULT_PRIMITIVES:
            field = make_field("field1", block=block, ftype=prim)
            field.block = block
            block.fields = [field]
            validator.execute([block], context)
            report = context.get_report(block.name)
            self.assertEqual(len(report.errors), 0, f"Primitive {prim} should be valid")

    def test_field_labeled_enum_type(self) -> None:
        class MyEnum(Enum):
            @classmethod
            def protofile(cls) -> str:
                return "foo"

            @classmethod
            def package(cls) -> str:
                return "bar"

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=MyEnum)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_field_non_labeled_enum_type(self) -> None:
        class WrongEnum(Enum):
            pass

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=WrongEnum)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 1)
        self.assertTrue(any(e.code == "E621" for e in report.errors))

    def test_field_non_callable_enum_type(self) -> None:
        class WrongEnum(Enum):
            protofile = "hello"
            package = 1

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=WrongEnum)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 1)
        self.assertTrue(any(e.code == "E621" for e in report.errors))

    def test_field_invalid_type(self) -> None:
        class NotAllowed:
            pass

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=NotAllowed)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))
        self.assertIn("not allowed", report.errors[0].message.lower())

    def test_field_list_of_valid_type(self) -> None:
        from typing import List

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=List[int])
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_field_list_of_invalid_type(self) -> None:
        from typing import List

        class NotAllowed:
            pass

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=List[NotAllowed])
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))

    def test_field_dict_with_valid_key_and_value(self) -> None:
        from typing import Dict

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=Dict[str, int])
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_field_dict_with_invalid_key(self) -> None:
        from typing import Dict

        class NotAllowedKey:
            pass

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=Dict[NotAllowedKey, int])
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))
        self.assertIn("not allowed key type", report.errors[0].message.lower())

    def test_field_protobuf_type(self) -> None:
        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=DummyProto)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_method_ok_req(self) -> None:

        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[BaseMessage],
            block=block,
            response_type=BaseMessage,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_method_ok_stream_req(self) -> None:

        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[Stream[BaseMessage]],
            block=block,
            response_type=Stream[BaseMessage],
            method_func=agen,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_method_empty_req(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1", request_type=[], block=block, response_type=BaseMessage
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E802" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_invalid_req(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[str],
            block=block,
            response_type=BaseMessage,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E801" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_invalid_req_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[str],
            block=block,
            response_type=int,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E801" for e in report.errors))
        self.assertTrue(any(e.code == "E804" for e in report.errors))
        self.assertEqual(len(report.errors), 2)

    def test_method_many_req(self) -> None:
        class Proto2(BaseMessage): ...

        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[BaseMessage, Proto2],
            block=block,
            response_type=Proto2,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E803" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_extra(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[BaseMessage, Path, bool],
            block=block,
            response_type=Stream[BaseMessage],
            method_func=agen,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator([Path, bool])
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_method_empty_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1", request_type=[BaseMessage], block=block, response_type=None
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E804" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_none_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1", request_type=None, block=block, response_type=BaseMessage
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E801" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_invalid_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1", request_type=[BaseMessage], block=block, response_type=Path
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E804" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_none_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1", request_type=[BaseMessage], block=block, response_type=None
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E804" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_no_async_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[BaseMessage],
            block=block,
            response_type=Stream[BaseMessage],
            method_func=not_async,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E805" for e in report.errors))
        self.assertEqual(len(report.errors), 1)

    def test_method_no_gen_res(self) -> None:
        block = make_block("Service'", block_type="service")
        method = make_method(
            "Method1",
            request_type=[BaseMessage],
            block=block,
            response_type=Stream[BaseMessage],
            method_func=not_gen,
        )
        context = CompilerContext(blocks=[block])
        validator = TypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E805" for e in report.errors))
        self.assertEqual(len(report.errors), 1)


if __name__ == "__main__":
    unittest.main()
