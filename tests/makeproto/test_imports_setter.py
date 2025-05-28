import unittest

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.setters.imports import ImportsSetter
from grpcAPI.types import BaseMessage, Int32
from tests.makeproto.test_helpers import make_field, make_message_block


class DummyMessage(BaseMessage):
    @classmethod
    def package(cls) -> str:
        return "otherpkg"

    @classmethod
    def protofile(cls) -> str:
        return "otherfile"


class TopMessage(BaseMessage):
    @classmethod
    def package(cls) -> str:
        return "testpkg"

    @classmethod
    def protofile(cls) -> str:
        return "testfile"


class MockModule:
    def __init__(self) -> None:
        self.imports = set()


class TestImportsSetter(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_message_block(name="TestBlock")
        self.block.package = TopMessage.package()
        self.block.protofile = TopMessage.protofile()

        make_field(name="test_field", ftype=DummyMessage, block=self.block)
        make_field(name="test_field2", ftype=str, block=self.block)
        make_field(name="test_field3", ftype=Int32, block=self.block)
        self.ctx = CompilerContext(state={self.block.protofile: MockModule()})
        self.setter = ImportsSetter()

    def test_imports_set(self) -> None:
        self.setter.execute([self.block], self.ctx)
        imports = self.ctx.get_state(self.block.protofile).imports
        self.assertEqual(len(imports), 1)
        expected_import = "otherpkg/otherfile.proto"
        self.assertIn(expected_import, imports)

    # def test_no_duplicate_imports(self) -> None:
    #     self.setter.visit_block(self.block)
    #     self.setter.visit_block(self.block)  # Rodar 2x para testar duplicação

    #     imports = self.block.render_dict.get("imports", [])
    #     self.assertEqual(imports.count("otherpkg/otherfile"), 1)


if __name__ == "__main__":
    unittest.main()
