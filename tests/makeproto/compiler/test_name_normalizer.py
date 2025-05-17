import unittest

from grpcAPI.makeproto.compiler.passes.name import (
    NameNormalizer,
    NameTransformStrategy,
    normalize_name,
    to_camel_case,
    to_pascal_case,
    to_snake_case,
)
from tests.makeproto.compiler.test_helpers import make_block, make_field, make_method


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


class TestNameNormalizer(unittest.TestCase):

    def test_visit_field_and_method(self) -> None:
        normalizer = NameNormalizer(strategy=NameTransformStrategy.SNAKE_CASE)

        field = make_field("FieldName")
        method = make_method("MethodName")

        normalizer.visit_field(field)
        normalizer.visit_method(method)

        self.assertEqual(field.name, "field_name")
        self.assertEqual(method.name, "method_name")

    def test_visit_block(self) -> None:
        field1 = make_field("FieldOne")
        field2 = make_field("FieldTwo")
        block = make_block("BlockName", [field1, field2])

        normalizer = NameNormalizer(strategy=NameTransformStrategy.CAMEL_CASE)
        normalizer.visit_block(block)

        self.assertEqual(block.name, "blockName")
        self.assertEqual(field1.name, "fieldOne")
        self.assertEqual(field2.name, "fieldTwo")


if __name__ == "__main__":
    unittest.main()
