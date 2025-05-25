import unittest
from enum import Enum
from pprint import pprint
from typing import List

from grpcAPI.makeproto import (
    CompilerContext,
    CompilerPass,
    IndexSetter,
    NameSetter,
    TypeSetter,
)
from grpcAPI.types.message import BaseMessage
from tests.compilerpasses.test_helpers import (
    make_field,
    make_message_block,
    make_oneof_block,
    make_oneof_field,
)


class Proto(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "proto1"

    @classmethod
    def package(cls) -> str:
        return "pack1"


class Enum1(Enum):
    @classmethod
    def protofile(cls) -> str:
        return "proto1"

    @classmethod
    def package(cls) -> str:
        return "pack1"


class TestTypeValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        make_field("field1", self.block, str, None, "comment1")
        make_field("field2", self.block, Proto, None, "comment1")
        make_field("enum", self.block, Enum1, None, "comment1")
        ooblock = make_oneof_block("oneof1", block=self.block)
        make_oneof_field("oo1", key="key1", block=ooblock, ftype=int, number=1)
        make_oneof_field("oo2", key="key1", block=ooblock, ftype=Proto)
        # self.service = make_service_block("Service")
        self.ctx = CompilerContext()

        self.setters: List[CompilerPass] = [
            TypeSetter(),
            NameSetter(),
            IndexSetter(),
        ]

    def test_setter(self) -> None:
        for compass in self.setters:
            compass.execute([self.block], self.ctx)
        rendering_dict = self.block.get_render_dict()
        self.assertEqual(rendering_dict["block_type"], "message")
        self.assertEqual(len(rendering_dict["fields"]), 4)
        self.assertEqual(rendering_dict["name"], "ValidBlock")
        oo_rendering_dict = rendering_dict["fields"][0]
        self.assertEqual(oo_rendering_dict["block_type"], "oneof")
        self.assertEqual(len(oo_rendering_dict["fields"]), 2)
        self.assertEqual(oo_rendering_dict["name"], "oneof1")
        # pprint(rendering_dict)
