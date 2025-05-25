import unittest
from enum import IntEnum

from grpcAPI.app import Module, Package
from grpcAPI.types import NO_PACKAGE, BaseMessage, ProtoOption


class TestModulePackage(unittest.TestCase):

    def test_module_proto_model(self) -> None:
        mod = Module("mymod.proto")
        ProtoModel = mod.ProtoModel

        self.assertTrue(issubclass(ProtoModel, BaseMessage))
        self.assertEqual(ProtoModel.protofile(), "mymod.proto")
        self.assertEqual(ProtoModel.package(), NO_PACKAGE)

    def test_module_proto_enum(self) -> None:
        mod = Module("enum.proto", "enum_pkg")
        ProtoEnum = mod.ProtoEnum

        self.assertTrue(issubclass(ProtoEnum, IntEnum))
        self.assertEqual(ProtoEnum.protofile(), "enum.proto")
        self.assertEqual(ProtoEnum.package(), "enum_pkg")

        class MyEnum(ProtoEnum):
            A = 1
            B = 2

        self.assertEqual(MyEnum.A.value, 1)
        self.assertEqual(MyEnum.B.value, 2)
        self.assertEqual(MyEnum.protofile(), "enum.proto")
        self.assertEqual(MyEnum.package(), "enum_pkg")

    def test_package_make_module(self) -> None:
        pack = Package("pack1")
        mod1 = pack.Module("mod1")

        self.assertEqual(mod1.name, "mod1")
        self.assertEqual(mod1.package, "pack1")
        self.assertIs(pack._modules["mod1"], mod1)

        with self.assertRaises(ValueError):
            pack.Module("mod1")

    def test_immutability(self) -> None:
        mod = Module("immutable.proto", "immutable_pkg")
        with self.assertRaises(AttributeError):
            mod.modname = "changed.proto"

        pack = Package("pack")
        with self.assertRaises(AttributeError):
            pack.packname = "changed"

    def test_usage_example(self) -> None:
        pack1 = Package("pack1")
        mod1 = pack1.Module("mod1")

        class NewClass(mod1.ProtoModel):
            arg1: str
            arg2: int

        class NewEnum(mod1.ProtoEnum):
            FOO = 1
            BAR = 2

        self.assertEqual(NewClass.protofile(), "mod1")
        self.assertEqual(NewClass.package(), "pack1")

        self.assertEqual(NewEnum.protofile(), "mod1")
        self.assertEqual(NewEnum.package(), "pack1")
        self.assertEqual(NewEnum.FOO.value, 1)
        self.assertEqual(NewEnum.BAR.value, 2)

    def test_service_decorator_registers_method(self) -> None:
        mod = Module("service.proto")

        proto_option = ProtoOption()

        serv_decorator = mod.Service("test_service")

        @serv_decorator(description="Test service description", options=proto_option)
        def test_func(x: int, y: int) -> int:
            return x + y

        # Verifica se o método foi registrado
        self.assertTrue(
            any(sp.name == "test_service" for sp in mod._services),
            "ServicePack with name 'test_service' not found",
        )

        service_pack = next(sp for sp in mod._services if sp.name == "test_service")
        method_obj = service_pack.methods[0]

        self.assertEqual(method_obj.description, "Test service description")
        self.assertEqual(method_obj.options, proto_option)
        self.assertEqual(method_obj.method, test_func)

        self.assertEqual(test_func(2, 3), 5)

    def test_multiple_services_same_name_allowed(self) -> None:
        mod = Module("dup_service.proto")
        serv1 = mod.Service("duplicate_service")
        serv2 = mod.Service("duplicate_service")  # agora permitido

        @serv1(description="First", options={})
        def func1():
            return 1

        @serv2(description="Second", options={})
        def func2():
            return 2

        matching = [sp for sp in mod._services if sp.name == "duplicate_service"]
        self.assertEqual(len(matching), 2, "Should allow duplicate service names")

        all_methods = [m for sp in matching for m in sp.methods]
        self.assertEqual(len(all_methods), 2)

    def test_multiple_methods_in_same_service(self) -> None:
        mod = Module("multi_method.proto")
        serv = mod.Service("multi_method_service")

        @serv(description="first method", options={})
        def method1() -> str:
            return "one"

        @serv(description="second method", options={})
        def method2() -> str:
            return "two"

        sp = next(sp for sp in mod._services if sp.name == "multi_method_service")
        self.assertEqual(len(sp.methods), 2)
        self.assertEqual(sp.methods[0].method(), "one")
        self.assertEqual(sp.methods[1].method(), "two")

    def test_package_duplicate_module_error(self) -> None:
        pack = Package("test_pack")
        pack.Module("mod1")
        with self.assertRaises(ValueError):
            pack.Module("mod1")  # deve falhar

    def test_module_services_immutable(self) -> None:
        mod = Module("immutable.proto")
        with self.assertRaises(AttributeError):
            mod._services = []

    def test_protomodel_and_protoenum_consistency(self) -> None:
        mod = Module("proto_consistency.proto", "testpkg")

        class TestMsg(mod.ProtoModel):
            field: int

        class TestEnum(mod.ProtoEnum):
            VAL = 42

        self.assertEqual(TestMsg.protofile(), "proto_consistency.proto")
        self.assertEqual(TestEnum.package(), "testpkg")
        self.assertEqual(TestEnum.VAL.value, 42)

    def test_service_no_description_options(self) -> None:
        mod = Module("simple.proto")
        serv = mod.Service("simple_service")

        @serv(description="", options={})
        def simple_method() -> str:
            return "ok"

        sp = next(sp for sp in mod._services if sp.name == "simple_service")
        self.assertEqual(sp.description, "")
        self.assertEqual(sp.options, {})
        self.assertEqual(sp.methods[0].method(), "ok")


if __name__ == "__main__":
    unittest.main()
