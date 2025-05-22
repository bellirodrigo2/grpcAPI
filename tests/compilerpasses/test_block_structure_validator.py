import unittest

from grpcAPI.makeproto.compiler.compiler import CompilerContext, list_ctx_error_code
from grpcAPI.makeproto.compiler.validators.blockstructure import BlockStructureValidator
from tests.compilerpasses.test_helpers import (
    make_enum_block,
    make_field,
    make_message_block,
    make_oneof_block,
)


class TestBlockStructureValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = CompilerContext()
        self.validator = BlockStructureValidator()

    def test_enum_block_empty(self) -> None:
        block = make_enum_block(name="EmptyEnum")
        self.validator.execute([block], self.ctx)
        self.assertEqual(len(self.ctx), 1)
        self.assertEqual(list_ctx_error_code(self.ctx), ["E301"])

    def test_oneof_block_empty(self) -> None:
        block = make_oneof_block(name="EmptyOneof", fields=[])
        self.validator.execute([block], self.ctx)
        self.assertEqual(len(self.ctx), 1)
        self.assertEqual(list_ctx_error_code(self.ctx), ["E302"])

    def test_unlinked_field_error(self) -> None:
        block = make_message_block(name="TestMessage")
        field = make_field("field1", block=block)
        field.block = None
        self.validator.execute([block], self.ctx)
        self.assertEqual(len(self.ctx), 1)
        self.assertEqual(list_ctx_error_code(self.ctx), ["E303"])


if __name__ == "__main__":
    unittest.main()
