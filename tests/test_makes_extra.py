import unittest
from enum import Enum
from typing import Annotated

from grpcAPI.makeproto.makeblock import (
    make_enumblock,
    make_method,
    make_msgblock,
    make_service,
)
from grpcAPI.makeproto.protoblock import Method
from grpcAPI.types import BaseMessage, Metadata


# 1. Enum para testar make_enumblock
class StatusEnum(Enum):
    @classmethod
    def protofile(cls) -> str:
        return "integration.proto"

    @classmethod
    def package(cls) -> str:
        return "integrationpkg"

    OK = 0
    ERROR = 1


class ProtoBase(BaseMessage):
    @classmethod
    def protofile(cls) -> str:
        return "integration.proto"

    @classmethod
    def package(cls) -> str:
        return "integrationpkg"


class Request(ProtoBase):
    user_id: Annotated[int, Metadata(description="ID do usuário")]
    action: Annotated[str, Metadata(description="ação solicitada")]


class Response(ProtoBase):
    status: StatusEnum
    message: str


# Função estilo FastAPI gRPC
def perform_action(
    req: Annotated[Request, Metadata(description="action request")],
) -> Response: ...


class TestIntegrationMakeBlocks(unittest.TestCase):

    def test_enumblock(self) -> None:
        enum_block = make_enumblock(StatusEnum)
        self.assertEqual(enum_block.name, "StatusEnum")
        self.assertEqual(len(enum_block.fields), 2)
        names = [f.name for f in enum_block.fields]
        self.assertIn("OK", names)
        self.assertIn("ERROR", names)
        self.assertEqual(enum_block.protofile, "integration.proto")

    def test_msgblock(self) -> None:
        req_block = make_msgblock(Request)
        self.assertEqual(req_block.name, "Request")
        self.assertEqual(req_block.protofile, "integration.proto")
        self.assertEqual(len(req_block.fields), 2)
        fields = [f.name for f in req_block.fields]
        self.assertIn("user_id", fields)
        self.assertIn("action", fields)

        res_block = make_msgblock(Response)
        self.assertEqual(res_block.name, "Response")
        self.assertEqual(len(res_block.fields), 2)
        self.assertIn("status", [f.name for f in res_block.fields])

    def test_method(self) -> None:
        method = make_method(perform_action, ignore_instance=[])
        self.assertEqual(method.name, "perform_action")
        self.assertEqual(len(method.request_type), 1)
        self.assertIs(method.request_type[0], Request)
        self.assertIs(method.response_type, Response)

    def test_service(self) -> None:
        service = make_service(
            servicename="IntegrationService",
            protofile="integration.proto",
            package="integrationpkg",
            methods=[(perform_action, "", {})],
            ignore_instance=[],
            description="Service for integration test",
            options={"deprecated": False},
        )
        self.assertEqual(service.name, "IntegrationService")
        self.assertEqual(service.protofile, "integration.proto")
        self.assertEqual(len(service.fields), 1)

        method = service.fields[0]
        self.assertIsInstance(method, Method)
        self.assertEqual(method.name, "perform_action")
        self.assertIs(method.block, service)

    def test_full_integration(self) -> None:
        # Enum
        enum_block = make_enumblock(StatusEnum)

        # Messages
        req_block = make_msgblock(Request)
        res_block = make_msgblock(Response)

        # Method
        method = make_method(perform_action, ignore_instance=[])

        # Service
        service = make_service(
            servicename="IntegrationService",
            protofile="integration.proto",
            package="integrationpkg",
            methods=[(perform_action, "", {})],
            ignore_instance=[],
            description="Service for integration test",
            options={},
        )

        # Assert all connected
        self.assertEqual(enum_block.package, req_block.package)
        self.assertEqual(req_block.package, res_block.package)
        self.assertEqual(service.protofile, req_block.protofile)
        self.assertEqual(method.response_type, Response)
        self.assertEqual(method.request_type[0], Request)
        self.assertEqual(service.fields[0].name, method.name)


if __name__ == "__main__":
    unittest.main()
