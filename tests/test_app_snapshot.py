import unittest
from enum import Enum
from typing import Annotated, Dict, List

from grpcAPI.proto_schema import ClassSchema, EnumSchema
from grpcAPI.types import Metadata, OneOf


class MyEnum(Enum):
    VALID = 0
    INVALID = 1


class Enum2(Enum):
    FOO = 0
    BAR = 1


class Hello:
    @classmethod
    def protofile(cls) -> str:
        return "proto"

    @classmethod
    def package(cls) -> str:
        return "pack1"

    a: Annotated[str, OneOf(key="choice")]
    aa: Annotated[int, OneOf(key="choice")]
    bb: Annotated[str, OneOf(key="choice")]
    b: Annotated[bytes, 123, "helloworld", OneOf(key="choice")]
    c: str
    d: str
    e: int
    f: Annotated[int, Metadata(options={"deprecated": True, "json_name": "f_alias"})]
    g: MyEnum
    h: Annotated[Enum2, "helloworld"]
    i: Annotated[int, 1234]
    j: List[str]
    k: Annotated[
        List[bool], 1, Metadata(options={"deprecated": True, "json_name": "k_alias"})
    ]
    li: Dict[str, MyEnum]
    m: Dict[int, bytes] = Metadata(description='Comment for "m"')
    y: int = OneOf(key="outro")
    z: bool = OneOf(key="outro")
    zz: str = OneOf(key="outro")
    zzz: str = OneOf(key="outro")


class TestHelloSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = ClassSchema(cls=Hello)

    def test_serialize_structure(self) -> None:
        data = self.schema.serialize()
        self.assertIn("module", data)
        self.assertIn("qualname", data)
        self.assertIn("fields", data)
        self.assertIsInstance(data["fields"], list)
        self.assertGreater(len(data["fields"]), 0)

    def test_fields_contain_expected_names(self) -> None:
        field_names = {f[0] for f in self.schema.serialize()["fields"]}
        expected_fields = {
            "a",
            "aa",
            "bb",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "li",
            "m",
            "y",
            "z",
            "zz",
            "zzz",
        }
        self.assertTrue(expected_fields.issubset(field_names))

    def test_oneof_group_choice_detected(self) -> None:
        fields = self.schema._get_fields()
        choice_keys = {f[0] for f in fields if f[2] == "choice"}
        expected = {"a", "aa", "bb", "b"}
        self.assertEqual(choice_keys, expected)

    def test_oneof_group_outro_detected(self) -> None:
        fields = self.schema._get_fields()
        outro_keys = {f[0] for f in fields if f[2] == "outro"}
        expected = {"y", "z", "zz", "zzz"}
        self.assertEqual(outro_keys, expected)

    def test_schema_hash_is_stable(self) -> None:
        h1 = self.schema.hash()
        h2 = self.schema.hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)  # SHA256 length


class MyEnum(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3

    @classmethod
    def package(cls) -> str:
        return "test_package"

    @classmethod
    def protofile(cls) -> str:
        return "test.proto"


class TestEnumSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = EnumSchema(cls=MyEnum)

    def test_serialize_structure(self) -> None:
        data = self.schema.serialize()
        self.assertIn("module", data)
        self.assertIn("qualname", data)
        self.assertIn("package", data)
        self.assertIn("protofile", data)
        self.assertIn("fields", data)
        self.assertIsInstance(data["fields"], list)
        self.assertGreater(len(data["fields"]), 0)

    def test_fields_content(self) -> None:
        fields = self.schema.serialize()["fields"]
        expected = [(member.name, member.value) for member in MyEnum]
        self.assertCountEqual(fields, expected)  # compara listas independente da ordem

    def test_hash_is_stable(self) -> None:
        h1 = self.schema.hash()
        h2 = self.schema.hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)  # SHA256 length


if __name__ == "__main__":
    unittest.main()
