import logging
import sys
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf.struct_pb2 import ListValue
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import StringValue
from typing_extensions import Annotated, Any, AsyncIterator, Dict, List

from grpcAPI.app import APIService, App
from grpcAPI.grpcapi import GrpcAPI
from grpcAPI.settings.utils import combine_settings
from grpcAPI.testclient.testclient import TestClient
from grpcAPI.types import AsyncContext, Depends, FromContext, FromRequest

lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))

from tests.lib.account_pb2 import Account, AccountCreated, AccountInput
from tests.lib.inner.inner_pb2 import InnerMessage
from tests.lib.other_pb2 import Other
from tests.lib.user_pb2 import User, UserCode

root = Path("./tests/proto")

logger = logging.getLogger("grpcAPI.server")


def assert_content(protofile_str: str, content: List[str]) -> None:
    for line in content:
        assert line in protofile_str


@pytest.fixture
def basic_proto() -> APIService:

    serviceapi = APIService(name="service1")

    @serviceapi
    async def unary(req: User) -> User:
        pass

    @serviceapi
    async def clientstream(req: AsyncIterator[User]) -> Other:
        pass

    @serviceapi
    async def serverstream(req: Other) -> AsyncIterator[User]:
        yield User()

    @serviceapi
    async def bilateral(req: AsyncIterator[Other]) -> AsyncIterator[User]:
        yield User()

    return serviceapi


@pytest.fixture
def complex_proto(basic_proto: APIService) -> List[APIService]:

    serviceapi2 = APIService(name="service2")

    @serviceapi2
    async def unary(req: User) -> DescriptorProto:
        pass

    @serviceapi2
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    @serviceapi2
    async def serverstream(req: Other) -> AsyncIterator[Timestamp]:
        yield User()

    @serviceapi2
    async def bilateral(req: AsyncIterator[Timestamp]) -> AsyncIterator[User]:
        yield User()

    serviceapi3 = APIService(
        name="service3",
        package="pack3",
        module="mod3",
    )

    @serviceapi3
    async def unary(req: User) -> DescriptorProto:
        pass

    @serviceapi3
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    return [basic_proto, serviceapi2, serviceapi3]


@pytest.fixture
def inject_proto() -> APIService:

    serviceapi = APIService(name="injected")

    async def get_db() -> str:
        return "sqlite"

    @serviceapi
    async def unary(
        code: Annotated[UserCode, FromRequest(User)],
        age: InnerMessage = FromRequest(User),
        db: str = Depends(get_db),
    ) -> User:
        pass

    @serviceapi
    async def clientstream(req: AsyncIterator[User]) -> Other:
        pass

    @serviceapi
    async def serverstream(
        name: Annotated[str, FromRequest(Other, "name")], peer: str = FromContext()
    ) -> AsyncIterator[User]:
        yield User()

    @serviceapi
    async def bilateral(
        req: AsyncIterator[Other], fromctx: str = FromContext(field="peer")
    ) -> AsyncIterator[User]:
        yield User()

    return serviceapi


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
        email: str = FromRequest(AccountInput),
        payload: Dict[str, Any] = FromRequest(AccountInput),
        itens: List[Any] = FromRequest(AccountInput),
    ) -> AccountCreated:

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
    return app


@pytest.fixture(scope="session")
def testclient_fixture(app_fixture: App) -> TestClient:
    settings = combine_settings(
        {
            "path": {
                "proto_path": "tests/proto",
                "lib_path": "tests/lib",
            },
            "compile_proto": {"clean_services": True},
            "format": {"case": "none", "comment_style": "multiline"},
        }
    )
    return TestClient(app_fixture, settings)


@pytest.fixture
def stringvalue_request() -> List[StringValue]:
    return [StringValue(value="foo"), StringValue(value="bar")]


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
