import unittest

from grpcAPI.makeproto.compiler import TypeSetter
from grpcAPI.makeproto.compiler.compiler import CompilerContext
from tests.makeproto.compiler.test_helpers import make_block, make_field


class TestTypeSetter(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_block("ValidBlock")
        self.context = CompilerContext(blocks=[self.block])
        self.setter = TypeSetter()
        self.report = self.context.get_report(self.block.name)

    def tearDown(self) -> None:
        self.block.fields = []
        self.report.errors = []

    def test_enum_field_with_type(self) -> None:
        make_field("field1", block=self.block, ftype=int)
        context = CompilerContext(blocks=[self.block])
        self.setter.execute([self.block], context)
        print(len(self.block.fields))

    def test_w(self) -> None:
        make_field("field2", block=self.block, ftype=int)
        context = CompilerContext(blocks=[self.block])
        self.setter.execute([self.block], context)
        print(len(self.block.fields))
