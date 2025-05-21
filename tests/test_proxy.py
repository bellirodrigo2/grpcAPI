import unittest
from enum import Enum
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from typing_extensions import Annotated

from grpcAPI.proto_proxy import (
    ProtoProxy,
    bind_proto_proxy,
    import_py_files_from_folder,
)
from grpcAPI.types import FieldSpec, Float, Int32, OneOf, String


class ProtoMessage(ProtoProxy):
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


class Requisition(ProtoMessage):
    user: User
    code: Code
    product: Product
    quantity: Int32
    enum2: Enum2


class CollectionMsg(ProtoMessage):
    list_id: List[ID]
    dict_prod: Dict[str, Product]


class ProxyTest(unittest.TestCase):

    def setUp(self) -> None:
        self.p = Path(__file__).parent / "proto" / "compiled"
        self.modules = import_py_files_from_folder(self.p)

        bind_proto_proxy(ID, self.modules)
        bind_proto_proxy(User, self.modules)
        bind_proto_proxy(Code, self.modules)
        bind_proto_proxy(Product, self.modules)
        bind_proto_proxy(Requisition, self.modules)
        bind_proto_proxy(CollectionMsg, self.modules)

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

        self.name_user = "Maria"
        self.lastname = "Silva"
        self.email = "foo.bar@gmail.com"
        self.age = 49
        self.tags = ["foo", "bar"]
        self.oobool = True
        self.proxy_user = User(
            id=self.proxy_id,
            name=self.name_user,
            lastname=self.lastname,
            email=self.email,
            age=self.age,
            tags=self.tags,
            code2=self.proxy_code,
            pa=self.obj_prodarea,
            o1=self.oobool,
        )
        quantity = 32
        self.proxy_req = Requisition(
            user=self.proxy_user,
            code=self.proxy_code,
            product=self.proxy_product,
            quantity=quantity,
            enum2=self.obj_enum2,
        )
        self.proxy_id2 = ID(id=42)
        self.proxy_collection = CollectionMsg(
            list_id=[self.proxy_id, self.proxy_id2],
            dict_prod={"foo": self.proxy_product},
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
        self.assertEqual(proto_code.le, [litem.value for litem in self.le])
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

    def test_code_list_append(self) -> None:
        code = self.proxy_code
        code.s.append("hello")
        self.assertEqual(len(code.s), 3)
        self.assertEqual(code.s[-1], "hello")

    def test_code_list_assignment_and_modification(self) -> None:
        code = self.proxy_code
        code.s = ["new"]
        self.assertEqual(code.s, ["new"])
        code.s[0] = "modified"
        self.assertEqual(code.s[0], "modified")

    def test_code_list_extend_insert_remove(self) -> None:
        code = self.proxy_code
        code.s = ["a"]
        code.s.extend(["more", "values"])
        self.assertEqual(code.s[-2:], ["more", "values"])
        code.s.insert(1, "middle")
        code.s.remove("middle")
        self.assertNotIn("middle", code.s)

    def test_code_list_pop_clear_reverse(self) -> None:
        code = self.proxy_code
        code.s = ["a", "b", "c"]
        item = code.s.pop()
        self.assertEqual(item, "c")
        code.s.clear()
        self.assertEqual(code.s, [])
        code.s = ["a", "b", "c"]
        code.s.reverse()
        self.assertEqual(code.s, ["c", "b", "a"])

    def test_code_list_copy_sort_slice_assignment(self) -> None:
        code = self.proxy_code
        code.s = ["c", "a", "b"]
        copy_list2 = code.s.copy()
        copy_list2.pop()
        self.assertEqual(len(code.s), 3)
        code.s.sort()
        self.assertEqual(code.s, ["a", "b", "c"])
        code.s[:2] = ["x", "y"]
        self.assertEqual(code.s[:2], ["x", "y"])

    def test_code_dict_get_and_del(self) -> None:
        code = self.proxy_code
        proto = code.unwrap

        self.assertEqual(proto.me["foo"], Enum2.e1.value)

        del code.me["foo"]
        self.assertEqual(code.me, {})

    def test_code_dict_set_and_keys(self) -> None:
        code = self.proxy_code
        code.me.clear()

        code.me["abc"] = Enum2.e2
        self.assertEqual(code.me["abc"], Enum2.e2)

        code.me["123"] = Enum2.e1
        self.assertEqual(set(code.me.keys()), {"abc", "123"})
        self.assertIn(Enum2.e2, code.me.values())

    def test_code_dict_get_and_pop(self) -> None:
        code = self.proxy_code

        code.me["abc"] = Enum2.e2
        self.assertEqual(code.me.get("abc"), Enum2.e2)
        self.assertIsNone(code.me.get("nonexistent_key"))

        self.assertEqual(code.me.pop("abc"), Enum2.e2)
        self.assertNotIn("abc", code.me)

    def test_code_dict_clear_and_update(self) -> None:
        code = self.proxy_code

        code.me.clear()
        self.assertEqual(code.me, {})

        code.me.update({"new_key": Enum2.e1})
        self.assertEqual(code.me["new_key"], Enum2.e1)

    def test_code_dict_setdefault_and_get_default(self) -> None:
        code = self.proxy_code
        self.assertEqual(len(code.me), 1)
        code.me["new_key"] = Enum2.e1
        self.assertEqual(len(code.me), 2)
        self.assertIn("new_key", code.me)
        self.assertEqual(code.me.setdefault("new_key", Enum2.e2), Enum2.e1)
        self.assertEqual(code.me.get("no_existant", 45), 45)

    def test_code_dict_len_and_set_method(self) -> None:
        code = self.proxy_code

        self.assertEqual(len(code.me), 1)
        code.me.set("new_key2", Enum2.e1)
        self.assertEqual(len(code.me), 2)

    def test_code_dict_reassign(self) -> None:
        code = self.proxy_code

        self.assertEqual(len(code.me), 1)
        code.me = {}
        self.assertEqual(len(code.me), 0)
        code.me = {"foo": Enum2.e1, "bar": Enum2.e2}
        self.assertEqual(len(code.me), 2)

    def test_code_dict_type_errors(self) -> None:
        code = self.proxy_code

        with self.assertRaises(TypeError):
            code.me.set("new_key2", 0)

        with self.assertRaises(TypeError):
            code.me.set("new_key2", None)

        with self.assertRaises(TypeError):
            code.me["new_key2"] = 0

        with self.assertRaises(TypeError):
            code.me["new_key2"] = None

    def test_code_dict_is_mapping(self) -> None:
        code = self.proxy_code
        self.assertIsInstance(code.me, Mapping)

    def test_code_unwrap(self) -> None:
        code = self.proxy_code
        proto = code.unwrap
        code2 = Code(_wrapped=proto)
        self.assertIs(code.unwrap, code2.unwrap)

    def test_sequence_accepts_only_strings(self) -> None:
        code = self.proxy_code
        code.s = []
        code.s.append("foo")

        with self.assertRaises(TypeError):
            code.s[0] = 4

        with self.assertRaises(TypeError):
            code.s.append(4)

        with self.assertRaises(TypeError):
            code.s.extend(4)

        self.assertIsInstance(code.s, Sequence)

    def test_constructor_rejects_invalid_field_type(self) -> None:
        with self.assertRaises(TypeError):
            Code(code="not an int")

    def test_enum_field_rejects_invalid_type(self) -> None:
        code = self.proxy_code

        with self.assertRaises(TypeError):
            code.pa = "not an enum"

    def test_int_field_rejects_invalid_type(self) -> None:
        code = self.proxy_code

        with self.assertRaises(TypeError):
            code.code = "not an int"

    def test_sequence_field_rejects_non_list_assignment(self) -> None:
        code = self.proxy_code

        with self.assertRaises(TypeError):
            code.s = 3

    def test_dict_field_rejects_non_dict_assignment(self) -> None:
        code = self.proxy_code

        with self.assertRaises(TypeError):
            code.me = 3

    def test_serialize_to_string(self) -> None:
        serialized = self.proxy_code.SerializeToString()
        self.assertIsInstance(serialized, bytes)
        self.assertGreater(len(serialized), 0)

    def test_parse_from_string(self) -> None:
        serialized = self.proxy_code.SerializeToString()

        new_proxy = Code()
        new_proxy.ParseFromString(serialized)

        self.assertEqual(new_proxy.code, self.proxy_code.code)
        self.assertEqual(new_proxy.pa, self.proxy_code.pa)

    def test_product(self) -> None:
        product = self.proxy_product
        self.assertEqual(product.code, self.proxy_code)
        self.assertEqual(product.code.code, self.proxy_code.code)

    def test_nested_message_assign(self) -> None:
        code2 = Code(code=10, pa=ProductArea.Area3, s=[], le=[], me={})
        self.proxy_product.code = code2

    def test_user(self) -> None:
        user = self.proxy_user
        self.assertEqual(user.id.id, self.proxy_id.id)
        self.assertEqual(user.code2.pa, self.proxy_code.pa)

        self.assertEqual(user.o1, self.oobool)
        self.assertEqual(user.o2, "")
        self.assertEqual(user.o3, 0)
        self.assertEqual(user.o4, "")

    def test_user_oneof(self) -> None:
        user = self.proxy_user
        self.assertEqual(user.WhichOneof("oo1"), "o1")
        self.proxy_user.o3 = 123
        self.assertEqual(user.WhichOneof("oo1"), "o3")

        self.assertEqual(user.o1, False)
        self.assertEqual(user.o2, "")
        self.assertEqual(user.o3, 123)
        self.assertEqual(user.o4, "")

    def test_req(self) -> None:
        req = self.proxy_req
        self.assertEqual(req.user.tags, self.proxy_user.tags)
        self.assertEqual(req.code, self.proxy_code)
        self.assertEqual(req.code.code, self.proxy_code.code)
        self.assertEqual(req.user.id.id, self.proxy_user.id.id)
        self.assertEqual(req.user.tags, self.proxy_user.tags)
        self.assertEqual(req.user.code2.code, self.proxy_code.code)
        self.assertEqual(req.user.code2.pa, self.proxy_code.pa)
        self.assertEqual(req.user.code2.le, self.proxy_code.le)
        self.assertEqual(req.user.code2.me, self.proxy_code.me)

        self.assertEqual(req.user.o1, self.oobool)
        self.assertEqual(req.user.o2, "")
        self.assertEqual(req.user.o3, 0)
        self.assertEqual(req.user.o4, "")

    def test_req_oneof(self) -> None:
        req = self.proxy_req

        self.assertEqual(req.user.WhichOneof("oo1"), "o1")
        req.user.o3 = 123
        self.assertEqual(req.user.WhichOneof("oo1"), "o3")
        self.assertEqual(req.user.o1, False)
        self.assertEqual(req.user.o2, "")
        self.assertEqual(req.user.o3, 123)
        self.assertEqual(req.user.o4, "")

    def test_collections_get(self) -> None:
        coll_list = self.proxy_collection.list_id
        coll_dict = self.proxy_collection.dict_prod
        self.assertEqual(coll_list, [self.proxy_id, self.proxy_id2])
        self.assertEqual(coll_dict["foo"], self.proxy_product)
        self.assertEqual(coll_dict.get("foo"), self.proxy_product)

    def test_collections_dunders(self) -> None:
        coll_list = self.proxy_collection.list_id
        coll_dict = self.proxy_collection.dict_prod
        self.assertEqual(len(coll_list), 2)
        self.assertEqual(len(coll_dict), 1)
        self.assertIn(self.proxy_id, coll_list)
        self.assertIn("foo", coll_dict)

        self.assertNotIn(self.proxy_code, coll_list)
        self.assertNotIn("bar", coll_dict)

    def test_collections_append_list(self) -> None:
        coll_list = self.proxy_collection.list_id

        newid = ID(id=457)
        coll_list.append(newid)
        self.assertEqual(coll_list[-1], newid)
        self.assertEqual(len(coll_list), 3)
        self.assertIn(newid, coll_list)
        self.proxy_collection.list_id.extend([ID(id=32), ID(id=100)])
        self.assertEqual(len(coll_list), 5)
        id35 = ID(id=35)
        self.proxy_collection.list_id.insert(1, id35)
        self.assertEqual(len(coll_list), 6)
        self.assertEqual(coll_list[1].id, 35)
        self.proxy_collection.list_id.remove(id35)
        self.assertEqual(len(coll_list), 5)

    def test_collections_setitem_del(self) -> None:
        coll_dict = self.proxy_collection.dict_prod

        newprod = Product(
            name="prod2",
            unit_price={},
            code=self.proxy_code,
            area=ProductArea.Area3,
            enum2=Enum2.e1,
        )
        self.assertEqual(len(coll_dict), 1)
        self.assertNotIn("bar", coll_dict)
        coll_dict["bar"] = newprod
        self.assertIn("bar", coll_dict)
        self.assertEqual(len(coll_dict), 2)
        self.assertIn("foo", coll_dict)
        del coll_dict["foo"]
        self.assertNotIn("foo", coll_dict)
        self.assertEqual(len(coll_dict), 1)
        coll_dict.set("hello", newprod)
        self.assertEqual(len(coll_dict), 2)
        self.assertIn("hello", coll_dict)

    def test_collections_update(self) -> None:
        coll_dict = self.proxy_collection.dict_prod

        newprod = Product(
            name="prod2",
            unit_price={},
            code=self.proxy_code,
            area=ProductArea.Area3,
            enum2=Enum2.e1,
        )
        self.proxy_collection.dict_prod.update({"bar": newprod})
        self.assertEqual(len(coll_dict), 2)
        self.assertIn("bar", coll_dict)

    def test_collections_list_assign(self) -> None:
        coll_list = self.proxy_collection.list_id

        newid = ID(id=457)
        self.assertEqual(len(coll_list), 2)
        self.proxy_collection.list_id = [newid]
        self.assertEqual(len(coll_list), 1)
        self.assertEqual(coll_list[0], newid)

    def test_collections_dict_assign(self) -> None:
        coll_dict = self.proxy_collection.dict_prod
        self.assertIn("foo", coll_dict)
        self.assertEqual(len(coll_dict), 1)

        self.proxy_collection.dict_prod = {}
        self.assertNotIn("foo", coll_dict)
        self.assertEqual(len(coll_dict), 0)

        self.proxy_collection.dict_prod = {"hello": self.proxy_product}
        self.assertIn("hello", coll_dict)
        self.assertNotIn("foo", coll_dict)
        self.assertEqual(len(coll_dict), 1)

    def test_collections_collections_fail(self) -> None:
        coll_list = self.proxy_collection.list_id
        coll_dict = self.proxy_collection.dict_prod

        with self.assertRaises(TypeError):
            coll_list.append(1)
        with self.assertRaises(TypeError):
            coll_list[0] = "world"

        with self.assertRaises(TypeError):
            coll_dict.set("1", "foobar")
        with self.assertRaises(TypeError):
            coll_dict["0"] = "world"


if __name__ == "__main__":
    unittest.main()
