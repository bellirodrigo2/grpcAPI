import unittest
from enum import Enum
from typing import Dict, List, Type

from grpcAPI.makeproto.makeblock import make_enumblock, make_msgblock
from grpcAPI.makeproto.protoblock import Block, EnumBlock, MessageBlock
from grpcAPI.mapclss import cls_map
from grpcAPI.types import BaseMessage, Int32


def cls_to_blocks(tgt: Type[BaseMessage]) -> List[Block]:

    clss = cls_map(tgt)

    blocks: List[Block] = []
    for cls in clss:
        if issubclass(cls, Enum):
            enumblock = make_enumblock(cls)
            blocks.append(enumblock)

        elif issubclass(cls, BaseMessage):
            msgblock = make_msgblock(cls)
            blocks.append(msgblock)
    return blocks


class Proto1(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "proto"

    @classmethod
    def package(cls) -> str:
        return "pack1"


class MyEnum(Proto1, Enum):
    VALID = 0
    INVALID = 1


class Nested(Proto1):
    field: Int32


class Complex(Proto1):
    enum_field: MyEnum
    nested_field: Nested
    list_of_nested: List[Nested]
    map_field: Dict[str, Nested]


class ClsMapTest(unittest.TestCase):

    def test_cls_map_simple(self) -> None:
        result = cls_map(Nested)
        self.assertIn(Nested, result)
        self.assertEqual(len(result), 1)

    def test_cls_map_complex(self) -> None:
        result = cls_map(Complex)
        self.assertIn(Complex, result)
        self.assertIn(Nested, result)
        self.assertIn(MyEnum, result)
        self.assertEqual(len(result), 3)  # Complex, Nested, MyEnum

    def test_cls_map_deduplication(self) -> None:
        result = cls_map(Complex)
        # Mesmo rodando novamente, não cresce nem repete
        result2 = cls_map(Complex, visited=result.copy())
        self.assertEqual(result, result2)

    def test_cls_to_blocks(self) -> None:
        blocks = cls_to_blocks(Complex)
        block_names = {b.name for b in blocks}
        expected_names = {"Complex", "Nested", "MyEnum"}
        self.assertEqual(block_names, expected_names)

        # Check types
        enum_blocks = [b for b in blocks if isinstance(b, EnumBlock)]
        msg_blocks = [b for b in blocks if isinstance(b, MessageBlock)]

        self.assertEqual(len(enum_blocks), 1)
        self.assertEqual(len(msg_blocks), 2)

    def test_enum_block(self) -> None:
        blocks = cls_to_blocks(MyEnum)
        self.assertEqual(len(blocks), 1)
        self.assertTrue(isinstance(blocks[0], EnumBlock))
        self.assertEqual(blocks[0].name, "MyEnum")

    def test_recursive_map(self) -> None:
        class Recursive(Proto1):
            self_ref: "Recursive"

        result = cls_map(Recursive)
        self.assertIn(Recursive, result)
        self.assertEqual(len(result), 1)  # Não entra em loop infinito!


if __name__ == "__main__":
    unittest.main()
