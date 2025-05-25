import unittest

from grpcAPI.makeproto import CompilerContext, IndexSetter
from tests.compilerpasses.test_helpers import (
    make_enum_block,
    make_enumfield,
    make_field,
    make_message_block,
    make_method,
    make_oneof_block,
    make_oneof_field,
    make_service_block,
)


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
        self.assertEqual([b.index for b in self.block.fields], [1, 2, 3])

    def test_field_index_one_set_ok_high(self) -> None:
        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=4)
        make_field("field3", block=self.block, number=None)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [1, 2, 4])
        self.assertEqual(
            [b.name for b in self.block.fields], ["field1", "field3", "field2"]
        )

    def test_field_index_one_set_ok_low(self) -> None:
        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=1)
        make_field("field3", block=self.block, number=None)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [1, 2, 3])
        self.assertEqual(
            [b.name for b in self.block.fields], ["field2", "field1", "field3"]
        )

    def test_field_index_all_set_ok(self) -> None:
        make_field("field1", block=self.block, number=47)
        make_field("field2", block=self.block, number=32)
        make_field("field3", block=self.block, number=1)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [1, 32, 47])

    def test_field_index_reserved(self) -> None:
        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=None)
        make_field("field3", block=self.block, number=None)
        self.block.reserveds = [1, range(3, 5)]
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [2, 6, 7])

    def test_field_index_reserved_set(self) -> None:
        make_field("field1", block=self.block, number=2)
        make_field("field2", block=self.block, number=None)
        make_field("field3", block=self.block, number=6)
        make_field("field4", block=self.block, number=7)
        make_field("field5", block=self.block, number=None)
        self.block.reserveds = [1, range(3, 5)]
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [2, 6, 7, 8, 9])
        self.assertEqual(
            [b.name for b in self.block.fields],
            ["field1", "field3", "field4", "field2", "field5"],
        )

    def test_field_index_reserved_set_ondeof(self) -> None:
        make_field("field1", block=self.block, number=7)
        make_field("field2", block=self.block, number=None)
        make_field("field3", block=self.block, number=6)
        oo = make_oneof_block("oneof1", block=self.block)
        make_oneof_field("oo1", block=oo, number=2)
        make_oneof_field("oo2", block=oo, number=None)
        self.block.reserveds = [1, range(3, 5)]
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [2, 6, 7, 8])
        self.assertEqual(
            [b.name for b in self.block.fields],
            ["oneof1", "field3", "field1", "field2"],
        )
        self.assertEqual([b.index for b in oo.fields], [2, 9])
        self.assertEqual(
            [b.name for b in oo.fields],
            ["oo1", "oo2"],
        )

    def test_field_index_oneof_included(self) -> None:

        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=None)
        make_field("field3", block=self.block, number=None)
        oo = make_oneof_block("oneof1", block=self.block)
        make_oneof_field("oo1", block=oo, number=None)
        make_oneof_field("oo2", block=oo, number=None)
        self.setter.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [1, 2, 3, 4])
        self.assertEqual([b.index for b in oo.fields], [4, 5])

    def test_index_reset(self) -> None:
        make_field("field1", block=self.block, number=None)
        make_field("field2", block=self.block, number=None)
        make_field("field3", block=self.block, number=None)
        oo = make_oneof_block("oneof1", block=self.block)
        make_oneof_field("oo1", block=oo, number=None)
        make_oneof_field("oo2", block=oo, number=None)

        block2 = make_message_block("block2")
        make_field("field1", block=block2, number=None)
        make_field("field2", block=block2, number=None)
        make_field("field3", block=block2, number=None)
        oo2 = make_oneof_block("oneof1", block=block2)
        make_oneof_field("oo1", block=oo2, number=None)
        make_oneof_field("oo2", block=oo2, number=None)

        self.setter.execute([self.block, block2], self.context)

        self.assertEqual(len(self.context), 0)
        self.assertEqual([b.index for b in self.block.fields], [1, 2, 3, 4])
        self.assertEqual([b.index for b in oo.fields], [4, 5])

        self.assertEqual([b.index for b in block2.fields], [1, 2, 3, 4])
        self.assertEqual([b.index for b in oo2.fields], [4, 5])

    def test_field_index_service_block(self) -> None:
        service = make_service_block("service")
        make_method("method1", service)
        make_method("method2", service)
        self.setter.execute([service], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_index_enum_block(self) -> None:
        enumblock = make_enum_block("eblock")
        make_enumfield("e1", enumblock, number=None)
        make_enumfield("e1", enumblock, number=None)
        self.setter.execute([enumblock], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertEqual([e.index for e in enumblock.fields], [None, None])
