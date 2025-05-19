import unittest

from grpcAPI.makeproto.compiler import IndexValidator
from grpcAPI.makeproto.compiler.compiler import CompilerContext
from tests.makeproto.compiler.test_helpers import make_block, make_field


class TestIndexValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_block(
            "ValidBlock",
        )
        self.context = CompilerContext(blocks=[self.block])
        self.setter = IndexValidator()
        self.report = self.context.get_report(self.block.name)

    def tearDown(self) -> None:
        self.block.fields = []
        self.report.errors = []

    def test_field_index_ok(self) -> None:
        make_field("field1", block=self.block, number=1)
        make_field("field1", block=self.block, number=10)
        make_field("field1", block=self.block, number=200)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 0)

    def test_field_index_not_int(self) -> None:
        make_field("field1", block=self.block, number="foo")
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E201" == e.code for e in self.report.errors))

    def test_field_index_none(self) -> None:
        make_field("field1", block=self.block, number=None)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E201" == e.code for e in self.report.errors))

    def test_field_index_duplicated(self) -> None:
        make_field("field1", block=self.block, number=1)
        make_field("field2", block=self.block, number=1)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E202" == e.code for e in self.report.errors))
        self.assertIn(
            "Index is already used in the block", self.report.errors[0].message
        )

    def test_field_index_reserved(self) -> None:
        make_field("field1", block=self.block, number=1)
        self.block.reserveds = [1]
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E202" == e.code for e in self.report.errors))
        self.assertIn("'1' is reserved", self.report.errors[0].message)

    def test_field_index_reserved_range_min(self) -> None:
        make_field("field1", block=self.block, number=1)
        self.block.reserveds = [range(1, 5)]
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E202" == e.code for e in self.report.errors))
        self.assertIn("'1' is reserved", self.report.errors[0].message)

    def test_field_index_reserved_range_max(self) -> None:
        make_field("field1", block=self.block, number=5)
        self.block.reserveds = [range(1, 5)]
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E202" == e.code for e in self.report.errors))
        self.assertIn("'5' is reserved", self.report.errors[0].message)

    def test_field_index_zero(self) -> None:
        make_field("field1", block=self.block, number=0)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.report.errors), 1)
        self.assertTrue(any("E203" == e.code for e in self.report.errors))

    def test_field_index_enum_zero(self) -> None:
        block_enum = make_block(name="enumblock", block_type="enum")
        make_field("field1", block=block_enum, number=0)
        self.setter.execute([block_enum], self.context)
        self.assertEqual(len(self.report.errors), 0)

falta testsr o range reservado pelo google