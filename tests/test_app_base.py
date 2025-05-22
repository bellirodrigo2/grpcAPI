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
        mod1 = pack.make_module("mod1")

        self.assertEqual(mod1.modname, "mod1")
        self.assertEqual(mod1.packname, "pack1")
        self.assertIs(pack.modules["mod1"], mod1)

        with self.assertRaises(ValueError):
            pack.make_module("mod1")

    def test_immutability(self) -> None:
        mod = Module("immutable.proto", "immutable_pkg")
        with self.assertRaises(AttributeError):
            mod.modname = "changed.proto"

        pack = Package("pack")
        with self.assertRaises(AttributeError):
            pack.packname = "changed"

    def test_usage_example(self) -> None:
        pack1 = Package("pack1")
        mod1 = pack1.make_module("mod1")

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

        @mod.service("test_service", "Test service description", proto_option)
        def test_func(x: int, y: int) -> int:
            return x + y

        # Verifica se o método foi registrado
        self.assertIn("test_service", mod._services)
        method_obj = mod._services["test_service"][0]

        self.assertEqual(method_obj.description, "Test service description")
        self.assertEqual(method_obj.options, proto_option)
        self.assertEqual(method_obj.method, test_func)

        # Também verifica que a função decorada retorna a função original
        self.assertEqual(test_func(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
