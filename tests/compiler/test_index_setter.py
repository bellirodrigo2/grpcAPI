import unittest

from grpcAPI.makeproto.compiler import IndexSetter
from grpcAPI.makeproto.compiler.compiler import CompilerContext
from tests.compiler.test_helpers import make_field, make_message_block


class TestIndexSetter(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.setter = IndexSetter()
        self.context = CompilerContext()

    def test_field_index_ok(self) -> None:
        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=None)
        make_field("field3", block=self.block, number=None)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.number for b in self.block.fields], [1, 2, 3])

    def test_field_index_one_set_ok(self) -> None:
        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=4)
        make_field("field3", block=self.block, number=None)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.number for b in self.block.fields], [1, 2, 4])

    def test_field_index_all_set_ok(self) -> None:
        make_field("field1", block=self.block, number=47)
        make_field("field2", block=self.block, number=32)
        make_field("field3", block=self.block, number=1)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.number for b in self.block.fields], [1, 32, 47])

    # def test_field_index_reserved_int(self) -> None: ...
    # def test_field_index_reserved_range(self) -> None: ...
    # def test_field_index_reserved_int_range(self) -> None: ...
    # def test_field_index_oneof_included(self) -> None: ...
    # def test_field_index_reset(self) -> None: ...
    # def test_field_index_reset_with_oneof(self) -> None: ...
    # def test_field_index_service_block(self) -> None: ...
    # def test_field_index_enum_block(self) -> None: ...
