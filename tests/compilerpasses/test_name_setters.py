import unittest

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.setters.name import (
    NameSetter,
    NameTransformStrategy,
    normalize_name,
    to_camel_case,
    to_pascal_case,
    to_snake_case,
)
from tests.compilerpasses.test_helpers import (
    make_field,
    make_message_block,
    make_method,
)


class TestNameTransforms(unittest.TestCase):

    def test_to_snake_case(self) -> None:
        self.assertEqual(to_snake_case("SomeName"), "some_name")
        self.assertEqual(to_snake_case("someName"), "some_name")
        self.assertEqual(
            to_snake_case("Some Name-With--Dashes"), "some_name_with_dashes"
        )
        self.assertEqual(to_snake_case("already_snake_case"), "already_snake_case")

    def test_to_camel_case(self) -> None:
        self.assertEqual(to_camel_case("some_name"), "someName")
        self.assertEqual(to_camel_case("Some_Name"), "someName")
        self.assertEqual(to_camel_case("some-name-with-dashes"), "someNameWithDashes")
        self.assertEqual(
            to_camel_case("alreadyCamelCase"), "alreadyCamelCase"
        )  # Note: lowercase first char

    def test_to_pascal_case(self) -> None:
        self.assertEqual(to_pascal_case("some_name"), "SomeName")
        self.assertEqual(to_pascal_case("some-name-with-dashes"), "SomeNameWithDashes")
        self.assertEqual(to_pascal_case("AlreadyPascalCase"), "Alreadypascalcase")

    def test_normalize_name(self) -> None:
        self.assertEqual(
            normalize_name("someName", NameTransformStrategy.SNAKE_CASE), "some_name"
        )
        self.assertEqual(
            normalize_name("some_name", NameTransformStrategy.CAMEL_CASE), "someName"
        )
        self.assertEqual(
            normalize_name("some_name", NameTransformStrategy.PASCAL_CASE), "SomeName"
        )
        self.assertEqual(
            normalize_name("some_name", NameTransformStrategy.NO_TRANSFORM), "some_name"
        )


class TestNameSetter(unittest.TestCase):
    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.context = CompilerContext()

    def test_visit_field_and_method_no_transform(self) -> None:
        field = make_field("FieldName", block=self.block)
        method = make_method("MethodName", block=self.block)
        normalizer = NameSetter()
        normalizer.execute([self.block], self.context)
        block_dict = self.block.render_dict
        field_dict = field.render_dict
        method_dict = method.render_dict
        self.assertEqual(block_dict["name"], "ValidBlock")
        self.assertEqual(field_dict["name"], "FieldName")
        self.assertEqual(method_dict["name"], "MethodName")

    def test_visit_field_and_method_snake(self) -> None:
        field = make_field("FieldName", block=self.block)
        method = make_method("MethodName", block=self.block)
        normalizer = NameSetter("snake_case")
        normalizer.execute([self.block], self.context)
        block_dict = self.block.render_dict
        field_dict = field.render_dict
        method_dict = method.render_dict

        self.assertEqual(block_dict["name"], "valid_block")
        self.assertEqual(field_dict["name"], "field_name")
        self.assertEqual(method_dict["name"], "method_name")

    def test_camel_case(self) -> None:
        block = make_message_block("block_name")
        field1 = make_field("field_one", block=block)
        field2 = make_field("field_two", block=block)
        normalizer = NameSetter(strategy="camel_case")
        normalizer.execute([block], self.context)

        field1_dict = field1.render_dict
        field2_dict = field2.render_dict
        block_dict = block.render_dict

        self.assertEqual(block_dict["name"], "blockName")
        self.assertEqual(field1_dict["name"], "fieldOne")
        self.assertEqual(field2_dict["name"], "fieldTwo")


if __name__ == "__main__":
    unittest.main()
