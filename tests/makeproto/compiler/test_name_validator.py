import unittest

from grpcAPI.makeproto.compiler.compiler import CompilerContext
from grpcAPI.makeproto.compiler.passes import NameValidator
from tests.makeproto.compiler.test_helpers import make_block, make_field, make_method


class TestNameValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_block("ValidBlock")
        self.context = CompilerContext(blocks=[self.block])
        self.validator = NameValidator()
        self.validator.execute([self.block], self.context)

    def test_valid_block_name(self) -> None:
        report = self.context.get_report("ValidBlock")
        self.assertEqual(len(report), 0)

    def test_invalid_block_name(self) -> None:
        block = make_block("1InvalidName")
        context = CompilerContext(blocks=[block])
        validator = NameValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any("E101" == e.code for e in report.errors))

    def test_reserved_word_block_name(self) -> None:
        block = make_block("message")  # "message" é reservado
        context = CompilerContext(blocks=[block])
        validator = NameValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any("E102" == e.code for e in report.errors))

    def test_field_reserved_name(self) -> None:
        field = make_field("reservedName")
        block = make_block(
            "BlockWithReserved", fields=[field], reserveds={"reservedName"}
        )
        field.block = block
        context = CompilerContext(blocks=[block])
        validator = NameValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any("E103" == e.code for e in report.errors))

    def test_duplicated_field_name(self) -> None:
        field1 = make_field("dupName")
        field2 = make_field("dupName")
        block = make_block("BlockWithDup", fields=[field1, field2])
        field1.block = block
        field2.block = block
        context = CompilerContext(blocks=[block])
        validator = NameValidator()
        validator.execute([block], context)
        report = context.get_report(block.name)
        self.assertTrue(any("E104" == e.code for e in report.errors))


if __name__ == "__main__":
    unittest.main()
