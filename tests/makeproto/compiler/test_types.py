import unittest

from grpcAPI.makeproto.compiler.compiler import CompilerContext
from grpcAPI.makeproto.compiler.passes.type import FieldTypeValidator
from grpcAPI.makeproto.protoobj.base import BaseProto
from grpcAPI.makeproto.protoobj.types import DEFAULT_PRIMITIVES
from tests.makeproto.compiler.test_helpers import make_block, make_field


# Dummy protobuf subclass para testes
class DummyProto(BaseProto):
    pass


class TestFieldTypeValidator(unittest.TestCase):
    def test_enum_field_with_type(self) -> None:
        block = make_block("MyEnum", block_type="enum")
        field = make_field("field1", block=block, ftype=int)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E620" for e in report.errors))

    def test_enum_field_without_type(self) -> None:
        block = make_block("MyEnum", block_type="enum")
        field = make_field("field1", block=block, ftype=None)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)

    def test_field_no_type(self) -> None:
        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=None)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))
        self.assertIn("no type annotation", report.errors[0].message.lower())

    def test_field_valid_primitive_type(self) -> None:
        block = make_block("MyMessage")
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
        for prim in DEFAULT_PRIMITIVES:
            field = make_field("field1", block=block, ftype=prim)
            field.block = block
            block.fields = [field]
            validator.execute([block], context)
            report = context.get_report(block.name)
            self.assertEqual(len(report.errors), 0, f"Primitive {prim} should be valid")

    def test_field_invalid_type(self) -> None:
        class NotAllowed:
            pass

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=NotAllowed)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
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
        validator = FieldTypeValidator()
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
        validator = FieldTypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))

    def test_field_dict_with_valid_key_and_value(self) -> None:
        from typing import Dict

        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=Dict[str, int])
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
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
        validator = FieldTypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any(e.code == "E621" for e in report.errors))
        self.assertIn("not allowed key type", report.errors[0].message.lower())

    def test_field_protobuf_type(self) -> None:
        block = make_block("MyMessage")
        field = make_field("field1", block=block, ftype=DummyProto)
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = FieldTypeValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertEqual(len(report.errors), 0)


if __name__ == "__main__":
    unittest.main()
