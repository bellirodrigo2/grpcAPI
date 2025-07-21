# ruff: noqa: E402
import logging
import sys
from datetime import datetime
from pathlib import Path

import pytest
from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import BytesValue, StringValue
from typing_extensions import Annotated, Any, AsyncIterator, Dict, List

from grpcAPI import ErrorCode
from grpcAPI.app import APIService, App
from grpcAPI.grpcapi import GrpcAPI
from grpcAPI.settings.utils import combine_settings
from grpcAPI.testclient.testclient import TestClient
from grpcAPI.types import AsyncContext, FromRequest

lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))

from tests.lib.account_pb2 import Account, AccountCreated, AccountInput
from tests.lib.inner.inner_pb2 import InnerMessage
from tests.lib.multi.inner.class_pb2 import ClassMsg
from tests.lib.other_pb2 import Other
from tests.lib.user_pb2 import User, UserCode

root = Path("./tests/proto")

logger = logging.getLogger("grpcAPI.server")


@pytest.fixture(scope="session")
def functional_service() -> APIService:
    serviceapi = APIService(
        module="account_service",
        name="functional",
        comments="This is a functional example of a service implementation",
        title="Functional Service",
        description="Service with function implementation",
        tags=["account", "test"],
    )
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."

    @serviceapi(
        title="Create Account",
        description="Create an account by giving a name, email, payload and itens",
        comment=text,
        tags=["account", "creator", "test"],
    )
    async def create_account(
        name: Annotated[str, FromRequest(AccountInput)],
        context: AsyncContext,
        email: str = FromRequest(AccountInput),
        payload: Dict[str, Any] = FromRequest(AccountInput),
        itens: List[Any] = FromRequest(AccountInput),
    ) -> AccountCreated:
        if name == "raise":
            raise NotImplementedError("Not Implemented Test")
        if name == "abort":
            await context.abort(35, "abort")

        created_at = datetime(2020, 1, 1)
        ts = Timestamp()
        ts.FromDatetime(created_at)
        country = payload["country"]
        return AccountCreated(
            id=f"id:{name}-{email}-{country}-{itens[0]}", created_at=ts
        )

    @serviceapi
    async def get_accounts(
        values: ListValue, context: AsyncContext
    ) -> AsyncIterator[Account]:

        for v in values:
            if v == "foo":
                context.peer()
            if v == "bar":
                context.set_code("bar")
            if v == "abort":
                await context.abort(35, "abort")
            if v == "raise":
                raise NotImplementedError("Not Implemented Test")
            yield Account(name=v, email=f"{v}@email.com")

    @serviceapi
    async def get_by_ids(ids: AsyncIterator[StringValue]) -> AsyncIterator[Account]:

        async for id in ids:
            yield Account(
                id=id.value, name=f"account{id.value}", email=f"{id.value}@email.com"
            )

    @serviceapi
    async def get_emails(ids: AsyncIterator[StringValue]) -> ListValue:

        emails = ListValue()
        async for id in ids:
            emails.extend([id])
        return emails

    return serviceapi


@pytest.fixture(scope="session")
def app_fixture(functional_service: APIService) -> App:

    app = GrpcAPI()
    app.add_service(functional_service)

    @app.exception_handler(NotImplementedError)
    async def handle_not_implemented(
        exc: NotImplementedError, context: AsyncContext
    ) -> None:
        context.set_code(500)
        await context.abort(ErrorCode.ABORTED, str(exc))

    return app


@pytest.fixture(scope="session")
def testclient_fixture(app_fixture: App) -> TestClient:
    settings = combine_settings(
        {
            "proto_path": "tests/proto",
            "lib_path": "tests/lib",
            "compile_proto": {"clean_services": True},
            "format": {"case": "none", "comment_style": "multiline"},
        }
    )
    return TestClient(app_fixture, settings)


class AsyncIt:
    def __init__(self, data: List[Any]) -> None:
        self._data = data
        self._index = 0

    def __aiter__(self) -> "AsyncIt":
        return self

    async def __anext__(self) -> Any:
        if self._index >= len(self._data):
            raise StopAsyncIteration
        value = self._data[self._index]
        self._index += 1
        return value
