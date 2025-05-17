import unittest
from enum import Enum
from pathlib import Path
from typing import List, Mapping, Sequence

from typing_extensions import Annotated

from grpcAPI.makeproto.protoobj.base import FieldSpec, OneOf
from grpcAPI.makeproto.protoobj.types import Float, String
from grpcAPI.proxy.importer import import_py_files_from_folder
from grpcAPI.proxy.proto_proxy import bind_proto_proxy
from grpcAPI.proxy.proxy import ProxyMessage


class ProtoMessage(ProxyMessage):
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
        FieldSpec(comment="email comment", options={"json_name": "email_field"}),
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
    Area1 = 0
    Area2 = 1
    Area3 = 2


class Enum2(Enum):
    e1 = 0
    e2 = 1


class Product(ProtoMessage):
    name: String
    unit_price: dict[String, Float]
    code: Code
    area: ProductArea
    enum2: Enum2


class ProxyTest(unittest.TestCase):

    def setUp(self) -> None:
        self.p = Path(__file__).parent / "proto" / "compiled"
        self.modules = import_py_files_from_folder(self.p)

        bind_proto_proxy(ID, self.modules)
        bind_proto_proxy(User, self.modules)
        bind_proto_proxy(Code, self.modules)
        bind_proto_proxy(Product, self.modules)

        self.id_value = 15
        self.proxy_id = ID(id=self.id_value)

        self.obj_prodarea = ProductArea.Area1
        self.obj_enum2 = Enum2.e1
        self.code_num = 12
        self.s = ["foo", "bar"]
        self.le = [self.obj_prodarea]
        self.me = {"foo": self.obj_enum2}
        self.proxy_code = Code(
            code=self.code_num,
            pa=self.obj_prodarea,
            s=self.s.copy(),
            le=self.le,
            me=self.me.copy(),
        )

        self.product_name = "John"
        self.unit_price = {"foo": 3.1415}
        self.proxy_product = Product(
            name=self.product_name,
            unit_price=self.unit_price,
            code=self.proxy_code,
            area=self.obj_prodarea,
            enum2=self.obj_enum2,
        )

    def test_proxy(self) -> None:
        proxy_id = self.proxy_id
        n = self.id_value

        self.assertEqual(proxy_id.id, n)
        proto_id = proxy_id.unwrap
        self.assertEqual(proto_id.id, n)

        proxy_id2 = ID(_wrapped=proto_id)
        self.assertEqual(proxy_id2.id, n)

        for new_val in [13, 12, 11]:
            proxy_id.id = new_val
            self.assertEqual(proxy_id.id, new_val)
            proto_id = proxy_id.unwrap
            self.assertEqual(proto_id.id, new_val)
            proxy_id2 = ID(_wrapped=proto_id)
            self.assertEqual(proxy_id2.id, new_val)

    def test_code_simple(self) -> None:
        code = self.proxy_code
        proto_code = code.unwrap
        code2 = Code(_wrapped=proto_code)

        self.assertEqual(code.code, self.code_num)
        self.assertEqual(code.pa, self.obj_prodarea)
        self.assertEqual(code.s, self.s)
        self.assertEqual(code.le, self.le)
        self.assertEqual(code.me, self.me)

        self.assertEqual(proto_code.code, self.code_num)
        self.assertEqual(proto_code.pa, self.obj_prodarea.value)
        self.assertEqual(proto_code.s, self.s)
        self.assertEqual(proto_code.le, [l.value for l in self.le])
        self.assertEqual(proto_code.me, {k: v.value for k, v in self.me.items()})

        self.assertEqual(code2, code)

    def test_code_enum(self) -> None:
        code = self.proxy_code
        proto_code = code.unwrap
        code2 = Code(_wrapped=proto_code)

        code.pa = ProductArea.Area2
        self.assertEqual(code.pa, ProductArea.Area2)
        self.assertEqual(proto_code.pa, ProductArea.Area2.value)
        self.assertEqual(code2.pa, ProductArea.Area2)

    def test_code_list(self) -> None:
        code = self.proxy_code
        proto_code = code.unwrap
        code2 = Code(_wrapped=proto_code)

        code.s.append("hello")
        self.assertEqual(len(code.s), 3)
        self.assertEqual(code.s[-1], "hello")

        code.s = ["new"]
        self.assertEqual(code.s, ["new"])

        code.s[0] = "modified"
        self.assertEqual(code.s[0], "modified")

        code.s.extend(["more", "values"])
        self.assertEqual(code.s[-2:], ["more", "values"])

        code.s.insert(1, "middle")
        code.s.remove("middle")

        item = code.s.pop()
        self.assertEqual(item, "values")

        code.s.clear()
        self.assertEqual(code.s, [])

        code.s = ["a", "b", "c"]
        code.s.reverse()
        self.assertEqual(code.s, ["c", "b", "a"])

        copy_list2 = code.s.copy()
        copy_list2.pop()
        self.assertEqual(len(code.s), 3)

        code.s.sort()
        self.assertEqual(code.s, ["a", "b", "c"])

        code.s[:2] = ["x", "y"]
        self.assertEqual(code.s[:2], ["x", "y"])

    def test_code_dict(self) -> None:
        code = self.proxy_code
        proto = code.unwrap

        self.assertEqual(proto.me["foo"], Enum2.e1.value)

        del code.me["foo"]
        self.assertEqual(code.me, {})

        code.me["abc"] = Enum2.e2
        self.assertEqual(code.me["abc"], Enum2.e2)

        code.me["123"] = Enum2.e1
        self.assertEqual(set(code.me.keys()), {"abc", "123"})
        self.assertIn(Enum2.e2, code.me.values())

        self.assertEqual(code.me.get("abc"), Enum2.e2)
        self.assertIsNone(code.me.get("nonexistent_key"))

        self.assertEqual(code.me.pop("abc"), Enum2.e2)
        self.assertNotIn("abc", code.me)

        code.me.clear()
        self.assertEqual(code.me, {})

        code.me.update({"new_key": Enum2.e1})
        self.assertEqual(code.me["new_key"], Enum2.e1)

        self.assertEqual(code.me.setdefault("new_key", Enum2.e2), Enum2.e1)

        self.assertEqual(code.me.get("no_existant", 45), 45)
        self.assertEqual(len(code.me), 1)

        code.me.set("new_key2", Enum2.e1)
        self.assertEqual(len(code.me), 2)

        with self.assertRaises(TypeError):
            code.me.set("new_key2", 0)

        with self.assertRaises(TypeError):
            code.me.set("new_key2", None)

        with self.assertRaises(TypeError):
            code.me["new_key2"] = 0

        with self.assertRaises(TypeError):
            code.me["new_key2"] = None

        self.assertIsInstance(code.me, Mapping)

    def test_code_unwrap(self) -> None:
        code = self.proxy_code
        proto = code.unwrap
        code2 = Code(_wrapped=proto)
        self.assertIs(code.unwrap, code2.unwrap)

    def test_code_wrong(self) -> None:
        code = self.proxy_code
        proto = code.unwrap
        code2 = Code(_wrapped=proto)

        code.s = []
        code.s.append("foo")

        with self.assertRaises(TypeError):
            code.s[0] = 4
        with self.assertRaises(TypeError):
            code.s.append(4)
        with self.assertRaises(TypeError):
            code.s.extend(4)

        self.assertIsInstance(code.s, Sequence)

        with self.assertRaises(TypeError):
            Code(code="not an int")

        with self.assertRaises(TypeError):
            code.pa = "not an enum"

        with self.assertRaises(TypeError):
            code.code = "not an int"

        with self.assertRaises(TypeError):
            code.s = 3

        with self.assertRaises(TypeError):
            code.me = 3

    def test_product(self) -> None:
        product = self.proxy_product
        self.assertEqual(product.code, self.proxy_code)
        self.assertEqual(product.code.code, self.proxy_code.code)


if __name__ == "__main__":
    unittest.main()

#     assert proto_product.code.code == obj_prod.code.code
#     for item in proto_product.code.s:
#         assert item in obj_prod.code.s
#     assert proto_product.code.le == [l.value for l in obj_prod.code.le]
#     assert proto_product.code.me == {k: v.value for k, v in obj_prod.code.me.items()}

#     cls_product = converter.from_proto(proto_product, Product)
#     assert cls_product.name == name

#     for k, v in cls_product.unit_price.items():
#         assert f"{v:.2f}" == f"{unit_price[k]:.2f}"

#     assert cls_product.code.code == obj_prod.code.code
#     assert cls_product.code.code == obj_prod.code.code
#     assert cls_product.code.s == obj_prod.code.s
#     assert cls_product.code.le == obj_prod.code.le
#     assert cls_product.code.me == obj_prod.code.me

#     # User TEst

#     name_user = "Maria"
#     lastname = "Silva"
#     email = "foo.bar@gmail.com"
#     age = 49
#     tags = ["foo", "bar"]
#     oobool = True
#     obj_user = user(
#         id=obj_id,
#         name=name_user,
#         lastname=lastname,
#         email=email,
#         age=age,
#         tags=tags,
#         code2=obj_code,
#         pa=obj_prodarea,
#         o1=oobool,
#         o2=None,
#         o3=None,
#         o4=None,
#     )
#     proto_user = converter.to_proto(obj_user)
#     assert proto_user.id.id == obj_id.id
#     assert proto_user.name == name_user
#     assert proto_user.lastname == lastname
#     assert proto_user.email == email
#     assert proto_user.age == age
#     assert proto_user.tags == tags
#     assert proto_user.code2.pa == obj_code.pa.value

#     assert proto_user.o1 == oobool
#     assert proto_user.o2 == ""
#     assert proto_user.o3 == 0
#     assert proto_user.o4 == ""

#     cls_user = converter.from_proto(proto_user, user)
#     assert cls_user.id.id == obj_id.id
#     assert cls_user.name == name_user
#     assert cls_user.lastname == lastname
#     assert cls_user.email == email
#     assert cls_user.age == age
#     assert cls_user.tags == tags
#     assert cls_user.code2.pa == obj_code.pa

#     assert cls_user.o1 == oobool
#     assert cls_user.o2 == ""
#     assert cls_user.o3 == 0
#     assert cls_user.o4 == ""

#     # Requisition Test

#     quantity = 32
#     obj_req = requisition(
#         user=obj_user,
#         code=obj_code,
#         product=obj_prod,
#         quantity=quantity,
#         enum2=obj_enum2,
#     )

#     proto_req = converter.to_proto(obj_req)
#     assert proto_req.user.id.id == obj_user.id.id
#     assert proto_req.user.name == obj_user.name
#     assert proto_req.user.lastname == obj_user.lastname
#     assert proto_req.user.email == obj_user.email
#     assert proto_req.user.tags == obj_user.tags
#     assert proto_req.user.code2.code == obj_user.code2.code
#     assert proto_req.user.code2.pa == obj_user.code2.pa.value
#     for item in proto_req.user.code2.s:
#         assert item in obj_user.code2.s

#     assert proto_req.user.code2.le == [l.value for l in obj_user.code2.le]
#     assert proto_req.user.code2.me == {k: v.value for k, v in obj_user.code2.me.items()}

#     assert proto_req.user.pa == obj_user.pa.value
#     assert proto_req.user.o1 == obj_user.o1

#     assert not proto_req.user.o2 and not obj_user.o2
#     assert not proto_req.user.o3 and not obj_user.o3
#     assert not proto_req.user.o4 and not obj_user.o4

#     assert proto_req.enum2 == obj_Enum2.value
#     assert proto_req.quantity == quantity

#     cls_req = converter.from_proto(proto_req, requisition)
#     assert cls_req.user.id.id == obj_user.id.id
#     assert cls_req.user.name == obj_user.name
#     assert cls_req.user.lastname == obj_user.lastname
#     assert cls_req.user.email == obj_user.email
#     assert cls_req.user.tags == obj_user.tags
#     assert cls_req.user.code2.code == obj_user.code2.code
#     assert cls_req.user.code2.pa == obj_user.code2.pa
#     for item in cls_req.user.code2.s:
#         assert item in obj_user.code2.s

#     assert cls_req.user.code2.le == obj_user.code2.le
#     assert cls_req.user.code2.me == obj_user.code2.me

#     assert cls_req.user.pa == obj_user.pa
#     assert cls_req.user.o1 == obj_user.o1

#     assert not cls_req.user.o2 and not obj_user.o2
#     assert not cls_req.user.o3 and not obj_user.o3
#     assert not cls_req.user.o4 and not obj_user.o4

#     assert cls_req.enum2 == obj_enum2
#     assert cls_req.quantity == quantity
