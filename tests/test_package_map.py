import unittest
from contextvars import Context
from enum import Enum
from typing import Dict, List

from typing_extensions import Annotated

from grpcAPI.app import Package, map_package_block
from grpcAPI.makeproto.compiler.compiler import CompilerContext
from grpcAPI.makeproto.compiler.validators.name import BlockNameValidator
from grpcAPI.makeproto.protoblock import EnumBlock, MessageBlock, ServiceBlock
from grpcAPI.types import BaseMessage, Float, Int32, Metadata, OneOf, Stream, String


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


class ProductArea(Enum):
    @classmethod
    def protofile(cls) -> str:
        return "teste"

    @classmethod
    def package(cls) -> str:
        return "testepack"

    Area1 = 0
    Area2 = 1
    Area3 = 2


class Enum2(Enum):
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


class ListBlocksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = Package("pack1")
        self.mod1 = self.pack.Module("mod1")
        self.mod2 = self.pack.Module("mod2")
        serv1 = self.mod1.Service("serv1")
        serv2 = self.mod2.Service("serv2")

        @serv1()
        def func1(coll: CollectionMsg, context: Context) -> Requisition:
            return Requisition()

        @serv1()
        def func2(col: User, name: str) -> Stream[Requisition]:
            return Requisition()

        @serv2()
        def func3(coll: Stream[CollectionMsg]) -> ID:
            return ID()

        @serv2()
        def func4(coll: Stream[Product]) -> Stream[CollectionMsg]:
            return CollectionMsg()

        self.blocks = map_package_block(self.pack, [])

    def test_total_blocks(self) -> None:
        total_blocks = len(self.blocks)
        # 2 serviços + 6 mensagens + 2 enums = 10
        self.assertEqual(total_blocks, 10)

    def test_all_block_names(self) -> None:
        blocks = self.blocks
        block_names = set(b.name for b in blocks)
        expected_block_names = {
            "serv1",
            "serv2",
            "CollectionMsg",
            "Requisition",
            "Product",
            "Code",
            "User",
            "ID",
            "ProductArea",
            "Enum2",
        }
        self.assertEqual(block_names, expected_block_names)

    def test_list_blocks_with_proto_classes(self) -> None:
        blocks = self.blocks
        service_blocks = [b for b in blocks if isinstance(b, ServiceBlock)]
        message_blocks = [b for b in blocks if isinstance(b, MessageBlock)]
        enum_blocks = [b for b in blocks if isinstance(b, EnumBlock)]

        self.assertEqual([serv.name for serv in service_blocks], ["serv1", "serv2"])
        expected_messages = {
            "CollectionMsg",
            "Requisition",
            "Product",
            "Code",
            "User",
            "ID",
        }
        self.assertEqual(expected_messages, set([m.name for m in message_blocks]))
        expected_enums = {"ProductArea", "Enum2"}
        self.assertEqual(expected_enums, set([m.name for m in enum_blocks]))

    def test_service_block_metadata(self) -> None:
        blocks = self.blocks
        service_blocks = [b for b in blocks if isinstance(b, ServiceBlock)]
        for service in service_blocks:
            self.assertEqual(
                service.protofile, "mod1" if service.name == "serv1" else "mod2"
            )
            self.assertEqual(service.package, "pack1")

    def test_validate_block_name(self) -> None:
        validator = BlockNameValidator()
        context = CompilerContext()
        validator.execute(self.blocks, context)
        self.assertEqual(len(context), 0)

    def test_validate_block_name_fail(self) -> None:
        validator = BlockNameValidator()
        context = CompilerContext()
        self.blocks[0].name = "Enum2"
        validator.execute(self.blocks, context)
        self.assertEqual(len(context), 1)


if __name__ == "__main__":
    unittest.main()
