import unittest

from grpcAPI.makeproto.compiler import (
    CompilerContext,
    DescriptionValidator,
    OptionsValidator,
)
from grpcAPI.makeproto.compiler.compiler import list_ctx_error_code
from tests.compilerpasses.test_helpers import (
    make_field,
    make_message_block,
    make_method,
    make_oneof_block,
    make_service_block,
)


class TestInfoValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.field = make_field("field1", block=self.block)
        self.oneof_block = make_oneof_block(name="oo", block=self.block)
        self.oneof_field = make_field("oo1", block=self.oneof_block)

        self.service = make_service_block("service1")
        self.method = make_method("method1", block=self.service)

        self.optionsvalidator = OptionsValidator()
        self.descriptionvalidator = DescriptionValidator()
        self.context = CompilerContext()
        self.report = self.context.get_report(self.block.name)

    def test_options_ok(self) -> None:
        self.block.options = {"foo": "bar", "hello": True}
        self.field.options = {"foo": "bar", "hello": True}
        self.oneof_block.options = {"foo": "bar", "hello": True}
        self.oneof_field.options = {"foo": "bar", "hello": True}
        self.service.options = {"foo": "bar", "hello": True}
        self.method.options = {"foo": "bar", "hello": True}
        self.optionsvalidator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_options_error(self) -> None:
        self.block.options = {"foo": 4, "hello": True}
        self.field.options = {"foo": "bar", "hello": None}
        self.oneof_block.options = {4: [], False: True}
        self.oneof_field.options = {"foo": {}, "hello": True}
        self.service.options = "helloworld"
        self.method.options = ["foo", "bar"]
        self.optionsvalidator.execute([self.block, self.service], self.context)
        errors = list_ctx_error_code(self.context)
        self.assertEqual(len(self.context), 8)
        self.assertEqual(len([err for err in errors if err == "E503"]), 4)
        self.assertEqual(len([err for err in errors if err == "E502"]), 2)
        self.assertEqual(len([err for err in errors if err == "E501"]), 2)

    def test_description_ok(self) -> None:
        description = "foobar"
        self.block.description = description
        self.field.description = description
        self.oneof_block.description = description
        self.oneof_field.description = description
        self.service.description = description
        self.method.description = description
        self.descriptionvalidator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_description_fail(self) -> None:
        self.block.description = 42
        self.field.description = []
        self.oneof_block.description = True
        self.oneof_field.description = set()
        self.service.description = "description"
        self.method.description = 3.45
        self.descriptionvalidator.execute([self.block, self.service], self.context)
        self.assertEqual(len(self.context), 5)
        errors = list_ctx_error_code(self.context)
        self.assertTrue(all(err == "E401" for err in errors))
