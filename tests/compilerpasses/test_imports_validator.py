import unittest

from grpcAPI.makeproto.compiler import CompilerContext, ImportsValidator
from grpcAPI.makeproto.compiler.compiler import list_ctx_error_code
from grpcAPI.types import BaseMessage
from tests.compilerpasses.test_helpers import make_field, make_message_block


class DummyMessage(BaseMessage):
    @classmethod
    def package(cls) -> str:
        return "testpkg"

    @classmethod
    def protofile(cls) -> str:
        return "testfile"


class TestImportsValidator(unittest.TestCase):
    def setUp(self) -> None:
        # Block com um field de tipo DummyMessage
        self.block = make_message_block(name="TestBlock")
        self.field = make_field(name="test_field", ftype=DummyMessage, block=self.block)

        self.packset = {("testpkg", "testfile")}
        self.ctx = CompilerContext(state={"_packages": self.packset})
        self.validator = ImportsValidator()

    def test_valid_import(self) -> None:
        self.validator.execute([self.block], self.ctx)
        self.assertEqual(len(self.ctx), 0)

    def test_invalid_import(self) -> None:
        # Alterando ftype para não mapeado
        class OtherMessage(BaseMessage):
            @classmethod
            def package(cls) -> str:
                return "otherpkg"

            @classmethod
            def protofile(cls) -> str:
                return "otherfile"

        self.field.ftype = OtherMessage
        self.validator.execute([self.block], self.ctx)
        self.assertEqual(len(self.ctx), 1)
        self.assertEqual(list_ctx_error_code(self.ctx), ["E305"])


if __name__ == "__main__":
    unittest.main()
