from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from grpcAPI.app import APIService, App
from grpcAPI.commands.build import BuildCommand
from grpcAPI.commands.protoc import ProtocCommand
from grpcAPI.protobuf import StringValue


@pytest.fixture()
def get_app() -> App:

    app = App()

    service1 = APIService("service1")

    gateway1 = {"get": "/api/v1/users/{user_id}"}

    @service1(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway1,
    )
    async def func1(value: str):
        return StringValue(value=value)

    gateway2 = {"post": "/api/v1/users", "body": "*"}

    @service1(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway2,
    )
    async def func2(value: str):
        return StringValue(value=value)

    gateway3 = {"put": "/api/v1/users/{user_id}", "body": "*"}

    @service1(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway3,
    )
    async def func3(value: str):
        return StringValue(value=value)

    gateway4 = {
        "patch": "/api/v1/users/{user_id}",
        "body": "*",
        "response_body": "user",
    }

    @service1(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway4,
    )
    async def func4(value: str):
        return StringValue(value=value)

    gateway5 = {"delete": "/api/v1/users/{user_id}"}

    @service1(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway5,
    )
    async def func5(value: str):
        return StringValue(value=value)

    gateway6 = {
        "get": "/api/v1/users",
        "additional_bindings": [{"get": "/api/v2/users"}],
    }

    @service1(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway6,
    )
    async def func6(value: str):
        return StringValue(value=value)

    service2 = APIService("service2")

    # Complex nested gateway configurations
    gateway7 = {
        "post": "/api/v1/orders",
        "body": "*",
        "additional_bindings": [
            {
                "post": "/api/v2/orders",
                "body": "order",
                "response_body": "order_response",
            },
            {"put": "/api/v1/orders/{order_id}", "body": "*"},
        ],
    }

    @service2(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway7,
    )
    async def func7(value: str):
        return StringValue(value=value)

    gateway8 = {
        "get": "/api/v1/analytics/{report_type}",
    }

    @service2(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway8,
    )
    async def func8(value: str):
        return StringValue(value=value)

    gateway9 = {
        "post": "/api/v1/bulk/operations",
        "body": "*",
    }

    @service2(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway9,
    )
    async def func9(value: str):
        return StringValue(value=value)

    gateway10 = {
        "get": "/api/v1/search/{query}",
        "additional_bindings": [
            {
                "get": "/api/v2/search/{query}",
                "response_body": "results",
            },
            {
                "post": "/api/v1/search/advanced",
                "body": "search_request",
            },
        ],
    }

    @service2(
        request_type_input=StringValue,
        response_type_input=StringValue,
        gateway=gateway10,
    )
    async def func10(value: str):
        return StringValue(value=value)

    app.add_service(service1)
    app.add_service(service2)
    return app


def test_full_add_gateway(get_app: App) -> None:
    app = get_app

    with TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        build = BuildCommand(app)
        build.execute(proto_path=temp_path, overwrite=True, outdir=temp_path)
        assert temp_path.exists()
        assert (temp_path / "service.proto").exists()

        protoc = ProtocCommand()
        protoc.execute(proto_path=temp_path, lib_path=temp_path, mypy_stubs=True)
        assert (temp_path / "service_pb2.py").exists()
        assert (temp_path / "service_pb2.pyi").exists()
