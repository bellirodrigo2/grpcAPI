import unittest

from grpcAPI.makeproto.compiler import (
    BlockNameValidator,
    CompilerContext,
    FieldNameValidator,
)
from grpcAPI.makeproto.compiler.compiler import list_ctx_error_code
from tests.compiler.test_helpers import (
    make_enum_block,
    make_enumfield,
    make_field,
    make_message_block,
    make_oneof_block,
    make_oneof_field,
)


class TestBlockNameValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.validator = BlockNameValidator()
        self.context = CompilerContext()

    def test_valid_block_name(self) -> None:
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_invalid_block_name(self) -> None:
        block = make_message_block("1InvalidName")
        self.validator.execute([block], self.context)
        report = self.context.get_report(block.name)
        self.assertTrue(any("E101" == e.code for e in report.errors))

    def test_reserved_word_block_name(self) -> None:
        block = make_message_block("message")  # "message" é reservado
        self.validator.execute([block], self.context)
        self.assertTrue(all(msg == "E102" for msg in list_ctx_error_code(self.context)))

    def test_non_duplicated_block_name(self) -> None:
        block1 = make_message_block("Other1")
        block2 = make_message_block("Other3")
        self.validator.execute([self.block, block1, block2], self.context)
        self.assertEqual(len(self.context), 0)

    def test_duplicated_block_name(self) -> None:
        block1 = make_message_block("Other1")
        block2 = make_message_block("Other1")
        self.validator.execute([self.block, block1, block2], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))

    def test_2duplicated_block_name(self) -> None:
        block1 = make_message_block("Other1")
        block2 = make_message_block("Other1")
        block3 = make_message_block("Other1")
        self.validator.execute([self.block, block1, block2, block3], self.context)
        self.assertEqual(len(self.context), 2)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))

    def test_oneof_name_ok(self) -> None:
        make_oneof_block("OO1", block=self.block)
        make_oneof_block("OO2", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_duplicated_oneof_repeat_message(self) -> None:
        make_oneof_block("ValidBlock", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))

    def test_duplicated_oneof_name_(self) -> None:
        make_oneof_block("OO1", block=self.block)
        make_oneof_block("OO1", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))


class TestFieldNameValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.name = "ValidBlock"
        self.block = make_message_block(self.name)
        self.context = CompilerContext()
        self.validator = FieldNameValidator()

    def test_valid_field_name(self) -> None:
        make_field("field1", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_invalid_field_name(self) -> None:
        make_field("1InvalidName", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E101" for msg in list_ctx_error_code(self.context)))

    def test_field_reserved_name(self) -> None:
        rw = "reservedName"
        make_field(rw, block=self.block)
        self.block.reserveds = [rw]
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E103" for msg in list_ctx_error_code(self.context)))

    def test_duplicated_field_name(self) -> None:
        make_field("field1", block=self.block)
        make_field("field1", block=self.block)
        make_field("field1", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))
        self.assertEqual(len(self.context), 2)

    def test_oneof_name(self) -> None:
        make_field("field1", block=self.block)
        make_field("field2")
        oneofblock = make_oneof_block("oo", block=self.block)
        make_oneof_field("oo1", block=oneofblock)
        make_oneof_field("oo2", block=oneofblock)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_dup_fail_oneof_name_field(self) -> None:
        make_field("field1", block=self.block)
        make_field("field2", block=self.block)
        oneofblock = make_oneof_block("oo", block=self.block)
        make_oneof_field("field1", block=oneofblock)
        make_oneof_field("field2", block=oneofblock)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 2)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))

    def test_dup_fail_oneof_name(self) -> None:
        make_field("field1", block=self.block)
        make_oneof_block("field1", block=self.block)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)

    def test_dup_ok_oneof_internal_name(self) -> None:
        make_field("field1", block=self.block)
        ooblock = make_oneof_block("oo1", block=self.block)
        make_oneof_field("field1", block=ooblock)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)

    def test_enum_ok(self) -> None:
        block = make_enum_block("enum1")
        make_enumfield("f1", block=block)
        self.validator.execute([block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_enum_ok_same_field(self) -> None:
        block = make_enum_block("enum1")
        make_enumfield("enum1", block=block)
        self.validator.execute([block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_enum_duplicated(self) -> None:
        block = make_enum_block("enum1")
        make_enumfield("enum11", block=block)
        make_enumfield("enum11", block=block)
        self.validator.execute([block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E104" for msg in list_ctx_error_code(self.context)))


if __name__ == "__main__":
    unittest.main()
