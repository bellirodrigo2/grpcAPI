import unittest

from grpcAPI.makeproto.compiler import CompilerContext, IndexValidator
from grpcAPI.makeproto.compiler.compiler import (
    list_ctx_error_code,
    list_ctx_error_messages,
)
from tests.compiler.test_helpers import (
    make_enum_block,
    make_enumfield,
    make_field,
    make_message_block,
    make_method,
    make_oneof_block,
    make_service_block,
)


class TestIndexValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.validator = IndexValidator()
        self.context = CompilerContext()
        self.report = self.context.get_report(self.block.name)

    def test_field_index_ok(self) -> None:
        make_field("field1", block=self.block, number=1)
        make_field("field1", block=self.block, number=10)
        make_field("field1", block=self.block, number=200)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_index_oneof(self) -> None:
        make_field("field1", block=self.block, number=1)
        make_field("field1", block=self.block, number=10)
        make_field("field1", block=self.block, number=200)

        oneof_block = make_oneof_block(name="oo", block=self.block)
        make_field("oo1", block=oneof_block, number=400)
        make_field("oo1", block=oneof_block, number=500)

        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

        # self.assertTrue(all(msg == "E621" for msg in list_ctx_error_code(self.context)))

    def test_field_index_oneof_duplicated(self) -> None:
        make_field("field1", block=self.block, number=1)
        make_field("field1", block=self.block, number=10)
        make_field("field1", block=self.block, number=200)
        oneof_block = make_oneof_block(name="oo", block=self.block)
        make_field("oo1", block=oneof_block, number=400)
        make_field("oo1", block=oneof_block, number=10)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E202" for msg in list_ctx_error_code(self.context)))

    def test_field_index_not_int(self) -> None:
        make_field("field1", block=self.block, number="foo")  # type: ignore
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E201" for msg in list_ctx_error_code(self.context)))

    def test_field_index_none_ok(self) -> None:
        make_field("field1", block=self.block, number=None)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_index_duplicated(self) -> None:
        make_field("field1", block=self.block, number=1)
        make_field("field2", block=self.block, number=1)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E202" for msg in list_ctx_error_code(self.context)))
        self.assertIn(
            "Index is already used in the block",
            list_ctx_error_messages(self.context)[0],
        )

    def test_enum_index_duplicated(self) -> None:
        eblock = make_enum_block("enumb")
        make_enumfield("field1", block=eblock, number=0)
        make_enumfield("field2", block=eblock, number=0)
        self.validator.execute([eblock], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E202" for msg in list_ctx_error_code(self.context)))

    def test_enum_index_no_default(self) -> None:
        eblock = make_enum_block("enumb")
        make_enumfield("field1", block=eblock, number=1)
        make_enumfield("field2", block=eblock, number=3)
        self.validator.execute([eblock], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E205" for msg in list_ctx_error_code(self.context)))

    def test_field_index_reserved(self) -> None:
        make_field("field1", block=self.block, number=1)
        self.block.reserveds = [1]
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E204" for msg in list_ctx_error_code(self.context)))

    def test_field_index_reserved_range_min(self) -> None:
        make_field("field1", block=self.block, number=1)
        self.block.reserveds = [range(1, 5)]
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any("E204" == e.code for e in self.report.errors))
        self.assertIn("Reserved by block statement", self.report.errors[0].message)

    def test_field_index_reserved_range_max(self) -> None:
        make_field("field1", block=self.block, number=5)
        self.block.reserveds = [range(1, 5)]
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any("E204" == e.code for e in self.report.errors))
        self.assertIn("Reserved by block statement", self.report.errors[0].message)

    def test_field_index_zero(self) -> None:
        make_field("field1", block=self.block, number=0)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any("E203" == e.code for e in self.report.errors))

    def test_field_index_enum_zero(self) -> None:
        block_enum = make_enum_block(name="enumblock")
        make_enumfield("field1", block=block_enum, number=0)
        self.validator.execute([block_enum], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_index_reserved_protobuf(self) -> None:
        make_field("field1", block=self.block, number=19000)
        make_field("field1", block=self.block, number=19999)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 2)
        self.assertTrue(any("E204" == e.code for e in self.report.errors))
        self.assertIn("Reserved by protobuf", self.report.errors[0].message)
        self.assertIn("Reserved by protobuf", self.report.errors[1].message)

    def test_service_ok(self) -> None:
        serv = make_service_block("serv1")
        make_method("met", block=serv)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_enum_reserved(self) -> None:
        eblock = make_enum_block("e1")
        make_enumfield("field1", block=eblock, number=0)
        make_enumfield("field1", block=eblock, number=1)
        eblock.reserveds = [1]
        self.validator.execute([eblock], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E204" for msg in list_ctx_error_code(self.context)))

    def test_field_enum_reserved_range_min(self) -> None:
        eblock = make_enum_block("e1")
        make_enumfield("field1", block=eblock, number=0)
        make_enumfield("field1", block=eblock, number=1)
        eblock.reserveds = [range(1, 5)]
        self.validator.execute([eblock], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E204" for msg in list_ctx_error_code(self.context)))

    def test_enum_index_reserved_range_max(self) -> None:
        eblock = make_enum_block("e1")
        make_enumfield("field1", block=eblock, number=0)
        make_enumfield("field1", block=eblock, number=5)
        eblock.reserveds = [range(1, 5)]
        self.validator.execute([eblock], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E204" for msg in list_ctx_error_code(self.context)))

    def test_enum_index_none(self) -> None:
        eblock = make_enum_block("e1")
        make_enumfield("field1", block=eblock, number=0)
        make_enumfield("field1", block=eblock, number=None)
        self.validator.execute([eblock], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E201" for msg in list_ctx_error_code(self.context)))
