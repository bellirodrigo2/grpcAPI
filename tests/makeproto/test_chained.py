import unittest
from typing import Any, Callable, Dict, Iterable, List, Union

from typing_extensions import Annotated

from grpcAPI.makeproto.makeblock import make_enumblock, make_msgblock
from grpcAPI.makeproto.protoblock import Block, EnumBlock, MessageBlock
from grpcAPI.mapclss import map_service_classes
from grpcAPI.types import (
    BaseMessage,
    Context,
    Float,
    Int32,
    Metadata,
    OneOf,
    Stream,
    String,
)
from grpcAPI.types.message import BaseEnum


def map_classes_blocks(
    clss: Iterable[type[Union[BaseMessage, BaseEnum]]],
) -> List[Block]:
    all_blocks: Dict[str, Block] = {}
    for cls in clss:
        if issubclass(cls, BaseEnum):
            name = cls.__name__
            if name not in all_blocks:
                all_blocks[name] = make_enumblock(cls)
        elif issubclass(cls, BaseMessage):
            name = cls.__name__
            if name not in all_blocks:
                all_blocks[name] = make_msgblock(cls)

    return list(all_blocks.values())


class ProtoMessage(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "teste"


class ID(ProtoMessage):
    id: int


class User(ProtoMessage):
    id: ID
    name: String
    lastname: str
    email: Annotated[
        String,
        Metadata(comment="email comment", options={"json_name": "email_field"}),
    ]
    age: int
    tags: list[String]
    code2: "Code"
    pa: "ProductArea"
    o1: Annotated[bool, OneOf("oo1")]
    o2: Annotated[str, OneOf("oo1")]
    o3: Annotated[int, OneOf("oo1")]
    o4: Annotated[str, OneOf("oo1")]


class Code(ProtoMessage):
    code: int
    pa: "ProductArea"
    s: List[str]
    le: list["ProductArea"]
    me: dict[str, "Enum2"]


class ProductArea(BaseEnum):
    @classmethod
    def protofile(cls) -> str:
        return "teste"

    @classmethod
    def package(cls) -> str:
        return "testepack"

    Area1 = 0
    Area2 = 1
    Area3 = 2


class Enum2(BaseEnum):
    @classmethod
    def protofile(cls) -> str:
        return "teste"

    @classmethod
    def package(cls) -> str:
        return "testepack"

    e1 = 0
    e2 = 1


class Product(ProtoMessage):
    name: String
    unit_price: dict[String, Float]
    code: Code
    area: ProductArea
    enum2: Enum2


class Requisition(ProtoMessage):
    user: User
    code: Code
    product: Product
    quantity: Int32
    enum2: Enum2


class CollectionMsg(ProtoMessage):
    list_id: List[Requisition]
    dict_prod: Dict[str, Product]


def func1(coll: CollectionMsg, context: Context) -> Requisition:
    pass


def func2(col: Requisition, name: str) -> Stream[Requisition]:
    pass


def func3(coll: Stream[CollectionMsg]) -> ID:
    pass


def func4(coll: Stream[Product]) -> Stream[CollectionMsg]:
    pass


def map_service_to_blocks(
    methods: List[Callable[..., Any]],
) -> List[Block]:
    clss = map_service_classes(methods)
    return map_classes_blocks(clss)


class MapServiceToBlocksTest(unittest.TestCase):
    def test_map_service_to_blocks_various_funcs(self) -> None:
        methods = [func1, func2, func3, func4]
        blocks = map_service_to_blocks(methods)
        expected_messages = {
            "CollectionMsg",
            "Requisition",
            "Product",
            "Code",
            "User",
            "ID",
        }
        expected_enums = {
            "ProductArea",
            "Enum2",
        }
        message_blocks = {
            block.name for block in blocks if isinstance(block, MessageBlock)
        }
        enum_blocks = {block.name for block in blocks if isinstance(block, EnumBlock)}
        self.assertEqual(
            message_blocks,
            expected_messages,
            f"Incorrect Message blocks: {message_blocks}",
        )
        self.assertEqual(
            enum_blocks, expected_enums, f"Incorrect Enum blocks: {enum_blocks}"
        )
        total_expected = len(expected_messages) + len(expected_enums)
        self.assertEqual(
            len(blocks),
            total_expected,
            f"Incorrect number of blocks: {len(blocks)}",
        )

        excluded_types = {"Context", "str", "int", "float"}
        for block in blocks:
            self.assertNotIn(
                block.name,
                excluded_types,
                f"Tipo {block.name} não deveria ter sido incluído.",
            )


if __name__ == "__main__":
    unittest.main()
